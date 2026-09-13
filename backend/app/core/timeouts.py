"""Request timeout configuration for the application."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
from collections.abc import Callable

from app.core.config import settings

# Timeout in seconds
DEFAULT_TIMEOUT = 30
SEARCH_TIMEOUT = 10
CHECKOUT_TIMEOUT = 15
AI_TIMEOUT = 60
REPORT_TIMEOUT = 45

TIMEOUT_PATHS = {
    "/api/v1/pos/search": SEARCH_TIMEOUT,
    "/api/v1/sales/checkout": CHECKOUT_TIMEOUT,
    "/api/v1/ai": AI_TIMEOUT,
    "/api/v1/reports": REPORT_TIMEOUT,
    "/api/v1/analytics": REPORT_TIMEOUT,
}


class TimeoutMiddleware:
    """Apply per-path request timeouts."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        timeout = DEFAULT_TIMEOUT
        for prefix, t in TIMEOUT_PATHS.items():
            if path.startswith(prefix):
                timeout = t
                break

        async def _send(message):
            await send(message)

        try:
            await asyncio.wait_for(self.app(scope, receive, _send), timeout=timeout)
        except asyncio.TimeoutError:
            response = JSONResponse(
                status_code=504,
                content={"error": {"code": 504, "message": f"Request timed out after {timeout}s"}},
            )
            await response(scope, receive, send)


def setup_timeouts(app: FastAPI) -> None:
    """Wrap the app with timeout middleware."""
    app.add_middleware(TimeoutMiddleware)
