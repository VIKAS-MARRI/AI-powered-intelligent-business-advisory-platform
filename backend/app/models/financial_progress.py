"""
Phase 9 — Financial Progress Record model.
Entrepreneur-entered periodic business metrics.
"""
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class FinancialProgressRecord(Base):
    __tablename__ = "financial_progress_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:     Mapped[str]          = mapped_column(String(36), nullable=False, index=True)
    business_id: Mapped[str | None]   = mapped_column(String(36), nullable=True, index=True)

    record_date: Mapped[date]         = mapped_column(Date, nullable=False)

    # Entrepreneur-entered data (INR)
    revenue:        Mapped[float | None] = mapped_column(Float, nullable=True)
    expenses:       Mapped[float | None] = mapped_column(Float, nullable=True)
    # profit = revenue - expenses (computed at write; stored for query efficiency)
    profit:         Mapped[float | None] = mapped_column(Float, nullable=True)
    customers:      Mapped[float | None] = mapped_column(Float, nullable=True)
    investment:     Mapped[float | None] = mapped_column(Float, nullable=True)
    savings:        Mapped[float | None] = mapped_column(Float, nullable=True)
    inventory_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<FinancialProgressRecord id={self.id} date={self.record_date} profit={self.profit}>"
