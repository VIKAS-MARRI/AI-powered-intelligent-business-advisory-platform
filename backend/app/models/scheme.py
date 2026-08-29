"""
SQLAlchemy Scheme model — Phase 6 Government Scheme Intelligence.

Stores curated government scheme/program records.
Supports national + state-level schemes for Indian rural micro-entrepreneurs.

IMPORTANT: All scheme data must be sourced from official government publications.
Fields that cannot be reliably verified must be marked as demo data.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name:              Mapped[str]      = mapped_column(String(300), nullable=False, index=True)
    slug:              Mapped[str]      = mapped_column(String(200), unique=True, nullable=False, index=True)
    short_description: Mapped[str]      = mapped_column(Text, nullable=False)
    full_description:  Mapped[str|None] = mapped_column(Text, nullable=True)

    # ── Classification ────────────────────────────────────────────────────────
    # category: "Loan" | "Subsidy" | "Grant" | "Training" | "Mixed" | "Enterprise Support"
    category:             Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    # sector: "Agriculture" | "MSME" | "Manufacturing" | "Services" | "Food Processing" | "General"
    sector:               Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    # Who can apply (text list, comma-separated)
    target_beneficiaries: Mapped[str]      = mapped_column(Text, nullable=False)
    # Location scope: "National" | "State"
    location_scope:       Mapped[str]      = mapped_column(String(50), default="National", nullable=False)
    # If State scope, which state(s) — comma-separated or "All"
    states:               Mapped[str]      = mapped_column(Text, default="All", nullable=False)
    # Business categories this scheme applies to (comma-separated keywords)
    business_categories:  Mapped[str]      = mapped_column(Text, nullable=False)
    # OSM-like tags for business matching (comma-separated)
    business_tags:        Mapped[str|None] = mapped_column(Text, nullable=True)

    # ── Age Eligibility ───────────────────────────────────────────────────────
    minimum_age: Mapped[int|None]   = mapped_column(Integer, nullable=True)
    maximum_age: Mapped[int|None]   = mapped_column(Integer, nullable=True)

    # ── Investment Range (INR) ────────────────────────────────────────────────
    minimum_investment: Mapped[float|None] = mapped_column(Float, nullable=True)
    maximum_investment: Mapped[float|None] = mapped_column(Float, nullable=True)

    # ── Financial Support ─────────────────────────────────────────────────────
    maximum_loan_amount:    Mapped[float|None] = mapped_column(Float, nullable=True)
    maximum_subsidy_amount: Mapped[float|None] = mapped_column(Float, nullable=True)
    subsidy_percentage:     Mapped[float|None] = mapped_column(Float, nullable=True)
    # e.g. "Up to ₹10 lakh loan at 7% p.a." — human readable benefit
    key_benefit:            Mapped[str|None]   = mapped_column(String(500), nullable=True)

    # ── Eligibility & Application ─────────────────────────────────────────────
    # Stored as JSON-encoded strings for SQLite compatibility
    eligibility_requirements: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    required_documents:       Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    application_steps:        Mapped[str] = mapped_column(Text, nullable=False)  # JSON array

    # ── Flags ─────────────────────────────────────────────────────────────────
    is_women_specific:  Mapped[bool] = mapped_column(Boolean, default=False)
    is_sc_st_specific:  Mapped[bool] = mapped_column(Boolean, default=False)
    is_rural_specific:  Mapped[bool] = mapped_column(Boolean, default=False)
    is_youth_specific:  Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Source & Provenance ───────────────────────────────────────────────────
    official_source:   Mapped[str]      = mapped_column(String(500), nullable=False)
    official_url:      Mapped[str]      = mapped_column(String(1000), nullable=False)
    # "verified" = sourced from official publications; "demo" = illustrative
    data_status:       Mapped[str]      = mapped_column(String(20), default="demo", nullable=False)
    last_reviewed:     Mapped[str]      = mapped_column(String(30), default="2024-01", nullable=False)

    # ── Metadata ──────────────────────────────────────────────────────────────
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    sort_order: Mapped[int]      = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<Scheme name={self.name} category={self.category} status={self.data_status}>"
