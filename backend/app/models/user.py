"""
SQLAlchemy User model.
Stores authentication credentials and the basic entrepreneur profile.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    # Primary key — UUID stored as string for SQLite compatibility
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ---- Auth fields -------------------------------------------------------
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # ---- Basic profile -----------------------------------------------------
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    simple_language_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    # Location
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village_town: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Business profile
    available_capital: Mapped[float | None] = mapped_column(Float, nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated or JSON
    experience_years: Mapped[int | None] = mapped_column(nullable=True)
    business_interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_income_goal: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ---- Timestamps --------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
