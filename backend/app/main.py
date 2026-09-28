"""Backend entry point. Run it with:  uv run uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import request_context
from app.core.rate_limit import RateLimiter


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    # Interactive API docs are for development; hide them in production.
    docs_enabled = not settings.is_production
    app = FastAPI(
        title="AI Lead Follow-Up Agent API",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.state.login_limiter = RateLimiter(max_attempts=10, window_seconds=15 * 60)
    app.state.register_limiter = RateLimiter(max_attempts=10, window_seconds=60 * 60)

    app.middleware("http")(request_context)
    app.include_router(api_router)
    return app


app = create_app()
