"""
Shared LangGraph state for the Phase 7 Multi-Agent Advisory System.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between all agents in the LangGraph workflow."""

    # ── Input ─────────────────────────────────────────────────────────────────
    user_id:             str
    question:            str
    available_capital:   Optional[float]
    business_id:         Optional[str]
    latitude:            Optional[float]
    longitude:           Optional[float]
    state_name:          Optional[str]      # user's state for scheme matching
    radius_km:           Optional[float]    # for market analysis

    # ── Routing ───────────────────────────────────────────────────────────────
    required_agents:     List[str]          # e.g. ["business", "finance", "market", "scheme"]

    # ── Specialist results ────────────────────────────────────────────────────
    business_result:     Optional[Dict[str, Any]]
    finance_result:      Optional[Dict[str, Any]]
    market_result:       Optional[Dict[str, Any]]
    scheme_result:       Optional[Dict[str, Any]]

    # ── Final synthesis ───────────────────────────────────────────────────────
    final_advice:        Optional[Dict[str, Any]]

    # ── Metadata ──────────────────────────────────────────────────────────────
    ai_status:           str               # "available" | "limited" | "unavailable"
    errors:              List[str]

    # ── Phase 10 ───────────────────────────────────────────────
    language:            Optional[str]     # target response language (en|hi|te)
    simple_language:     Optional[bool]    # whether to use simple language mode
