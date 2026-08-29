"""
RuralBiz AI — FastAPI application entry point (Phase 11: Production Ready).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import (
    setup_logging,
    log_startup,
    log_shutdown,
    mask_db_url,
)
from app.core.exceptions import register_exception_handlers
from app.database.db import init_db

from app.api import (
    health,
    auth,
    users,
    businesses,
    recommendations,
    finance,
    optimizer,
)

from app.api.market import locations_router, market_router
from app.api.schemes import router as schemes_router
from app.api.advisor import router as advisor_router
from app.api.phase8 import router as phase8_router, saved_router

from app.api.analytics import (
    goals_router,
    progress_router,
    analytics_router,
    actions_router,
    activity_router,
)

from app.api.language import (
    languages_router,
    lang_user_router,
    translate_router,
)

from app.api.demo import router as demo_router


# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────

setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiter
# ─────────────────────────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)


# ─────────────────────────────────────────────────────────────────────────────
# Application lifespan
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ── STARTUP ──────────────────────────────────────────────────────────────

    # Initialize database and create tables
    await init_db()

    # Automatically seed business database on startup, regardless of launch path.
    # This uses the same DATABASE_URL as the running app and runs only after the
    # schema is initialized, avoiding circular startup re-entry.
    try:
        from app.seed_businesses import ensure_businesses_seeded

        print("Checking and seeding business database...")

        inserted, skipped = await ensure_businesses_seeded()

        print(
            f"Business database seeding completed: "
            f"{inserted} inserted, {skipped} skipped."
        )

    except Exception as e:
        print(f"WARNING: Business database seeding failed: {e}")

    # AI service
    from app.services.ai_service import ai_service

    # Application startup logging
    log_startup(
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        db_url_masked=mask_db_url(settings.DATABASE_URL),
        ai_available=ai_service.is_available(),
    )

    # Application runs here
    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────

    log_shutdown()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RuralBiz AI",
    version=settings.APP_VERSION,
    description=(
        "**RuralBiz AI** — An AI-Driven Hyper-Local Business Advisory "
        "& Financial Structuring Assistant for Rural Micro-Entrepreneurs "
        "in India.\n\n"

        "## Features\n"
        "- 🤖 **LangGraph Multi-Agent AI Advisor** "
        "(Gemini + deterministic fallback)\n"
        "- 💼 **Personalized Business Recommendations**\n"
        "- 📊 **Financial Intelligence** — ROI, break-even, cash flow\n"
        "- ⚡ **OR-Tools Investment Optimizer**\n"
        "- 🗺️ **Hyper-Local Market Intelligence** via OpenStreetMap\n"
        "- 🏛️ **Government Scheme Matching** — PMEGP, MUDRA, etc.\n"
        "- 📈 **Entrepreneur Analytics & Goal Tracking**\n"
        "- 🌐 **Multilingual** — English, Hindi, Telugu\n"
        "- 🎙️ **Voice Input & TTS**\n\n"

        "## Authentication\n"
        "Most endpoints require `Authorization: Bearer <token>` "
        "from `/auth/login`.\n\n"

        "## Fallback Mode\n"
        "All features work without `GEMINI_API_KEY` using "
        "deterministic algorithms."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "RuralBiz AI Team",
    },
    license_info={
        "name": "MIT",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiter state
# ─────────────────────────────────────────────────────────────────────────────

app.state.limiter = limiter


# ─────────────────────────────────────────────────────────────────────────────
# CORS Middleware
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting middleware
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(SlowAPIMiddleware)


# ─────────────────────────────────────────────────────────────────────────────
# Security headers
# ─────────────────────────────────────────────────────────────────────────────

if settings.SECURE_HEADERS:

    @app.middleware("http")
    async def add_security_headers(
        request: Request,
        call_next,
    ):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        if settings.is_production:
            response.headers[
                "Strict-Transport-Security"
            ] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


# ─────────────────────────────────────────────────────────────────────────────
# Request ID middleware
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):

    from app.core.logging import generate_request_id

    request.state.request_id = generate_request_id()

    response = await call_next(request)

    response.headers[
        "X-Request-ID"
    ] = request.state.request_id

    return response


# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

register_exception_handlers(app)

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ─────────────────────────────────────────────────────────────────────────────
# API Routers
# ─────────────────────────────────────────────────────────────────────────────

# Health
app.include_router(health.router)

# Authentication
app.include_router(auth.router)

# Users
app.include_router(users.router)

# Businesses
app.include_router(businesses.router)

# Recommendations
app.include_router(recommendations.router)

# Financial intelligence
app.include_router(finance.router)

# Investment optimizer
app.include_router(optimizer.router)

# Market intelligence
app.include_router(locations_router)
app.include_router(market_router)

# Government schemes
app.include_router(schemes_router)

# AI Advisor
app.include_router(advisor_router)

# Phase 8
app.include_router(phase8_router)
app.include_router(saved_router)

# Analytics
app.include_router(goals_router)
app.include_router(progress_router)
app.include_router(analytics_router)
app.include_router(actions_router)
app.include_router(activity_router)

# Languages and translation
app.include_router(languages_router)
app.include_router(lang_user_router)
app.include_router(translate_router)

# Demo mode
app.include_router(demo_router)


# ─────────────────────────────────────────────────────────────────────────────
# Root endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():

    return {
        "message": "RuralBiz AI API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "demo": settings.DEMO_MODE,
    }