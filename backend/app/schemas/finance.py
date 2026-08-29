"""
Pydantic schemas for Phase 3 Finance API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class FinancialAssumptions(BaseModel):
    """Optional user-overridable assumptions for the financial engine."""
    emergency_reserve_pct:    float = Field(0.125, ge=0, le=0.5,  description="Fraction of capital held as reserve (default 12.5%)")
    working_capital_pct:      float = Field(0.20,  ge=0, le=0.5,  description="Fraction of capital as working capital (default 20%)")
    monthly_revenue_growth:   float = Field(0.02,  ge=0, le=0.30, description="Monthly revenue growth rate (default 2%)")
    monthly_expense_growth:   float = Field(0.005, ge=0, le=0.20, description="Monthly expense growth rate (default 0.5%)")
    fixed_cost_ratio:         float = Field(0.55,  ge=0.1, le=0.9, description="Fraction of expenses that are fixed (default 55%)")
    variable_cost_ratio: Optional[float] = Field(None, ge=0.01, le=0.99, description="Variable cost ratio (auto-derived if not set)")


class AnalyzeRequest(BaseModel):
    business_id:       str
    available_capital: float = Field(..., gt=0, description="User's available investment capital in INR")
    assumptions:       FinancialAssumptions = Field(default_factory=FinancialAssumptions)

    @field_validator("available_capital")
    @classmethod
    def capital_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("available_capital must be positive")
        return v


class CashFlowRequest(BaseModel):
    business_id:              str
    initial_monthly_revenue:  float = Field(..., gt=0)
    initial_monthly_expenses: float = Field(..., gt=0)
    months:                   int   = Field(12, ge=1, le=60)
    monthly_revenue_growth:   float = Field(0.02, ge=0, le=0.30)
    monthly_expense_growth:   float = Field(0.005, ge=0, le=0.20)
    ramp_up_months:           int   = Field(2, ge=0, le=6)
    ramp_up_factor:           float = Field(0.70, ge=0.1, le=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class InvestmentAllocationOut(BaseModel):
    equipment:         float
    initial_inventory: float
    business_setup:    float
    licensing:         float
    marketing:         float
    working_capital:   float
    emergency_reserve: float
    total_allocated:   float
    available_capital: float
    funding_gap:       float
    is_feasible:       bool
    allocation_dict:   Dict[str, float]


class ScenarioOut(BaseModel):
    name:               str
    monthly_revenue:    float
    monthly_expenses:   float
    monthly_profit:     float
    annual_revenue:     float
    annual_profit:      float
    profit_margin_pct:  float


class BreakEvenOut(BaseModel):
    fixed_costs_monthly:       float
    variable_cost_ratio:       float
    contribution_margin_ratio: float
    break_even_revenue:        float
    assumed:                   bool


class CashFlowMonthOut(BaseModel):
    month:                int
    revenue:              float
    expenses:             float
    profit:               float
    cumulative_cash_flow: float


class HealthScoreOut(BaseModel):
    budget_sufficiency:       float
    profitability:            float
    roi_score:                float
    payback_score:            float
    emergency_reserve_score:  float
    expense_ratio_score:      float
    total:                    float
    status:                   str
    strengths:                List[str]
    risks:                    List[str]
    recommendations:          List[str]


class RiskIndicatorOut(BaseModel):
    name:        str
    level:       str
    explanation: str


class FullAnalysisOut(BaseModel):
    business_id:      str
    business_name:    str
    available_capital: float
    investment:       InvestmentAllocationOut
    conservative:     ScenarioOut
    expected:         ScenarioOut
    optimistic:       ScenarioOut
    roi_pct:          float
    payback_months:   Optional[float]
    payback_feasible: bool
    payback_note:     str
    break_even:       BreakEvenOut
    health:           HealthScoreOut
    risks:            List[RiskIndicatorOut]
    cash_flow:        List[CashFlowMonthOut]
    disclaimer:       str


class CashFlowOut(BaseModel):
    business_id: str
    months:      List[CashFlowMonthOut]
    disclaimer:  str = "Financial projections are estimates for planning purposes only."
