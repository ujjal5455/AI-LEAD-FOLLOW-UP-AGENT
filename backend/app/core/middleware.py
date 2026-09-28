"""Per-request middleware: request IDs, timing, safe error responses, security headers."""

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.logging import request_id_var

logger = logging.getLogger("app.request")

# Accept a caller-supplied request ID only if it is short and plain, so it can't be
# used to inject fake lines into our logs.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    incoming_id = request.headers.get("x-request-id", "")
    request_id = incoming_id if _VALID_REQUEST_ID.fullmatch(incoming_id) else uuid.uuid4().hex
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            # Log the full error for us; give the caller nothing internal, just an ID
            # they can quote so we can find the matching log lines.
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            response = JSONResponse(
                {"detail": "Internal server error", "request_id": request_id}, status_code=500
            )
        response.headers["X-Request-ID"] = request_id
        response.headers.update(_SECURITY_HEADERS)
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %d (%.0f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    finally:
        request_id_var.reset(token)
