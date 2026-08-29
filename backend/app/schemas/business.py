"""
Pydantic schemas for Business and Recommendation endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Business schemas
# ─────────────────────────────────────────────────────────────────────────────

class BusinessBase(BaseModel):
    name: str
    category: str
    description: str
    business_type: str
    suitable_for_rural: bool = True
    min_investment: float
    max_investment: float
    estimated_monthly_revenue_min: float
    estimated_monthly_revenue_max: float
    estimated_monthly_expenses_min: float
    estimated_monthly_expenses_max: float
    estimated_monthly_profit_min: float
    estimated_monthly_profit_max: float
    risk_level: str
    required_skills: str
    risk_factors: Optional[str] = None
    key_challenges: Optional[str] = None
    setup_time_weeks_min: int = 2
    setup_time_weeks_max: int = 8
    is_demo_data: bool = True


class BusinessPublic(BusinessBase):
    id: str
    # Computed helpers
    avg_investment: float = 0.0
    avg_monthly_profit: float = 0.0
    required_skills_list: List[str] = []
    risk_factors_list: List[str] = []
    key_challenges_list: List[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_extras(cls, b: "Business") -> "BusinessPublic":  # type: ignore[name-defined]
        obj = cls.model_validate(b)
        obj.avg_investment = (b.min_investment + b.max_investment) / 2
        obj.avg_monthly_profit = (b.estimated_monthly_profit_min + b.estimated_monthly_profit_max) / 2
        obj.required_skills_list = [s.strip() for s in b.required_skills.split(",") if s.strip()]
        obj.risk_factors_list = (
            [r.strip() for r in b.risk_factors.split(",") if r.strip()] if b.risk_factors else []
        )
        obj.key_challenges_list = (
            [c.strip() for c in b.key_challenges.split(",") if c.strip()] if b.key_challenges else []
        )
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation schemas
# ─────────────────────────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    budget: float = Field(..., ge=0, le=100, description="Budget compatibility score 0-100")
    skills: float = Field(..., ge=0, le=100, description="Skill match score 0-100")
    interest: float = Field(..., ge=0, le=100, description="Business interest match score 0-100")
    profit: float = Field(..., ge=0, le=100, description="Profit potential score 0-100")
    risk: float = Field(..., ge=0, le=100, description="Risk compatibility score 0-100")
    income_goal: float = Field(..., ge=0, le=100, description="Income goal compatibility 0-100")


class RecommendationItem(BaseModel):
    rank: int
    business: BusinessPublic
    final_score: float = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    reasons: List[str]
    disclaimer: str = (
        "⚠️ Estimated values — actual results depend on execution, local conditions, and market factors."
    )


class RecommendationRequest(BaseModel):
    """Optional overrides for recommendation scoring (uses user profile by default)."""
    available_capital: Optional[float] = Field(None, ge=0)
    skills: Optional[str] = None
    business_interests: Optional[str] = None
    monthly_income_goal: Optional[float] = Field(None, ge=0)
    preferred_risk: Optional[str] = None   # Low / Medium / High / Any
    top_n: int = Field(5, ge=1, le=10)


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    profile_completeness: int = Field(..., ge=0, le=100, description="% of profile filled")
    total_businesses_scored: int
    disclaimer: str = (
        "⚠️ These are AI-generated suggestions based on estimated data. "
        "Consult local experts before making business decisions."
    )


class BusinessListResponse(BaseModel):
    items: List[BusinessPublic]
    total: int
    disclaimer: str = "⚠️ Financial values are estimates for advisory purposes only."
