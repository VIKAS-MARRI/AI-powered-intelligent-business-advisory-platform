"""
Phase 8 models: RecommendationInteraction, SavedBusiness, EntrepreneurProfile.
Migration-safe: uses nullable columns and SQLite-compatible ALTER TABLE via init_db.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class RecommendationInteraction(Base):
    """Tracks user interactions with recommended businesses."""
    __tablename__ = "recommendation_interactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id:          Mapped[str]   = mapped_column(String(36), nullable=False, index=True)
    business_id:      Mapped[str]   = mapped_column(String(36), nullable=False, index=True)
    # viewed | saved | compared | dismissed | explored
    interaction_type: Mapped[str]   = mapped_column(String(30), nullable=False)
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self) -> str:
        return f"<Interaction user={self.user_id} biz={self.business_id} type={self.interaction_type}>"


class SavedBusiness(Base):
    """User's saved / favourited businesses."""
    __tablename__ = "saved_businesses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id:     Mapped[str]        = mapped_column(String(36), nullable=False, index=True)
    business_id: Mapped[str]        = mapped_column(String(36), nullable=False, index=True)
    notes:       Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self) -> str:
        return f"<SavedBusiness user={self.user_id} biz={self.business_id}>"


class EntrepreneurProfile(Base):
    """
    Extended entrepreneur intelligence profile (Phase 8).
    Stores rich context beyond what fits in the User model.
    One-to-one with User (user_id is unique).
    """
    __tablename__ = "entrepreneur_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )

    # Detailed skills / experience
    detailed_skills:           Mapped[str | None] = mapped_column(Text, nullable=True)
    education_level:           Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_description:    Mapped[str | None] = mapped_column(Text, nullable=True)

    # Work preferences
    preferred_work_style:      Mapped[str | None] = mapped_column(String(50), nullable=True)
    # service | manufacturing | agriculture | retail | digital
    daily_available_hours:     Mapped[float | None] = mapped_column(Float, nullable=True)
    # rural | semi_urban | urban
    location_type:             Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Business goals
    preferred_business_types:  Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-sep
    family_business_experience: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    existing_assets:           Mapped[str | None] = mapped_column(Text, nullable=True)
    # stable | balanced | aggressive
    growth_preference:         Mapped[str | None] = mapped_column(String(30), nullable=True)
    business_goal:             Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    def __repr__(self) -> str:
        return f"<EntrepreneurProfile user={self.user_id}>"
