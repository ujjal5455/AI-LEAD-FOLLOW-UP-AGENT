"""Password hashing and login tokens.

Passwords are never stored, only an Argon2 hash of them, which cannot be reversed.
After login the user receives a signed token (a JWT) containing their user ID. The
signature proves our backend issued it: changing any character of the token breaks
the signature, so it can't be forged or edited without knowing JWT_SECRET.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

ACCESS_TOKEN_COOKIE = "access_token"  # noqa: S105 (a cookie name, not a secret)
_JWT_ALGORITHM = "HS256"

_password_hash = PasswordHash.recommended()
# Checked against when a login uses an unknown email, so the response takes the same
# time whether or not the account exists. Otherwise timing reveals which emails exist.
_DUMMY_HASH = _password_hash.hash("timing-equalizer")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Return (is_valid, new_hash). `new_hash` is set when the stored hash is outdated."""
    return _password_hash.verify_and_update(password, password_hash)


def spend_equivalent_verify_time(password: str) -> None:
    _password_hash.verify(password, _DUMMY_HASH)


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID | None:
    """Return the user ID from a valid token, or None if it is invalid or expired."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[_JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None
