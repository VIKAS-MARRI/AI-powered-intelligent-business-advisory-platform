"""
Phase 9 — AI Action Item model.
Stores generated next-action recommendations per user.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:          Mapped[str]        = mapped_column(String(36), nullable=False, index=True)
    title:            Mapped[str]        = mapped_column(String(200), nullable=False)
    description:      Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    category:         Mapped[str]        = mapped_column(String(40), nullable=False, default="business")
    # low | medium | high | critical
    priority:         Mapped[str]        = mapped_column(String(20), nullable=False, default="medium")
    # low | medium | high
    impact:           Mapped[str]        = mapped_column(String(20), nullable=False, default="medium")
    # minutes | quick | half-day | 1 hour | 1 day
    estimated_effort: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Link to platform phase
    related_phase:    Mapped[str | None] = mapped_column(String(20), nullable=True)
    action_url:       Mapped[str | None] = mapped_column(String(200), nullable=True)

    # pending | completed | dismissed
    status:           Mapped[str]        = mapped_column(String(20), nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<ActionItem id={self.id} title={self.title!r} status={self.status}>"
