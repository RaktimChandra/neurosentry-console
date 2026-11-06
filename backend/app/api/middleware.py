"""Custom middleware: request-timing header, graceful error handling."""
from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.logging_config import get_logger

log = get_logger("api")


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Add `X-Request-ID` and `X-Response-Time-ms` to every response and log it."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = uuid.uuid4().hex[:12]
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            log.exception(
                "[%s] %s %s → 500 (%.1fms): %s",
                req_id, request.method, request.url.path, elapsed, exc,
            )
            raise
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-ms"] = f"{elapsed:.1f}"
        # Only log non-GET-health routes to avoid log spam
        if not (request.method == "GET" and request.url.path == "/api/health"):
            log.info(
                "[%s] %s %s → %d (%.1fms)",
                req_id, request.method, request.url.path,
                response.status_code, elapsed,
            )
        return response
