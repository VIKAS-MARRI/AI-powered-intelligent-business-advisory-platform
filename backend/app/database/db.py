"""
Async SQLAlchemy database engine, session factory, and base model.
Supports SQLite (default) and PostgreSQL (set DATABASE_URL in .env).
"""
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _resolve_sqlite_url() -> str:
    """Keep SQLite files anchored to the backend project directory.

    This prevents local and hosted runs from creating different DB files depending on
    the shell's current working directory.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        relative = settings.DATABASE_URL.replace("sqlite+aiosqlite:///./", "", 1)
        if relative != settings.DATABASE_URL:
            return f"sqlite+aiosqlite:///{(settings.backend_root / relative).as_posix()}"
        if settings.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
            raw_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "", 1)
            path = Path(raw_path).expanduser()
            if not path.is_absolute():
                path = (settings.backend_root / path).resolve()
            return f"sqlite+aiosqlite:///{path.as_posix()}"
    return settings.DATABASE_URL

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# SQLite needs check_same_thread=False passed via connect_args.
# PostgreSQL works without it, so we detect which DB we're using.
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

resolved_database_url = _resolve_sqlite_url()
engine = create_async_engine(
    resolved_database_url,
    echo=settings.ENVIRONMENT == "development",
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependency — FastAPI Depends()
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and close it after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# DB initialisation (called at app startup)
# ---------------------------------------------------------------------------
async def init_db() -> None:
    """Create all tables if they do not already exist.

    Business/scheme seed data should be bootstrapped from startup code rather than
    re-entering this function from inside seeders, which causes recursive loops.
    """
    # Import models so that SQLAlchemy discovers them before create_all
    import app.models.user              # noqa: F401
    import app.models.business          # noqa: F401
    import app.models.scheme            # noqa: F401
    import app.models.advisory          # noqa: F401
    import app.models.phase8            # noqa: F401
    import app.models.goal              # noqa: F401
    import app.models.financial_progress # noqa: F401
    import app.models.activity          # noqa: F401
    import app.models.action_item       # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Development-time compatibility: add recently-introduced columns
    # to SQLite tables when running against an older schema created
    # without Alembic migrations. This keeps the local dev DB usable
    # after adding small model fields during iterative phases.
    if _is_sqlite:
        from sqlalchemy import text
        async with engine.begin() as conn:
            # Check `users` table for `simple_language_mode` column
            res = await conn.execute(text("PRAGMA table_info('users')"))
            rows = res.fetchall()
            cols = [r[1] for r in rows]
            if 'simple_language_mode' not in cols:
                # Add boolean column with default 0 (False)
                await conn.execute(text("ALTER TABLE users ADD COLUMN simple_language_mode BOOLEAN DEFAULT 0"))
            # Check `advisory_sessions` for language-related columns added in later phases
            res = await conn.execute(text("PRAGMA table_info('advisory_sessions')"))
            rows = res.fetchall()
            cols = [r[1] for r in rows]
            if 'original_language' not in cols:
                await conn.execute(text("ALTER TABLE advisory_sessions ADD COLUMN original_language TEXT DEFAULT 'en'"))
            if 'response_language' not in cols:
                await conn.execute(text("ALTER TABLE advisory_sessions ADD COLUMN response_language TEXT DEFAULT 'en'"))
            if 'canonical_query' not in cols:
                # `canonical_query` holds a normalized form of user queries for analytics/search.
                # Add as nullable text so existing rows remain valid.
                await conn.execute(text("ALTER TABLE advisory_sessions ADD COLUMN canonical_query TEXT DEFAULT NULL"))

    # Startup-level bootstrap is handled in app.main.lifespan(); keep init_db() as
    # a database-creation primitive without re-triggering seeders recursively.
    # Avoid side effects here to prevent duplicate startup loops when seeding.
    return None
