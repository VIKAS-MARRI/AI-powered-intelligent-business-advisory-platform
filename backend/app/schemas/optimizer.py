"""
Pydantic schemas for Phase 4 Investment Optimizer API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    """Request body for POST /optimizer/optimize (all three strategies)."""
    business_id:            str   = Field(..., description="Business ID from the catalogue")
    available_capital:      float = Field(..., gt=0,  description="User's investable capital (₹)")
    risk_preference:        str   = Field("balanced", description="conservative | balanced | growth")
    minimum_emergency_reserve: Optional[float] = Field(None, ge=0, description="Hard floor on emergency reserve (₹)")
    minimum_working_capital:   Optional[float] = Field(None, ge=0, description="Hard floor on working capital (₹)")
    maximum_marketing_budget:  Optional[float] = Field(None, ge=0, description="Cap on marketing spend (₹)")

    @field_validator("available_capital")
    @classmethod
    def capital_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("available_capital must be positive")
        return v

    @field_validator("risk_preference")
    @classmethod
    def valid_risk(cls, v: str) -> str:
        allowed = {"conservative", "balanced", "growth"}
        if v not in allowed:
            raise ValueError(f"risk_preference must be one of {allowed}")
        return v


class StrategyRequest(BaseModel):
    """Request body for POST /optimizer/strategy (single strategy)."""
    business_id:            str   = Field(..., description="Business ID from the catalogue")
    available_capital:      float = Field(..., gt=0)
    strategy:               str   = Field("balanced", description="conservative | balanced | growth")
    minimum_emergency_reserve: Optional[float] = Field(None, ge=0)
    minimum_working_capital:   Optional[float] = Field(None, ge=0)
    maximum_marketing_budget:  Optional[float] = Field(None, ge=0)

    @field_validator("available_capital")
    @classmethod
    def capital_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("available_capital must be positive")
        return v

    @field_validator("strategy")
    @classmethod
    def valid_strategy(cls, v: str) -> str:
        allowed = {"conservative", "balanced", "growth"}
        if v not in allowed:
            raise ValueError(f"strategy must be one of {allowed}")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class AllocationResultOut(BaseModel):
    name:           str
    allocated:      float
    minimum:        float
    recommended:    float
    maximum:        float
    pct_of_total:   float


class StrategyResultOut(BaseModel):
    name:               str
    label:              str
    total_allocated:    float
    remaining_capital:  float
    optimization_score: float
    risk_level:         str
    allocations:        List[AllocationResultOut]
    tradeoffs:          List[str]
    explanations:       List[str]
    allocation_dict:    Dict[str, float]


class InsufficientCapitalInfoOut(BaseModel):
    minimum_required_capital: float
    funding_gap:              float
    suggestions:              List[str]


class OptimizationResultOut(BaseModel):
    status:                   str
    recommended_strategy:     str
    available_capital:        float
    minimum_required_capital: float
    funding_gap:              float
    strategies:               List[StrategyResultOut]
    insufficient_info:        Optional[InsufficientCapitalInfoOut]
    disclaimer:               str
