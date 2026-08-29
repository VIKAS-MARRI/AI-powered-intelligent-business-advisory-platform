"""
Async SQLAlchemy database engine, session factory, and base model.
Supports SQLite (default) and PostgreSQL (set DATABASE_URL in .env).
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# SQLite needs check_same_thread=False passed via connect_args.
# PostgreSQL works without it, so we detect which DB we're using.
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
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
    """Create all tables if they do not already exist, then seed reference data."""
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

    # Seed government schemes if the table is empty
    from app.seed_schemes import seed_schemes
    async with AsyncSessionLocal() as db:
        await seed_schemes(db)
