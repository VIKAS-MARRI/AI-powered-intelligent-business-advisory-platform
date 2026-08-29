"""
Supervisor / Router Agent — Phase 7.

Determines which specialist agents are needed for a given question.
Uses two strategies (tried in order):
  1. Gemini structured JSON routing (if AI available)
  2. Deterministic keyword fallback (always works, no AI needed)
"""
from __future__ import annotations

import re
from typing import List

from app.agents.prompts import GROUNDING_INSTRUCTION, SUPERVISOR_PROMPT
from app.agents.state import AgentState
from app.services.ai_service import ai_service

# ── Keyword fallback routing ──────────────────────────────────────────────────

_KEYWORD_MAP: dict[str, List[str]] = {
    "business": [
        "business", "start", "idea", "what to do", "which business", "venture",
        "enterprise", "shop", "work", "earn", "income", "livelihood", "occupation",
        "retail", "tailoring", "dairy", "bakery", "kirana", "farming",
    ],
    "finance": [
        "invest", "capital", "money", "fund", "loan", "profit", "roi", "return",
        "revenue", "income", "break-even", "breakeven", "cash", "cost",
        "expense", "budget", "afford", "pay", "₹", "lakh", "rupee",
        "financial", "finance", "feasib",
    ],
    "market": [
        "area", "location", "local", "market", "competition", "competitor",
        "village", "town", "district", "nearby", "neighbourhood", "map",
        "place", "region", "demand", "customer", "suitable", "near me",
    ],
    "scheme": [
        "scheme", "government", "subsidy", "grant", "mudra", "pmegp",
        "stand-up", "standup", "nabard", "nrlm", "support", "help",
        "assistance", "fund", "loan", "financial support", "eligib",
        "apply", "application", "program", "programme", "benefit",
    ],
}

_ALWAYS_INCLUDE_MIN = {"business"}   # always include at least business agent


def _keyword_route(question: str) -> List[str]:
    """Deterministic keyword-based routing. Always returns at least ['business']."""
    q = question.lower()
    selected: set[str] = set()

    for agent, keywords in _KEYWORD_MAP.items():
        if any(kw in q for kw in keywords):
            selected.add(agent)

    # Ensure minimum coverage
    if not selected:
        selected = {"business", "finance"}
    else:
        selected.update(_ALWAYS_INCLUDE_MIN)

    # If capital/money mentioned with location → include market too
    if "finance" in selected and any(kw in q for kw in ["area", "location", "local", "village", "town"]):
        selected.add("market")

    # Cap at 4 agents
    priority = ["business", "finance", "market", "scheme"]
    return [a for a in priority if a in selected]


# ── AI routing ────────────────────────────────────────────────────────────────

async def _ai_route(question: str) -> List[str] | None:
    """Try Gemini-based routing. Returns None if AI unavailable or fails."""
    if not ai_service.is_available():
        return None

    prompt = SUPERVISOR_PROMPT.format(question=question)
    result = await ai_service.generate_json(prompt)

    if not result or "agents" not in result:
        return None

    valid_agents = {"business", "finance", "market", "scheme"}
    agents = [a for a in result["agents"] if a in valid_agents]
    return agents if agents else None


# ── LangGraph node ────────────────────────────────────────────────────────────

async def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node: determines required_agents from the user's question.
    Falls back to keyword routing if AI is unavailable.
    """
    question = state.get("question", "")
    errors: List[str] = list(state.get("errors", []))

    # Try AI routing first
    try:
        agents = await _ai_route(question)
    except Exception as exc:
        agents = None
        errors.append(f"Supervisor AI routing error: {exc}")

    # Fall back to keyword routing
    if not agents:
        agents = _keyword_route(question)

    return {
        **state,
        "required_agents": agents,
        "ai_status":        ai_service.status,
        "errors":           errors,
    }
