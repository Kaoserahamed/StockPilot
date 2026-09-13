"""Security and observability middleware for StockPilot backend.

Provides:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request ID generation and propagation
- Request timing metrics
- Response caching headers
"""
import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        # HSTS only meaningful over HTTPS; harmless over HTTP.
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # CSP: strict but allows inline styles (common with React/Tailwind).
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """Add appropriate cache headers based on endpoint type."""

    # Endpoints that should never be cached
    NO_CACHE_PATHS = {"/api/v1/auth", "/api/v1/sales", "/api/v1/purchases", "/api/v1/expenses"}

    # Endpoints that can be cached briefly
    SHORT_CACHE_PATHS = {"/api/v1/products", "/api/v1/categories", "/api/v1/parties"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        path = request.url.path

        if request.method != "GET":
            # State-changing requests: never cache
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        elif any(path.startswith(p) for p in self.NO_CACHE_PATHS):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        elif any(path.startswith(p) for p in self.SHORT_CACHE_PATHS):
            response.headers["Cache-Control"] = "private, max-age=30"
        else:
            response.headers["Cache-Control"] = "private, max-age=60"

        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and timing to each request.

    The request ID is:
    - Generated if not present in the incoming header
    - Stored in request.state for access in route handlers
    - Echoed back in the response header for client-side correlation
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
        request.state.request_id = req_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = req_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        logger.info(
            "%s %s -> %d (%.2fms)",
            request.method, request.url.path, response.status_code, elapsed_ms,
            extra={"request_id": req_id, "status": response.status_code, "ms": elapsed_ms},
        )
        return response


def register_middleware(app: FastAPI) -> None:
    """Register all custom middleware with the FastAPI app."""
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(CacheHeadersMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
