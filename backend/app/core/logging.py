"""
Centralized structured logging — Phase 11.

Usage:
    from app.core.logging import get_logger, log_startup, log_request_error
    logger = get_logger(__name__)

Rules:
  - NEVER log: passwords, JWT tokens, API keys, sensitive secrets.
  - Log: startup, shutdown, API errors, auth failures, AI availability,
    external API failures, database errors.
  - Format: JSON-like structured in production, readable in development.
"""
import logging
import sys
import time
from typing import Optional
from uuid import uuid4

from app.core.config import settings


# ── Formatter ─────────────────────────────────────────────────────────────────

class _ReadableFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    LEVEL_COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, "")
        ts    = self.formatTime(record, "%H:%M:%S")
        name  = record.name.split(".")[-1]  # last component only
        msg   = record.getMessage()
        rid   = getattr(record, "request_id", "")
        rid_s = f"[{rid[:8]}] " if rid else ""
        return f"{color}[{ts}] {record.levelname:8s}{self.RESET} {rid_s}{name}: {msg}"


class _JsonFormatter(logging.Formatter):
    """JSON-structured formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        payload = {
            "time":       self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":      record.levelname,
            "logger":     record.name,
            "message":    record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info and settings.DEBUG:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps({k: v for k, v in payload.items() if v is not None})


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure root logger. Call once at application startup."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_ReadableFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quieten noisy third-party loggers
    for noisy in ("sqlalchemy.engine", "httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if not settings.DEBUG else logging.DEBUG
        )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Call in each module: logger = get_logger(__name__)"""
    return logging.getLogger(name)


# ── Structured event helpers ──────────────────────────────────────────────────

_app_logger = get_logger("ruralbiz.app")


def log_startup(version: str, environment: str, db_url_masked: str, ai_available: bool) -> None:
    _app_logger.info(
        "🚀 RuralBiz AI starting — version=%s env=%s db=%s ai=%s demo=%s",
        version, environment, db_url_masked,
        "available" if ai_available else "fallback-mode",
        settings.DEMO_MODE,
    )


def log_shutdown() -> None:
    _app_logger.info("🛑 RuralBiz AI shutting down.")


def log_api_error(
    path: str,
    method: str,
    status_code: int,
    detail: str,
    request_id: Optional[str] = None,
) -> None:
    _app_logger.warning(
        "API error — %s %s → %d | %s | req=%s",
        method, path, status_code, detail, request_id or "-",
    )


def log_auth_failure(reason: str, email_hint: Optional[str] = None) -> None:
    """Log auth failures WITHOUT logging the actual password or token."""
    hint = f" (email: {email_hint[:3]}***)" if email_hint else ""
    _app_logger.warning("Auth failure — %s%s", reason, hint)


def log_ai_status(available: bool, provider: str) -> None:
    if available:
        _app_logger.info("AI provider ready — %s", provider)
    else:
        _app_logger.warning(
            "AI provider unavailable (%s). Deterministic fallback active.", provider
        )


def log_external_api_failure(service: str, error: str) -> None:
    _app_logger.warning("External API failure — service=%s error=%s", service, error)


def log_db_error(operation: str, error: str) -> None:
    _app_logger.error("Database error — operation=%s error=%s", operation, error)


def mask_db_url(url: str) -> str:
    """Remove passwords from database URLs for safe logging."""
    import re
    return re.sub(r"://[^:]+:[^@]+@", "://***:***@", url)


def generate_request_id() -> str:
    return str(uuid4())
