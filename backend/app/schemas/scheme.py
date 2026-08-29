"""
Pydantic schemas for Phase 6 Government Scheme API.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class SchemeMatchRequest(BaseModel):
    """POST /schemes/match"""
    business_id:          str
    estimated_investment: float = Field(..., gt=0, description="Total estimated investment in INR")
    available_capital:    float = Field(..., ge=0,  description="Capital the user has available")
    state:                Optional[str]  = Field(None, description="User's state for location matching")
    user_age:             Optional[int]  = Field(None, ge=10, le=100)
    is_woman:             Optional[bool] = None
    is_sc_st:             Optional[bool] = None
    is_rural:             Optional[bool] = None

class SchemeCompareRequest(BaseModel):
    """POST /schemes/compare"""
    scheme_ids:           List[str]      = Field(..., min_length=2, max_length=4)
    business_id:          Optional[str]  = None
    estimated_investment: Optional[float]= Field(None, gt=0)
    available_capital:    Optional[float]= Field(None, ge=0)
    state:                Optional[str]  = None


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class SchemeOut(BaseModel):
    """Full scheme details."""
    id:                       str
    name:                     str
    slug:                     str
    short_description:        str
    full_description:         Optional[str]
    category:                 str
    sector:                   str
    target_beneficiaries:     str
    location_scope:           str
    states:                   str
    business_categories:      str
    minimum_age:              Optional[int]
    maximum_age:              Optional[int]
    minimum_investment:       Optional[float]
    maximum_investment:       Optional[float]
    maximum_loan_amount:      Optional[float]
    maximum_subsidy_amount:   Optional[float]
    subsidy_percentage:       Optional[float]
    key_benefit:              Optional[str]
    eligibility_requirements: List[str]
    required_documents:       List[str]
    application_steps:        List[str]
    is_women_specific:        bool
    is_sc_st_specific:        bool
    is_rural_specific:        bool
    is_youth_specific:        bool
    official_source:          str
    official_url:             str
    data_status:              str
    last_reviewed:            str
    sort_order:               int


class SchemeSummaryOut(BaseModel):
    """Compact scheme card (list views)."""
    id:                     str
    name:                   str
    slug:                   str
    short_description:      str
    category:               str
    sector:                 str
    location_scope:         str
    key_benefit:            Optional[str]
    maximum_loan_amount:    Optional[float]
    maximum_subsidy_amount: Optional[float]
    subsidy_percentage:     Optional[float]
    is_women_specific:      bool
    is_sc_st_specific:      bool
    is_rural_specific:      bool
    is_youth_specific:      bool
    official_url:           str
    data_status:            str
    last_reviewed:          str


class ScoreBreakdownOut(BaseModel):
    business_relevance:       float
    sector_match:             float
    investment_compatibility: float
    location_eligibility:     float
    profile_eligibility:      float
    total:                    float


class EligibilityFlagOut(BaseModel):
    status:              str
    reasons:             List[str]
    missing_information: List[str]


class SchemeMatchOut(BaseModel):
    scheme_id:         str
    scheme_name:       str
    scheme_slug:       str
    category:          str
    sector:            str
    data_status:       str
    key_benefit:       str
    official_url:      str
    score_breakdown:   ScoreBreakdownOut
    eligibility:       EligibilityFlagOut
    match_reasons:     List[str]
    funding_relevance: str
    tags:              List[str]


class FundingGapOut(BaseModel):
    estimated_investment: float
    available_capital:    float
    funding_gap:          float
    gap_percentage:       float
    has_gap:              bool
    gap_label:            str


class MatchResultOut(BaseModel):
    funding_gap:   FundingGapOut
    matches:       List[SchemeMatchOut]
    best_overall:  Optional[str]
    best_loan:     Optional[str]
    best_subsidy:  Optional[str]
    best_rural:    Optional[str]
    total_schemes: int
    disclaimer:    str


class CategoriesOut(BaseModel):
    categories: List[str]
    sectors:    List[str]


class SchemesListOut(BaseModel):
    items:  List[SchemeSummaryOut]
    total:  int
