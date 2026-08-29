"""
Business Advisor Agent — Phase 7.

Uses Phase 2 deterministic recommendation engine for data.
Gemini only summarizes/explains real results — never invents data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.prompts import BUSINESS_AGENT_PROMPT, GROUNDING_INSTRUCTION, build_language_instruction
from app.agents.state import AgentState
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _format_business_data(recs: List[Dict]) -> str:
    if not recs:
        return "No specific recommendations available."
    lines = []
    for i, r in enumerate(recs[:3], 1):
        lines.append(
            f"{i}. {r['name']} (Score: {r['score']:.0f}/100)\n"
            f"   Category: {r['category']} | "
            f"Investment: ₹{r['min_investment']:,.0f}–₹{r['max_investment']:,.0f}\n"
            f"   Est. Monthly Revenue: ₹{r['monthly_revenue']:,.0f} | Risk: {r['risk_level']}\n"
            f"   Reasons: {'; '.join(r['reasons'][:2])}"
        )
    return "\n\n".join(lines)


async def business_agent_node(state: AgentState) -> AgentState:
    """Business agent: fetches Phase 2 recommendations, optionally generates AI explanation."""
    if "business" not in state.get("required_agents", []):
        return state

    errors: List[str] = list(state.get("errors", []))
    result: Dict[str, Any] = {}

    try:
        from sqlalchemy import select
        from app.models.business import Business
        from app.services.recommendation_engine import score_business, generate_reasons

        capital      = state.get("available_capital")
        state_name   = state.get("state_name", "")
        question     = state.get("question", "")

        # Use the db session stored in state (injected by graph)
        db = state.get("_db")
        businesses: List[Business] = []
        if db:
            res = await db.execute(select(Business).where(Business.is_active == True))
            businesses = list(res.scalars().all())

        if not businesses:
            result = {"status": "error", "error": "No business data available", "recommendations": []}
            return {**state, "business_result": result, "errors": errors}

        # Score all businesses
        scored = []
        for biz in businesses:
            scores = score_business(
                biz       = biz,
                capital   = capital,
                skills    = question,    # use question keywords as interest proxy
                interests = question,
                income_goal  = None,
                preferred_risk = "any",
            )
            reasons = generate_reasons(scores, biz, capital)
            scored.append({
                "id":             biz.id,
                "name":           biz.name,
                "category":       biz.category,
                "score":          scores["final"],
                "min_investment": biz.min_investment,
                "max_investment": biz.max_investment,
                "monthly_revenue": (biz.estimated_monthly_revenue_min + biz.estimated_monthly_revenue_max) / 2,
                "risk_level":     biz.risk_level,
                "reasons":        reasons,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = scored[:5]

        result["recommendations"] = top5
        result["top_business"]    = top5[0] if top5 else None
        result["data_source"]     = "Phase 2 Recommendation Engine (deterministic)"
        result["status"]          = "success"

        # Optional AI explanation
        ai_explanation: Optional[str] = None
        if ai_service.is_available():
            lang_instruction = build_language_instruction(
                state.get("language") or "en",
                bool(state.get("simple_language", False)),
            )
            prompt = BUSINESS_AGENT_PROMPT.format(
                grounding            = GROUNDING_INSTRUCTION,
                question             = question,
                available_capital    = f"₹{capital:,.0f}" if capital else "Not specified",
                state_name           = state_name or "Not specified",
                business_data        = _format_business_data(top5),
                language_instruction = lang_instruction,
            )
            ai_explanation = await ai_service.generate(prompt)

        result["ai_explanation"] = ai_explanation

    except Exception as exc:
        logger.exception("Business agent error: %s", exc)
        errors.append(f"Business agent error: {exc}")
        result = {"status": "error", "error": str(exc), "recommendations": []}

    return {**state, "business_result": result, "errors": errors}
