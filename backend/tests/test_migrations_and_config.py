import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import Engine, text

from app.core.config import Settings
from tests.conftest import BACKEND_DIR

VALID_SECRET = "x" * 32


def alembic_config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


def test_models_and_migrations_are_in_sync(engine: Engine) -> None:
    # Fails if someone changes a model but forgets to create a migration for it.
    command.check(alembic_config())


def test_migrations_can_be_rolled_back_and_reapplied(engine: Engine) -> None:
    command.downgrade(alembic_config(), "base")
    command.upgrade(alembic_config(), "head")


def test_row_level_security_is_enabled_on_every_table(engine: Engine) -> None:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT relname FROM pg_class "
                "WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' "
                "AND relname <> 'alembic_version' AND NOT relrowsecurity"
            )
        ).all()
    assert rows == []


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ],
)
def test_database_url_uses_the_psycopg_driver(given: str, expected: str) -> None:
    settings = Settings(database_url=given, jwt_secret=VALID_SECRET, _env_file=None)
    assert settings.database_url == expected


def test_non_postgres_database_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL"):
        Settings(database_url="sqlite:///app.db", jwt_secret=VALID_SECRET, _env_file=None)


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings(database_url="postgresql://u:p@h/db", jwt_secret="too-short", _env_file=None)
