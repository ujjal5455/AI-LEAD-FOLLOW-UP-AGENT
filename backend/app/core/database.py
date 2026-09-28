"""Database engine and sessions.

The engine owns a small pool of open connections to PostgreSQL. A session is a
short-lived unit of work: FastAPI opens one per request (see `get_db`), the request
reads and writes through it, and it is closed when the request finishes.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        # Quietly replace pooled connections the server has closed (e.g. after idling).
        pool_pre_ping=True,
        # Supabase's transaction-mode pooler can't handle server-side prepared
        # statements. Turning them off costs nothing at our scale.
        connect_args={"prepare_threshold": None},
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session
