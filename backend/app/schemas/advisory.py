"""
Pydantic schemas for Phase 7 Advisory API.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class AdvisoryQueryRequest(BaseModel):
    question:          str           = Field(..., min_length=3, max_length=1000,
                                             description="The user's business question")
    available_capital: Optional[float]   = Field(None, ge=0)
    business_id:       Optional[str]     = None
    latitude:          Optional[float]   = Field(None, ge=-90,  le=90)
    longitude:         Optional[float]   = Field(None, ge=-180, le=180)
    state_name:        Optional[str]     = None
    radius_km:         Optional[float]   = Field(5.0, ge=0.5, le=50)


class SchemeCompareIdsRequest(BaseModel):
    scheme_ids:           List[str]
    business_id:          Optional[str]   = None
    estimated_investment: Optional[float] = None
    available_capital:    Optional[float] = None
    state:                Optional[str]   = None


# ── Inner response models ─────────────────────────────────────────────────────

class FinalAdviceOut(BaseModel):
    summary:            str
    recommendation:     Optional[str]    = None
    financial_plan:     Optional[str]    = None
    market_insight:     Optional[str]    = None
    government_support: Optional[str]    = None
    risks:              List[str]        = []
    next_steps:         List[str]        = []
    ai_generated:       bool             = False
    data_source:        Optional[str]    = None
    disclaimer:         str              = ""
    ai_generated_text:  Optional[str]    = None


class AdvisoryResultOut(BaseModel):
    session_id:      str
    status:          str
    required_agents: List[str]
    ai_status:       str
    results: Dict[str, Any]   = {}
    final_advice:    FinalAdviceOut
    errors:          List[str] = []
    disclaimer:      str


class AIStatusOut(BaseModel):
    ai_available:       bool
    provider:           str
    model:              str
    fallback_available: bool
    status:             str


class AdvisoryHistoryItem(BaseModel):
    model_config = {"from_attributes": True}

    id:               str
    question:         str
    required_agents:  List[str]
    ai_status:        str
    status:           str
    created_at:       datetime
    summary:          Optional[str] = None


class AdvisoryHistoryOut(BaseModel):
    items: List[AdvisoryHistoryItem]
    total: int
