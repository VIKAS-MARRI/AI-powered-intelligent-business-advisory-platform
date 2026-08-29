"""
RuralBiz AI — FastAPI application entry point (Phase 11: Production Ready).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import setup_logging, log_startup, log_shutdown, mask_db_url
from app.core.exceptions import register_exception_handlers
from app.database.db import init_db
from app.api import health, auth, users, businesses, recommendations, finance, optimizer
from app.api.market import locations_router, market_router
from app.api.schemes import router as schemes_router
from app.api.advisor import router as advisor_router
from app.api.phase8 import router as phase8_router, saved_router
from app.api.analytics import (
    goals_router, progress_router, analytics_router, actions_router, activity_router
)
from app.api.language import languages_router, lang_user_router, translate_router
from app.api.demo import router as demo_router

# ── Logging setup (must be first) ─────────────────────────────────────────────
setup_logging()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Automatically seed businesses if the database is empty
    try:
        from app.seed_businesses import seed_businesses

        inserted, skipped = await seed_businesses()

        print(
            f"Business database seeding completed: "
            f"{inserted} inserted, {skipped} skipped"
        )
    except Exception as e:
        print(f"Business database seeding error: {e}")

    from app.services.ai_service import ai_service

    log_startup(
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        db_url_masked=mask_db_url(settings.DATABASE_URL),
        ai_available=ai_service.is_available(),
    )



# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title="RuralBiz AI",
    version=settings.APP_VERSION,
    description=(
        "**RuralBiz AI** — An AI-Driven Hyper-Local Business Advisory & Financial Structuring "
        "Assistant for Rural Micro-Entrepreneurs in India.\n\n"
        "## Features\n"
        "- 🤖 **LangGraph Multi-Agent AI Advisor** (Gemini + deterministic fallback)\n"
        "- 💼 **Personalized Business Recommendations** (Phase 2)\n"
        "- 📊 **Financial Intelligence** — ROI, break-even, cash flow (Phase 3)\n"
        "- ⚡ **OR-Tools Investment Optimizer** (Phase 4)\n"
        "- 🗺️ **Hyper-Local Market Intelligence** via OpenStreetMap (Phase 5)\n"
        "- 🏛️ **Government Scheme Matching** — PMEGP, MUDRA, etc. (Phase 6)\n"
        "- 📈 **Entrepreneur Analytics & Goal Tracking** (Phase 9)\n"
        "- 🌐 **Multilingual** — English, Hindi, Telugu (Phase 10)\n"
        "- 🎙️ **Voice Input & TTS** (Phase 10)\n\n"
        "## Authentication\n"
        "Most endpoints require `Authorization: Bearer <token>` from `/auth/login`.\n\n"
        "## Fallback Mode\n"
        "All features work without `GEMINI_API_KEY` using deterministic algorithms."
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

# ── Rate limiter state ────────────────────────────────────────────────────────
app.state.limiter = limiter

# ── Middleware ────────────────────────────────────────────────────────────────

# CORS (must be before SlowAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(SlowAPIMiddleware)

# Security headers (Phase 11, Section 5)
if settings.SECURE_HEADERS:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]         = "DENY"
        response.headers["X-XSS-Protection"]        = "1; mode=block"
        response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    from app.core.logging import generate_request_id
    request.state.request_id = generate_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# Rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(businesses.router)
app.include_router(recommendations.router)
app.include_router(finance.router)
app.include_router(optimizer.router)
app.include_router(locations_router)
app.include_router(market_router)
app.include_router(schemes_router)
app.include_router(advisor_router)
app.include_router(phase8_router)
app.include_router(saved_router)
app.include_router(goals_router)
app.include_router(progress_router)
app.include_router(analytics_router)
app.include_router(actions_router)
app.include_router(activity_router)
# Phase 10 — Language & Translation
app.include_router(languages_router)
app.include_router(lang_user_router)
app.include_router(translate_router)
# Phase 11 — Demo Mode
app.include_router(demo_router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "RuralBiz AI API",
        "version": settings.APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
        "demo":    settings.DEMO_MODE,
    }
