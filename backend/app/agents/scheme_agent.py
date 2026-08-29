"""
Government Scheme Agent — Phase 7.

Uses Phase 6 scheme matching engine for real verified scheme data.
Gemini only explains real matching results — never invents schemes, amounts, or URLs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.prompts import SCHEME_AGENT_PROMPT, GROUNDING_INSTRUCTION, build_language_instruction
from app.agents.state import AgentState
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _format_scheme_data(matches: List[Dict]) -> str:
    if not matches:
        return "No scheme matches available."
    lines = []
    for i, m in enumerate(matches[:3], 1):
        lines.append(
            f"{i}. {m['scheme_name']} (Match Score: {m['score']:.0f}/100)\n"
            f"   Category: {m['category']} | Eligibility: {m['eligibility_status']}\n"
            f"   Funding: {m['funding_relevance']} | {m['key_benefit']}\n"
            f"   Official: {m['official_url']}"
        )
    return "\n\n".join(lines)


async def scheme_agent_node(state: AgentState) -> AgentState:
    """Scheme agent: matches Phase 6 government schemes to the user's business profile."""
    if "scheme" not in state.get("required_agents", []):
        return state

    errors: List[str] = list(state.get("errors", []))
    result: Dict[str, Any] = {}

    try:
        from sqlalchemy import select
        from app.models.scheme import Scheme
        from app.services.scheme_matcher import MatchRequest, match_schemes, compute_funding_gap

        db          = state.get("_db")
        capital     = state.get("available_capital") or 0
        state_name  = state.get("state_name")
        question    = state.get("question", "")

        # Get business context from business_result
        biz_id   = state.get("business_id", "advisor-query")
        biz_name = "Business"
        biz_cat  = "General"
        biz_type = "Service"
        estimated_investment = capital or 150000

        if state.get("business_result") and (state["business_result"] or {}).get("top_business"):
            top = state["business_result"]["top_business"]
            biz_id   = top.get("id", biz_id)
            biz_name = top.get("name", biz_name)
            biz_cat  = top.get("category", biz_cat)
            estimated_investment = top.get("min_investment", estimated_investment)

        if state.get("finance_result") and (state["finance_result"] or {}).get("investment_required"):
            estimated_investment = state["finance_result"]["investment_required"]

        # Load schemes
        schemes: List[Scheme] = []
        if db:
            res = await db.execute(select(Scheme).where(Scheme.is_active == True))
            schemes = list(res.scalars().all())

        if not schemes:
            result = {"status": "error", "error": "No scheme data available", "matches": []}
            return {**state, "scheme_result": result, "errors": errors}

        req = MatchRequest(
            business_id          = biz_id,
            business_name        = biz_name,
            business_category    = biz_cat,
            business_type        = biz_type,
            estimated_investment = estimated_investment,
            available_capital    = capital,
            state                = state_name,
        )

        match_result = match_schemes(schemes, req, top_n=5)

        matches_out = [
            {
                "scheme_id":        m.scheme_id,
                "scheme_name":      m.scheme_name,
                "score":            m.score_breakdown.total,
                "category":         m.category,
                "funding_relevance": m.funding_relevance,
                "eligibility_status": m.eligibility.status,
                "key_benefit":      m.key_benefit,
                "official_url":     m.official_url,
                "match_reasons":    m.match_reasons,
                "data_status":      m.data_status,
                "tags":             m.tags,
            }
            for m in match_result.matches
        ]

        gap = match_result.funding_gap
        result = {
            "matches":             matches_out,
            "top_scheme":          matches_out[0] if matches_out else None,
            "funding_gap":         gap.funding_gap,
            "funding_gap_label":   gap.gap_label,
            "best_overall":        match_result.best_overall,
            "best_loan":           match_result.best_loan,
            "best_subsidy":        match_result.best_subsidy,
            "data_source":         "Phase 6 Scheme Matcher (verified scheme data)",
            "status":              "success",
        }

        # Optional AI explanation
        ai_explanation: Optional[str] = None
        if ai_service.is_available():
            lang_instruction = build_language_instruction(
                state.get("language") or "en",
                bool(state.get("simple_language", False)),
            )
            prompt = SCHEME_AGENT_PROMPT.format(
                grounding            = GROUNDING_INSTRUCTION,
                question             = question,
                business_name        = biz_name,
                available_capital    = f"₹{capital:,.0f}" if capital else "Not specified",
                funding_gap          = f"₹{gap.funding_gap:,.0f}" if gap.has_gap else "No gap",
                scheme_data          = _format_scheme_data(matches_out),
                language_instruction = lang_instruction,
            )
            ai_explanation = await ai_service.generate(prompt)

        result["ai_explanation"] = ai_explanation

    except Exception as exc:
        logger.exception("Scheme agent error: %s", exc)
        errors.append(f"Scheme agent error: {exc}")
        result = {"status": "error", "error": str(exc), "matches": []}

    return {**state, "scheme_result": result, "errors": errors}
