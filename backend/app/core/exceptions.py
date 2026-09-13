"""Centralized exception handling for StockPilot backend.

Provides custom exception classes and a global exception handler that ensures
consistent error response format across all API endpoints.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ---------- Custom Exception Classes ----------

class AppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: str | None = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id={resource_id} not found"
        super().__init__(message=msg, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Resource conflict (duplicate, etc.)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class ForbiddenException(AppException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class BadRequestException(AppException):
    """Invalid request data."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimitException(AppException):
    """Too many requests."""

    def __init__(self, message: str = "Too many requests. Please slow down."):
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


# ---------- Error Response Format ----------

def _error_response(status_code: int, message: str, details: dict | None = None,
                    request_id: str | None = None) -> JSONResponse:
    """Build a consistent JSON error response."""
    content: dict = {
        "error": {
            "code": status_code,
            "message": message,
        }
    }
    if details:
        content["error"]["details"] = details
    if request_id:
        content["error"]["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=content)


# ---------- Exception Handlers ----------

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "AppException: %s (status=%d) at %s %s",
            exc.message, exc.status_code, request.method, request.url.path,
        )
        return _error_response(exc.status_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })
        logger.warning(
            "Validation error at %s %s: %d field(s) invalid",
            request.method, request.url.path, len(errors),
        )
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Request validation failed",
            details={"fields": errors},
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_exception_handler(request: Request, exc: PydanticValidationError):
        logger.warning("Pydantic validation error: %s", str(exc))
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Data validation failed",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception at %s %s: %s",
            request.method, request.url.path, str(exc),
        )
        # Hide internal details from the client
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An internal server error occurred. Please try again later.",
        )
