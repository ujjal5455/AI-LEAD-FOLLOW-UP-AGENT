from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN_COOKIE
from app.models import Business, User
from tests.conftest import TEST_PASSWORD, register


def login(client: TestClient, email: str = "owner@example.com", password: str = TEST_PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ─── Registration ────────────────────────────────────────────────────────────


def test_register_creates_owner_and_business_and_logs_in(client: TestClient) -> None:
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "owner@example.com"
    assert body["user"]["full_name"] == "Asha Das"
    assert body["business"]["name"] == "ABC Interiors"
    assert body["business"]["timezone"] == "Asia/Kolkata"
    assert "password" not in response.text
    # Logged in straight away: the session cookie works for /me.
    assert client.get("/api/auth/me").status_code == 200


def test_session_cookie_is_http_only_and_same_site(client: TestClient) -> None:
    response = register(client)
    cookie_header = response.headers["set-cookie"].lower()
    assert f"{ACCESS_TOKEN_COOKIE}=" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header


def test_password_is_stored_as_a_hash(client: TestClient, db: Session) -> None:
    register(client)
    user = db.scalar(select(User).where(User.email == "owner@example.com"))
    assert user is not None
    assert TEST_PASSWORD not in user.password_hash
    assert user.password_hash.startswith("$argon2")


def test_email_is_normalised_to_lowercase(client: TestClient) -> None:
    response = register(client, email="Owner@Example.COM")
    assert response.json()["user"]["email"] == "owner@example.com"


def test_duplicate_email_is_rejected_regardless_of_case(client: TestClient) -> None:
    assert register(client).status_code == 201
    response = register(client, email="OWNER@example.com")
    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"email": "not-an-email"},
        {"business_name": "   "},
        {"full_name": ""},
        {"password": "x" * 129},
    ],
)
def test_register_validates_input(client: TestClient, overrides: dict) -> None:
    response = register(client, **overrides)
    assert response.status_code == 422


def test_registration_creates_exactly_one_business_owned_by_the_user(
    client: TestClient, db: Session
) -> None:
    register(client)
    user = db.scalar(select(User))
    businesses = db.scalars(select(Business)).all()
    assert user is not None
    assert len(businesses) == 1
    assert businesses[0].owner_id == user.id


# ─── Login / logout ──────────────────────────────────────────────────────────


def test_login_with_correct_credentials(client: TestClient) -> None:
    register(client)
    client.cookies.clear()

    response = login(client, email="Owner@Example.com")

    assert response.status_code == 200
    assert response.json()["business"]["name"] == "ABC Interiors"
    assert client.get("/api/auth/me").status_code == 200


def test_wrong_password_and_unknown_email_give_the_same_error(client: TestClient) -> None:
    register(client)
    client.cookies.clear()

    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert ACCESS_TOKEN_COOKIE not in client.cookies


def test_inactive_user_cannot_log_in(client: TestClient, db: Session) -> None:
    register(client)
    client.cookies.clear()
    user = db.scalar(select(User))
    assert user is not None
    user.is_active = False
    db.commit()

    assert login(client).status_code == 401


def test_logout_ends_the_session(client: TestClient) -> None:
    register(client)
    assert client.get("/api/auth/me").status_code == 200

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_repeated_failed_logins_are_rate_limited(client: TestClient) -> None:
    register(client)
    client.cookies.clear()

    for _ in range(10):
        assert login(client, password="wrong-password").status_code == 401

    # Blocked now, even with the right password, until the window passes.
    assert login(client).status_code == 429


def test_successful_login_resets_the_failure_count(client: TestClient) -> None:
    register(client)
    client.cookies.clear()

    for _ in range(9):
        login(client, password="wrong-password")
    assert login(client).status_code == 200
    for _ in range(9):
        assert login(client, password="wrong-password").status_code == 401


# ─── Session tokens ──────────────────────────────────────────────────────────


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_tampered_token_is_rejected(client: TestClient) -> None:
    register(client)
    token = client.cookies[ACCESS_TOKEN_COOKIE]
    client.cookies.set(ACCESS_TOKEN_COOKIE, token[:-2] + ("AA" if token[-2:] != "AA" else "BB"))

    assert client.get("/api/auth/me").status_code == 401


def test_token_signed_with_another_secret_is_rejected(client: TestClient) -> None:
    user_id = register(client).json()["user"]["id"]
    now = datetime.now(UTC)
    forged = jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + timedelta(hours=1)},
        "an-attacker-secret-that-is-32-characters-long",
        algorithm="HS256",
    )
    client.cookies.set(ACCESS_TOKEN_COOKIE, forged)

    assert client.get("/api/auth/me").status_code == 401


def test_expired_token_is_rejected(client: TestClient) -> None:
    user_id = register(client).json()["user"]["id"]
    past = datetime.now(UTC) - timedelta(days=30)
    expired = jwt.encode(
        {"sub": user_id, "iat": past, "exp": past + timedelta(days=7)},
        get_settings().jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    client.cookies.set(ACCESS_TOKEN_COOKIE, expired)

    assert client.get("/api/auth/me").status_code == 401
