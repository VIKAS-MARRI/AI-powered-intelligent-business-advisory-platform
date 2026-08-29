"""
Advisory session model — Phase 7.
Stores user advisory queries and results for history.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AdvisorySession(Base):
    __tablename__ = "advisory_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Input ─────────────────────────────────────────────────────────────────
    question:          Mapped[str]           = mapped_column(Text, nullable=False)
    available_capital: Mapped[float | None]  = mapped_column(Float, nullable=True)
    business_id:       Mapped[str | None]    = mapped_column(String(36), nullable=True)
    latitude:          Mapped[float | None]  = mapped_column(Float, nullable=True)
    longitude:         Mapped[float | None]  = mapped_column(Float, nullable=True)
    state_name:        Mapped[str | None]    = mapped_column(String(100), nullable=True)

    # ── Routing ────────────────────────────────────────────────────────────────
    required_agents: Mapped[str | None] = mapped_column(String(200), nullable=True)  # JSON list

    # ── Results (stored as JSON text) ─────────────────────────────────────────
    business_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    finance_result:  Mapped[str | None] = mapped_column(Text, nullable=True)
    market_result:   Mapped[str | None] = mapped_column(Text, nullable=True)
    scheme_result:   Mapped[str | None] = mapped_column(Text, nullable=True)
    final_advice:    Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    ai_status: Mapped[str] = mapped_column(String(20), default="unavailable")
    status:    Mapped[str] = mapped_column(String(20), default="completed")

    # ── Phase 10 language metadata ─────────────────────────────────────────────
    original_language:  Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")
    canonical_query:    Mapped[str | None] = mapped_column(Text, nullable=True)  # English version
    response_language:  Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
