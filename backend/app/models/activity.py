"""
Phase 9 — Entrepreneur Activity Log model.
Tracks key milestones and events in the user's business journey.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


# Activity type constants
ACTIVITY_TYPES = {
    "account_created":        "Account Created",
    "profile_completed":      "Profile Completed",
    "recommendation_viewed":  "Business Recommendation Viewed",
    "business_saved":         "Business Saved",
    "financial_analysis":     "Financial Analysis Completed",
    "investment_optimized":   "Investment Optimization Run",
    "market_analyzed":        "Market Analysis Performed",
    "scheme_matched":         "Government Scheme Found",
    "goal_created":           "Goal Created",
    "goal_completed":         "Goal Completed",
    "goal_updated":           "Goal Progress Updated",
    "financial_record_added": "Financial Record Added",
    "ai_advisory":            "AI Advisory Session",
    "advisor_query":          "AI Advisor Queried",
}


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:       Mapped[str]        = mapped_column(String(36), nullable=False, index=True)
    activity_type: Mapped[str]        = mapped_column(String(60), nullable=False)
    title:         Mapped[str]        = mapped_column(String(200), nullable=False)
    description:   Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_id:  Mapped[str | None] = mapped_column(String(36), nullable=True)   # linked entity id
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)          # extra JSON data
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ActivityLog user={self.user_id} type={self.activity_type}>"
