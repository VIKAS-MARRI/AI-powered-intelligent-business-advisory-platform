"""
Phase 9 — Entrepreneur Business Goal model.
Tracks goals with progress, status, and overdue detection.
"""
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class BusinessGoal(Base):
    __tablename__ = "business_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:      Mapped[str]          = mapped_column(String(36), nullable=False, index=True)
    title:        Mapped[str]          = mapped_column(String(200), nullable=False)
    description:  Mapped[str | None]   = mapped_column(Text, nullable=True)

    # Typing
    goal_type:    Mapped[str]          = mapped_column(String(60), nullable=False, default="general")
    # not_started | in_progress | completed | overdue
    status:       Mapped[str]          = mapped_column(String(30), nullable=False, default="not_started")
    # low | medium | high
    priority:     Mapped[str]          = mapped_column(String(20), nullable=False, default="medium")

    # Progress
    target_value:  Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    unit:          Mapped[str | None]   = mapped_column(String(30), nullable=True)  # ₹, %, customers, …

    # Dates
    start_date:   Mapped[date | None]  = mapped_column(Date, nullable=True)
    target_date:  Mapped[date | None]  = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # ── Computed helpers (not stored) ─────────────────────────────────────────
    @property
    def progress_percentage(self) -> float:
        if self.target_value and self.target_value > 0 and self.current_value is not None:
            return round(min(100.0, (self.current_value / self.target_value) * 100), 1)
        if self.status == "completed":
            return 100.0
        return 0.0

    @property
    def days_remaining(self) -> int | None:
        if not self.target_date:
            return None
        today = date.today()
        return (self.target_date - today).days

    @property
    def is_overdue(self) -> bool:
        if self.status == "completed":
            return False
        if self.target_date and date.today() > self.target_date:
            return True
        return False

    def __repr__(self) -> str:
        return f"<BusinessGoal id={self.id} title={self.title!r} status={self.status}>"
