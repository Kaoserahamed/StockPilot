"""CSRF protection for state-changing operations.

Uses the double-submit cookie pattern:
- A CSRF token is set as a cookie on first GET request
- State-changing requests (POST/PUT/PATCH/DELETE) must include the token
  in a header (X-CSRF-Token) that matches the cookie value
"""
import hashlib
import hmac
import secrets
import time
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_EXPIRY = 3600  # 1 hour

# Methods that require CSRF protection
PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that are exempt from CSRF (e.g., login, webhooks)
EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}


def _generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection using double-submit cookie pattern."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Set CSRF cookie on GET requests
        if request.method == "GET":
            response = await call_next(request)
            if not request.cookies.get(CSRF_COOKIE_NAME):
                token = _generate_csrf_token()
                response.set_cookie(
                    CSRF_COOKIE_NAME,
                    token,
                    httponly=False,  # Must be readable by JavaScript
                    samesite="strict",
                    secure=settings.environment == "production",
                    max_age=CSRF_TOKEN_EXPIRY,
                )
            return response

        # Check CSRF token on state-changing requests
        if request.method in PROTECTED_METHODS:
            path = request.url.path
            if path not in EXEMPT_PATHS:
                cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
                header_token = request.headers.get(CSRF_HEADER_NAME)

                if not cookie_token or not header_token:
                    return JSONResponse(
                        status_code=403,
                        content={"error": {"code": 403, "message": "CSRF token missing"}},
                    )

                if not hmac.compare_digest(cookie_token, header_token):
                    return JSONResponse(
                        status_code=403,
                        content={"error": {"code": 403, "message": "CSRF token invalid"}},
                    )

        response = await call_next(request)
        return response
