"""
Phase 9 Pydantic schemas — Goals, Financial Progress, Analytics, Actions, Timeline.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Goals ─────────────────────────────────────────────────────────────────────

GOAL_TYPES = [
    "start_business", "revenue_target", "profit_target", "savings_capital",
    "apply_scheme", "business_registration", "improve_skills",
    "reduce_expenses", "customer_growth", "general",
]

GOAL_STATUSES   = ["not_started", "in_progress", "completed", "overdue"]
GOAL_PRIORITIES = ["low", "medium", "high"]


class GoalCreate(BaseModel):
    title:         str            = Field(..., min_length=2, max_length=200)
    description:   Optional[str] = None
    goal_type:     str            = Field("general")
    priority:      str            = Field("medium")
    target_value:  Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit:          Optional[str]  = Field(None, max_length=30)
    start_date:    Optional[date] = None
    target_date:   Optional[date] = None


class GoalUpdate(BaseModel):
    title:         Optional[str]   = Field(None, min_length=2, max_length=200)
    description:   Optional[str]   = None
    goal_type:     Optional[str]   = None
    priority:      Optional[str]   = None
    status:        Optional[str]   = None
    target_value:  Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit:          Optional[str]   = None
    start_date:    Optional[date]  = None
    target_date:   Optional[date]  = None


class GoalProgressUpdate(BaseModel):
    current_value: float = Field(..., ge=0)
    notes:         Optional[str] = None


class GoalOut(BaseModel):
    id:               str
    user_id:          str
    title:            str
    description:      Optional[str]
    goal_type:        str
    status:           str
    priority:         str
    target_value:     Optional[float]
    current_value:    Optional[float]
    unit:             Optional[str]
    start_date:       Optional[date]
    target_date:      Optional[date]
    progress_percentage: float
    days_remaining:   Optional[int]
    is_overdue:       bool
    created_at:       datetime
    updated_at:       datetime
    model_config = {"from_attributes": True}


class GoalListOut(BaseModel):
    items:  List[GoalOut]
    total:  int


# ── Financial Progress ────────────────────────────────────────────────────────

class FinancialRecordCreate(BaseModel):
    record_date:    date
    revenue:        Optional[float] = Field(None, ge=0)
    expenses:       Optional[float] = Field(None, ge=0)
    customers:      Optional[float] = Field(None, ge=0)
    investment:     Optional[float] = Field(None, ge=0)
    savings:        Optional[float] = Field(None, ge=0)
    inventory_cost: Optional[float] = Field(None, ge=0)
    business_id:    Optional[str]   = None
    notes:          Optional[str]   = Field(None, max_length=500)

    @model_validator(mode="after")
    def compute_profit(self) -> "FinancialRecordCreate":
        # profit computed server-side — do not accept from client
        return self


class FinancialRecordUpdate(BaseModel):
    record_date:    Optional[date]  = None
    revenue:        Optional[float] = Field(None, ge=0)
    expenses:       Optional[float] = Field(None, ge=0)
    customers:      Optional[float] = Field(None, ge=0)
    investment:     Optional[float] = Field(None, ge=0)
    savings:        Optional[float] = Field(None, ge=0)
    inventory_cost: Optional[float] = Field(None, ge=0)
    notes:          Optional[str]   = None


class FinancialRecordOut(BaseModel):
    id:             str
    user_id:        str
    business_id:    Optional[str]
    record_date:    date
    revenue:        Optional[float]
    expenses:       Optional[float]
    profit:         Optional[float]
    customers:      Optional[float]
    investment:     Optional[float]
    savings:        Optional[float]
    inventory_cost: Optional[float]
    notes:          Optional[str]
    created_at:     datetime
    updated_at:     datetime
    model_config = {"from_attributes": True}


class FinancialRecordListOut(BaseModel):
    items:         List[FinancialRecordOut]
    total:         int
    disclaimer:    str = "⚠️ Entrepreneur-entered data — not verified financial records."


# ── Analytics ─────────────────────────────────────────────────────────────────

class ProgressScoreOut(BaseModel):
    overall_score:    float
    category_scores:  Dict[str, float]
    weights:          Dict[str, float]
    strengths:        List[str]
    improvement_areas: List[str]
    confidence:       str
    score_explanation: str
    disclaimer:       str


class FinancialTrendPoint(BaseModel):
    date:  Optional[str]
    value: float


class FinancialAnalyticsOut(BaseModel):
    status:               str
    record_count:         int
    period_months:        int
    total_revenue:        float
    total_expenses:       float
    total_profit:         float
    avg_monthly_revenue:  float
    avg_monthly_expenses: float
    avg_monthly_profit:   float
    revenue_growth_pct:   Optional[float]
    expense_growth_pct:   Optional[float]
    profit_growth_pct:    Optional[float]
    revenue_trend:        str
    expense_trend:        str
    profit_trend:         str
    best_period:          Optional[str]
    worst_period:         Optional[str]
    revenue_series:       List[FinancialTrendPoint]
    expense_series:       List[FinancialTrendPoint]
    profit_series:        List[FinancialTrendPoint]
    disclaimer:           str


class GoalAnalyticsOut(BaseModel):
    total:          int
    completed:      int
    in_progress:    int
    not_started:    int
    overdue:        int
    completion_pct: float
    by_priority:    Dict[str, int]
    by_type:        Dict[str, int]


class DashboardAnalyticsOut(BaseModel):
    progress_score:      ProgressScoreOut
    financial_analytics: FinancialAnalyticsOut
    goal_analytics:      GoalAnalyticsOut
    financial_insights:  List[str]
    recent_activities:   List[Dict[str, Any]]
    disclaimer:          str = (
        "⚠️ Analytics are based on entrepreneur-entered data and platform activity only."
    )


# ── Action Items ──────────────────────────────────────────────────────────────

class ActionItemOut(BaseModel):
    id:               str
    user_id:          str
    title:            str
    description:      Optional[str]
    category:         str
    priority:         str
    impact:           str
    estimated_effort: Optional[str]
    related_phase:    Optional[str]
    action_url:       Optional[str]
    status:           str
    created_at:       datetime
    updated_at:       datetime
    model_config = {"from_attributes": True}


class ActionStatusUpdate(BaseModel):
    status: str = Field(..., description="pending | completed | dismissed")


class ActionPlanOut(BaseModel):
    actions:     List[Dict[str, Any]]
    generated:   bool   = True
    total:       int


# ── Activity Timeline ─────────────────────────────────────────────────────────

class ActivityOut(BaseModel):
    id:            str
    user_id:       str
    activity_type: str
    title:         str
    description:   Optional[str]
    reference_id:  Optional[str]
    created_at:    datetime
    model_config = {"from_attributes": True}


class TimelineOut(BaseModel):
    items:  List[ActivityOut]
    total:  int
