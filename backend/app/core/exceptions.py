"""
Centralized exception classes and FastAPI exception handlers — Phase 11.

Provides consistent API error responses:
  {
    "success": false,
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "The requested resource was not found"
    }
  }

Stack traces are hidden in production (DEBUG=false).
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Custom exception classes ──────────────────────────────────────────────────

class RuralBizError(Exception):
    """Base application exception."""
    status_code: int = 500
    code:        str = "INTERNAL_ERROR"
    message:     str = "An unexpected error occurred."

    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        self.message = message or self.__class__.message
        self.detail  = detail
        super().__init__(self.message)


class AuthenticationError(RuralBizError):
    status_code = 401
    code        = "AUTHENTICATION_FAILED"
    message     = "Authentication failed."


class AuthorizationError(RuralBizError):
    status_code = 403
    code        = "FORBIDDEN"
    message     = "You do not have permission to perform this action."


class ResourceNotFoundError(RuralBizError):
    status_code = 404
    code        = "RESOURCE_NOT_FOUND"
    message     = "The requested resource was not found."


class ValidationFailedError(RuralBizError):
    status_code = 422
    code        = "VALIDATION_FAILED"
    message     = "The request data is invalid."


class ExternalAPIError(RuralBizError):
    status_code = 503
    code        = "EXTERNAL_API_UNAVAILABLE"
    message     = "An external service is temporarily unavailable."


class DatabaseError(RuralBizError):
    status_code = 500
    code        = "DATABASE_ERROR"
    message     = "A database error occurred."


class RateLimitError(RuralBizError):
    status_code = 429
    code        = "RATE_LIMIT_EXCEEDED"
    message     = "Too many requests. Please slow down and try again."


class DemoModeError(RuralBizError):
    status_code = 403
    code        = "DEMO_MODE_RESTRICTED"
    message     = "This action is restricted in Demo Mode."


# ── Response builder ──────────────────────────────────────────────────────────

def _error_response(
    code: str,
    message: str,
    status_code: int,
    detail: Optional[str] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "success": False,
        "error": {
            "code":    code,
            "message": message,
        },
    }
    if detail and settings.DEBUG:
        body["error"]["detail"] = detail
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


def _get_request_id(request: Request) -> Optional[str]:
    return request.state.__dict__.get("request_id")


# ── Exception handlers ────────────────────────────────────────────────────────

async def ruralbiz_error_handler(request: Request, exc: RuralBizError) -> JSONResponse:
    logger.warning("RuralBizError[%s]: %s", exc.code, exc.message)
    return _error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=_get_request_id(request),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    codes = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_FAILED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_FAILED",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = codes.get(exc.status_code, "HTTP_ERROR")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    logger.info("HTTPException[%d %s]: %s", exc.status_code, code, detail)
    return _error_response(
        code=code,
        message=detail,
        status_code=exc.status_code,
        request_id=_get_request_id(request),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    # Summarise fields without exposing internals
    fields = ", ".join(
        ".".join(str(p) for p in e.get("loc", [])) for e in errors[:5]
    )
    logger.info("Validation error on %s %s — fields: %s", request.method, request.url.path, fields)
    return _error_response(
        code="VALIDATION_FAILED",
        message=f"Invalid request data. Check: {fields}" if fields else "Invalid request data.",
        status_code=422,
        request_id=_get_request_id(request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Always log the full traceback server-side
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
        exc_info=True,
    )
    detail = traceback.format_exc() if settings.DEBUG else None
    return _error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again.",
        status_code=500,
        detail=detail,
        request_id=_get_request_id(request),
    )


# ── Registration helper ───────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(RuralBizError,          ruralbiz_error_handler)   # type: ignore[arg-type]
    app.add_exception_handler(HTTPException,           http_exception_handler)   # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError,  validation_error_handler) # type: ignore[arg-type]
    app.add_exception_handler(Exception,               unhandled_exception_handler) # type: ignore[arg-type]
