"""
Application configuration — Phase 11 production-ready.

Reads from environment variables or .env file.
Supports: development | testing | production

Rules:
  - Never log or return secrets.
  - GEMINI_API_KEY is optional (deterministic fallback always works).
  - SQLite is allowed in development/testing.
  - Production enforces secure JWT secret.
"""
import warnings
from pathlib import Path
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT = {"change-me-to-a-long-random-secret", "secret", "changeme", "insecure"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App metadata ───────────────────────────────────────────────────────────
    APP_NAME:    str = "RuralBiz AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV:     str = "development"    # alias kept for compatibility
    ENVIRONMENT: str = "development"    # canonical name used internally
    DEBUG:       bool = False

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./ruralbiz.db"

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def resolved_database_path(self) -> Path:
        url = self.DATABASE_URL
        if url.startswith("sqlite"):
            if url.startswith("sqlite+aiosqlite:///./"):
                return self.backend_root / url.replace("sqlite+aiosqlite:///./", "")
            if url.startswith("sqlite+aiosqlite:///"):
                db_path = url.replace("sqlite+aiosqlite:///", "", 1)
                return Path(db_path).expanduser()
        return self.backend_root / "ruralbiz.db"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY:              str = "change-me-to-a-long-random-secret"
    JWT_ALGORITHM:               str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ──────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── AI / Gemini ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""         # optional — fallback mode works without it
    GEMINI_MODEL:   str = "gemini-1.5-flash"
    AI_MAX_RETRIES: int = 2
    AI_TIMEOUT_SEC: int = 30

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_ENABLED:      bool = True
    RATE_LIMIT_AUTH:         str  = "10/minute"
    RATE_LIMIT_ADVISOR:      str  = "20/minute"
    RATE_LIMIT_TRANSLATE:    str  = "30/minute"
    RATE_LIMIT_DEFAULT:      str  = "100/minute"

    # ── Demo mode (Section 9) ─────────────────────────────────────────────────
    DEMO_MODE: bool = False

    # ── Security ──────────────────────────────────────────────────────────────
    SECURE_HEADERS: bool = True

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [o.strip() for o in v.split(",")]
        return v

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalise_environment(cls, v):
        v = str(v).lower().strip()
        if v not in {"development", "testing", "production"}:
            warnings.warn(
                f"Unknown ENVIRONMENT '{v}'. Defaulting to 'development'.",
                stacklevel=2,
            )
            return "development"
        return v

    @model_validator(mode="after")
    def production_checks(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            # Insecure JWT secret in production is dangerous
            if self.JWT_SECRET_KEY in _INSECURE_JWT or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "PRODUCTION requires JWT_SECRET_KEY to be a random string of ≥32 chars. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            # SQLite is strongly discouraged in production
            if self.DATABASE_URL.startswith("sqlite"):
                warnings.warn(
                    "SQLite is NOT recommended for production. "
                    "Set DATABASE_URL to a PostgreSQL connection string.",
                    stacklevel=2,
                )
            # DEBUG must be off in production
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production.")
        return self

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    @property
    def ai_available(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())


settings = Settings()
