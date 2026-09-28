"""Test setup: every test run uses a real, throwaway PostgreSQL database.

If TEST_DATABASE_URL is set, that database is used. Otherwise a temporary PostgreSQL
server is started automatically (from the `pgserver` dev dependency) and deleted
when the run ends. Either way, the schema is built by running our real migrations.
"""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_PASSWORD = "correct-horse-battery"

_temporary_server: Any = None


def pytest_configure(config: pytest.Config) -> None:
    # Runs before any test module (and therefore the app) is imported, so the app's
    # settings pick up the test database, never the development one from .env.
    global _temporary_server
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        import pgserver
        import psycopg

        data_dir = Path(tempfile.mkdtemp(prefix="lead-agent-test-db-"))
        _temporary_server = pgserver.get_server(data_dir, cleanup_mode="delete")
        with psycopg.connect(_temporary_server.get_uri(), autocommit=True) as connection:
            connection.execute("CREATE DATABASE lead_agent_test")
        url = (
            make_url(_temporary_server.get_uri())
            .set(database="lead_agent_test")
            .render_as_string(hide_password=False)
        )

    if "test" not in (make_url(url).database or ""):
        raise pytest.UsageError(
            "Refusing to run: the test database name must contain 'test', "
            "because the tests delete all of its data."
        )
    os.environ["DATABASE_URL"] = url
    os.environ["APP_ENV"] = "test"
    os.environ["JWT_SECRET"] = "test-only-secret-that-is-at-least-32-chars"


def pytest_unconfigure(config: pytest.Config) -> None:
    if _temporary_server is not None:
        _temporary_server.cleanup()


@pytest.fixture(scope="session")
def engine() -> Engine:
    from alembic import command
    from alembic.config import Config

    from app.core.database import get_engine

    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    return get_engine()


@pytest.fixture(autouse=True)
def _empty_database_after_each_test(engine: Engine) -> Iterator[None]:
    yield
    from app.models import Base

    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    from app.core.database import get_session_factory

    with get_session_factory()() as session:
        yield session


@pytest.fixture
def app(engine: Engine):
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def register(
    client: TestClient,
    *,
    email: str = "owner@example.com",
    password: str = TEST_PASSWORD,
    full_name: str = "Asha Das",
    business_name: str = "ABC Interiors",
) -> httpx2.Response:
    return client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "business_name": business_name,
        },
    )
