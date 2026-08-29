"""
SQLAlchemy Business model.
Stores business opportunity templates with financial estimates.
ALL financial values are ESTIMATES for demo/advisory purposes only.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Service", "Retail"
    suitable_for_rural: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Investment (INR) ──────────────────────────────────────────────────────
    min_investment: Mapped[float] = mapped_column(Float, nullable=False)
    max_investment: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Monthly Revenue estimate (INR) ─────────────────────────────────────
    estimated_monthly_revenue_min: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_monthly_revenue_max: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Monthly Expenses estimate (INR) ───────────────────────────────────
    estimated_monthly_expenses_min: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_monthly_expenses_max: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Monthly Profit estimate (INR) ─────────────────────────────────────
    estimated_monthly_profit_min: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_monthly_profit_max: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Risk & Requirements ───────────────────────────────────────────────
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # Low / Medium / High
    required_skills: Mapped[str] = mapped_column(Text, nullable=False)   # comma-separated
    risk_factors: Mapped[str] = mapped_column(Text, nullable=True)        # comma-separated descriptions
    key_challenges: Mapped[str] = mapped_column(Text, nullable=True)

    # ── Setup time ────────────────────────────────────────────────────────
    setup_time_weeks_min: Mapped[int] = mapped_column(Integer, default=2)
    setup_time_weeks_max: Mapped[int] = mapped_column(Integer, default=8)

    # ── Metadata ──────────────────────────────────────────────────────────
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<Business name={self.name} category={self.category}>"
