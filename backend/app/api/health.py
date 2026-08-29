"""
Health & readiness check endpoints — Phase 11.

GET /health         — basic status (backward-compatible)
GET /health/live    — liveness probe (is process running?)
GET /health/ready   — readiness probe (is DB reachable?)
GET /health/details — full diagnostic (safe, no secrets)
"""
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["Health"])

# Track startup time
_START_TIME = time.time()


# ── Response models ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:      str
    version:     str
    environment: str


class LivenessResponse(BaseModel):
    status:    str
    timestamp: str
    uptime_s:  float


class ReadinessResponse(BaseModel):
    status:   str
    database: str
    message:  Optional[str] = None


class AIStatusDetail(BaseModel):
    available:          bool
    fallback_available: bool
    provider:           str


class DetailedHealthResponse(BaseModel):
    status:      str
    version:     str
    environment: str
    demo_mode:   bool
    uptime_s:    float
    database:    str
    ai:          AIStatusDetail


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _check_database() -> tuple[str, str]:
    """Returns ('connected', '') or ('error', reason)."""
    try:
        from app.database.db import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "connected", ""
    except Exception as exc:
        return "error", str(exc)[:100]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic health check (backward-compatible)",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """
    Returns 200 when the service is up.
    Used by load balancers and monitoring tools.
    """
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe — is the process running?",
    tags=["Health"],
)
async def liveness() -> LivenessResponse:
    """
    Returns 200 as long as the Python process is alive.
    Suitable for Kubernetes liveness probes.
    """
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_s=round(time.time() - _START_TIME, 1),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe — can the service handle requests?",
    tags=["Health"],
)
async def readiness() -> ReadinessResponse:
    """
    Returns 200 when the database is reachable and the service is ready.
    Returns 503 if essential services are unavailable.
    """
    from fastapi import HTTPException
    db_status, db_error = await _check_database()
    if db_status != "connected":
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready — database: {db_error}",
        )
    return ReadinessResponse(
        status="ready",
        database="connected",
    )


@router.get(
    "/health/details",
    response_model=DetailedHealthResponse,
    summary="Detailed diagnostic (safe, no secrets exposed)",
    tags=["Health"],
)
async def health_details() -> DetailedHealthResponse:
    """
    Returns comprehensive health information for monitoring and debugging.
    Never exposes secrets, API keys, or passwords.
    """
    from app.services.ai_service import ai_service

    db_status, _ = await _check_database()

    return DetailedHealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        demo_mode=settings.DEMO_MODE,
        uptime_s=round(time.time() - _START_TIME, 1),
        database=db_status,
        ai=AIStatusDetail(
            available=ai_service.is_available(),
            fallback_available=True,  # always true — deterministic fallback
            provider=ai_service.provider if hasattr(ai_service, "provider") else "gemini",
        ),
    )
