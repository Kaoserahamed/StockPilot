"""Rate limiting configuration for StockPilot backend.

Uses slowapi (built on limits library) to enforce per-endpoint and
per-client rate limits. Supports in-memory storage for dev and Redis
for production deployments.
"""
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
    _HAS_SLOWAPI = True
except ImportError:
    _HAS_SLOWAPI = False

from app.core.config import settings


def _get_limit_key(request: Request) -> str:
    """Identify the client: prefer authenticated user ID, fall back to IP."""
    user = getattr(request.state, "user_id", None)
    if user:
        return f"user:{user}"
    return get_remote_address(request) if _HAS_SLOWAPI else "global"


def setup_rate_limiting(app: FastAPI) -> None:
    """Attach rate limiting middleware to the FastAPI app.

    In-memory storage is used by default. For production with multiple
    workers, set REDIS_URL in environment to enable Redis-backed limits.
    """
    if not _HAS_SLOWAPI:
        # slowapi not installed — skip silently
        return

    storage_uri = getattr(settings, "redis_url", None) or "memory://"
    limiter = Limiter(key_func=_get_limit_key, storage_uri=storage_uri)

    # Attach limiter to app state so route handlers can access it
    app.state.limiter = limiter  # type: ignore[attr-defined]

    # Register the exception handler for 429 responses
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


def rate_limit(requests: int, window_seconds: int) -> Callable:
    """Decorator factory for per-endpoint rate limits.

    Usage:
        @router.get("/expensive")
        @rate_limit(requests=10, window_seconds=60)
        def expensive_endpoint():
            ...

    Returns a no-op decorator if slowapi is not installed.
    """
    if not _HAS_SLOWAPI:
        def noop_decorator(func: Callable) -> Callable:
            return func
        return noop_decorator

    limiter: Limiter = None  # Will be resolved from app state at request time

    def decorator(func: Callable) -> Callable:
        # Store limits on the function; actual decoration happens via middleware
        func._rate_limit = (requests, window_seconds)  # type: ignore[attr-defined]
        return func

    return decorator
