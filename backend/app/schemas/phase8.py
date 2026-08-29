"""
Pydantic schemas for Phase 8: Personalized Recommendations, Saved Businesses,
Interactions, Natural Language Query, Entrepreneur Profile.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Entrepreneur Profile ──────────────────────────────────────────────────────

class EntrepreneurProfileIn(BaseModel):
    detailed_skills:            Optional[str]   = None
    education_level:            Optional[str]   = None
    experience_description:     Optional[str]   = None
    preferred_work_style:       Optional[str]   = None
    daily_available_hours:      Optional[float] = Field(None, ge=0, le=24)
    location_type:              Optional[str]   = None   # rural | semi_urban | urban
    preferred_business_types:   Optional[str]   = None
    family_business_experience: Optional[bool]  = None
    existing_assets:            Optional[str]   = None
    growth_preference:          Optional[str]   = None   # stable | balanced | aggressive
    business_goal:              Optional[str]   = None


class EntrepreneurProfileOut(EntrepreneurProfileIn):
    id:         str
    user_id:    str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Semantic match detail ─────────────────────────────────────────────────────

class SemanticMatchDetail(BaseModel):
    semantic_score:    float
    matched_concepts:  List[str]
    explanation:       str
    method:            str


# ── Score breakdown ───────────────────────────────────────────────────────────

class PersonalizedBreakdown(BaseModel):
    semantic_skill:       float
    budget:               float
    market_opportunity:   float
    financial_potential:  float
    experience:           float
    gov_support:          float
    risk:                 float
    interest:             float
    income_goal:          float
    location:             float
    preference_modifier:  float = 0.0


class PersonalizedScoreRaw(BaseModel):
    semantic_skill:       float
    budget:               float
    market_opportunity:   float
    financial_potential:  float
    experience:           float
    gov_support:          float
    risk:                 float
    interest:             float
    income_goal:          float
    location:             float


# ── Recommendation explanation ────────────────────────────────────────────────

class FinancialOutlook(BaseModel):
    min_investment:       float
    max_investment:       float
    monthly_profit_min:   float
    monthly_profit_max:   float
    risk_level:           str


class SemanticMatchSummary(BaseModel):
    score:        float
    concepts:     List[str]
    explanation:  str


class RecommendationExplanation(BaseModel):
    why_recommended:   List[str]
    strengths:         List[str]
    challenges:        List[str]
    next_steps:        List[str]
    financial_outlook: FinancialOutlook
    semantic_match:    SemanticMatchSummary
    disclaimer:        str


# ── Personalized recommendation item ─────────────────────────────────────────

class PersonalizedRecommendationItem(BaseModel):
    rank:           int
    business_id:    str
    business_name:  str
    category:       str
    business_type:  str
    risk_level:     str
    min_investment: float
    max_investment: float
    monthly_profit_min: float
    monthly_profit_max: float
    setup_time_weeks_min: int
    setup_time_weeks_max: int
    suitable_for_rural: bool
    description:    str
    required_skills: str

    final_score:    float
    breakdown:      PersonalizedBreakdown
    raw_scores:     PersonalizedScoreRaw
    semantic_detail: SemanticMatchDetail
    explanation:    RecommendationExplanation

    is_saved:       bool = False
    disclaimer:     str = (
        "⚠️ Estimated figures — actual results depend on execution, local conditions, and market factors."
    )


# ── Personalized recommendation request / response ───────────────────────────

class PersonalizedRecommendationRequest(BaseModel):
    available_capital:    Optional[float] = Field(None, ge=0)
    skills:               Optional[str]   = None
    business_interests:   Optional[str]   = None
    monthly_income_goal:  Optional[float] = Field(None, ge=0)
    preferred_risk:       Optional[str]   = None
    experience_years:     Optional[int]   = Field(None, ge=0)
    location_type:        Optional[str]   = None
    top_n:                int             = Field(8, ge=1, le=15)
    use_preferences:      bool            = True


class PersonalizedRecommendationResponse(BaseModel):
    recommendations:          List[PersonalizedRecommendationItem]
    profile_completeness:     int
    total_businesses_scored:  int
    ai_mode:                  str = "data"   # data | enhanced
    disclaimer:               str = (
        "⚠️ AI-assisted suggestions based on estimated data. "
        "Consult local experts before making business decisions."
    )


# ── Natural language query ────────────────────────────────────────────────────

class NaturalQueryRequest(BaseModel):
    query:          str = Field(..., min_length=3)
    top_n:          int = Field(5, ge=1, le=10)
    use_ai_parsing: bool = True


class ExtractedIntent(BaseModel):
    budget:               Optional[float]
    skills:               Optional[str]
    risk_preference:      Optional[str]
    business_type_hints:  List[str]
    location_type:        Optional[str]
    raw_query:            str


class NaturalQueryResponse(BaseModel):
    recommendations:  List[PersonalizedRecommendationItem]
    extracted_intent: ExtractedIntent
    parse_method:     str
    disclaimer:       str = (
        "⚠️ Natural language parsing is best-effort. "
        "Recommendations are based on estimated data only."
    )


# ── Interaction tracking ──────────────────────────────────────────────────────

class InteractionRequest(BaseModel):
    interaction_type: str = Field(
        ...,
        description="One of: viewed | saved | compared | dismissed | explored"
    )


class InteractionOut(BaseModel):
    id:               str
    business_id:      str
    interaction_type: str
    created_at:       datetime
    model_config = {"from_attributes": True}


class PreferenceSummary(BaseModel):
    preferred_categories: Dict[str, int]
    avoided_categories:   Dict[str, int]
    preferred_risk:       Optional[str]
    total_interactions:   int
    disclaimer:           str = "Preference adjustments are small (+/-10 pts max) and fully transparent."


# ── Saved businesses ──────────────────────────────────────────────────────────

class SavedBusinessIn(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class SavedBusinessOut(BaseModel):
    id:          str
    business_id: str
    notes:       Optional[str]
    created_at:  datetime
    model_config = {"from_attributes": True}


class SavedBusinessListOut(BaseModel):
    items: List[SavedBusinessOut]
    total: int
