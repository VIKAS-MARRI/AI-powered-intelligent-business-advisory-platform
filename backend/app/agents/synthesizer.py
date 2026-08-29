"""
Synthesizer Agent — Phase 7.

Combines outputs from all specialist agents into a single, personalized
action plan. Gemini generates the narrative; all facts come from
deterministic agent results.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.prompts import DISCLAIMER, GROUNDING_INSTRUCTION, SYNTHESIZER_PROMPT, build_language_instruction
from app.agents.state import AgentState
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _fallback_advice(state: AgentState) -> Dict[str, Any]:
    """
    Generate structured deterministic advice when AI is unavailable.
    Uses raw agent results to produce sensible defaults.
    """
    biz_res    = state.get("business_result") or {}
    fin_res    = state.get("finance_result")  or {}
    market_res = state.get("market_result")   or {}
    scheme_res = state.get("scheme_result")   or {}

    top_biz    = biz_res.get("top_business", {}) or {}
    top_scheme = scheme_res.get("top_scheme",  {}) or {}

    biz_name = top_biz.get("name", "a suitable business")
    capital  = state.get("available_capital")
    gap      = fin_res.get("funding_gap", 0)

    summary = (
        f"Based on your profile, {biz_name} appears to be a good match for your situation."
        if top_biz else
        "Based on your inputs, here is the structured analysis from our system."
    )

    recommendation = (
        f"{biz_name} has been identified as the top recommendation "
        f"with a match score of {top_biz.get('score', 0):.0f}/100. "
        f"Investment required: ₹{top_biz.get('min_investment', 0):,.0f}–"
        f"₹{top_biz.get('max_investment', 0):,.0f}."
    ) if top_biz else "See business recommendations above."

    fin_plan = ""
    if capital:
        fin_plan = f"Your available capital is ₹{capital:,.0f}."
    if gap and gap > 0:
        fin_plan += f" Funding gap: ₹{gap:,.0f}. Explore government schemes to bridge this gap."
    elif fin_res.get("break_even_months"):
        fin_plan += f" Estimated break-even in {fin_res['break_even_months']:.1f} months."

    market_insight = ""
    if market_res.get("status") == "success":
        market_insight = (
            f"Competition level: {market_res.get('competition_level', 'N/A')}. "
            f"Market opportunity score: {market_res.get('market_opportunity_score', 'N/A')}/100."
        )
    elif market_res.get("status") == "skipped":
        market_insight = "Provide location coordinates for local market analysis."

    gov_support = ""
    if top_scheme:
        gov_support = (
            f"Top scheme match: {top_scheme.get('scheme_name', 'N/A')} "
            f"(Score: {top_scheme.get('score', 0):.0f}/100). "
            f"Eligibility: {top_scheme.get('eligibility_status', 'N/A')}. "
            f"Visit {top_scheme.get('official_url', 'official government portal')} for details."
        )

    risks = [
        "Business estimates are projections and may differ from actual results.",
        "Market conditions and competition can change.",
        "Government scheme eligibility must be verified through official sources.",
    ]

    next_steps = [
        "Visit the nearest Common Service Centre (CSC) or bank for scheme applications.",
        f"Research {biz_name} thoroughly in your local market.",
        "Speak to entrepreneurs already running similar businesses in your area.",
        "Create a detailed business plan before investing.",
        "Consult a qualified financial advisor for major investment decisions.",
    ]

    return {
        "summary":           summary,
        "recommendation":    recommendation,
        "financial_plan":    fin_plan     or "See financial analysis above.",
        "market_insight":    market_insight or "Location analysis not available.",
        "government_support": gov_support  or "See scheme matches above.",
        "risks":             risks,
        "next_steps":        next_steps,
        "ai_generated":      False,
        "data_source":       "Deterministic fallback (AI unavailable)",
    }


def _extract_structured_advice(ai_text: str) -> Dict[str, Any]:
    """Parse the structured AI output into individual fields."""
    import re
    sections = {
        "recommendation":    r"🎯 MY RECOMMENDATION\s*(.*?)(?=💰|\Z)",
        "financial_plan":    r"💰 FINANCIAL PLAN\s*(.*?)(?=📍|\Z)",
        "market_insight":    r"📍 LOCAL MARKET INSIGHT\s*(.*?)(?=🏛️|\Z)",
        "government_support": r"🏛️ POSSIBLE GOVERNMENT SUPPORT\s*(.*?)(?=⚠️|\Z)",
        "risks_raw":         r"⚠️ KEY RISKS\s*(.*?)(?=📋|\Z)",
        "steps_raw":         r"📋 YOUR NEXT STEPS\s*(.*?)(?=\Z)",
    }
    parsed: Dict[str, Any] = {"ai_generated": True, "ai_generated_text": ai_text}

    for key, pattern in sections.items():
        m = re.search(pattern, ai_text, re.DOTALL | re.IGNORECASE)
        if m:
            parsed[key] = m.group(1).strip()

    # Parse risks and steps as lists
    risks_raw = parsed.pop("risks_raw", "") or ""
    parsed["risks"] = [
        line.lstrip("•-*123456789. ").strip()
        for line in risks_raw.splitlines()
        if line.strip() and not line.strip().startswith("⚠️")
    ][:5]

    steps_raw = parsed.pop("steps_raw", "") or ""
    parsed["next_steps"] = [
        line.lstrip("•-*123456789. ").strip()
        for line in steps_raw.splitlines()
        if line.strip() and not line.strip().startswith("📋")
    ][:7]

    # Fallback summary
    parsed["summary"] = (
        parsed.get("recommendation", "")[:200] or "Personalized AI advisory generated."
    )

    return parsed


async def synthesizer_node(state: AgentState) -> AgentState:
    """Synthesizer: combines all specialist results into final advice."""
    errors: List[str] = list(state.get("errors", []))

    try:
        biz_res    = state.get("business_result") or {}
        fin_res    = state.get("finance_result")  or {}
        market_res = state.get("market_result")   or {}
        scheme_res = state.get("scheme_result")   or {}

        question  = state.get("question", "")
        capital   = state.get("available_capital")
        loc_parts = [state.get("state_name", "")]
        if state.get("latitude") and state.get("longitude"):
            loc_parts.append(f"Lat {state['latitude']:.4f}, Lon {state['longitude']:.4f}")
        location = ", ".join(p for p in loc_parts if p) or "Not specified"

        # Helper to extract AI explanation or fallback text from any result
        def _summary(res: Dict, fallback: str) -> str:
            exp = res.get("ai_explanation")
            if exp and exp.strip():
                return exp.strip()
            if res.get("status") == "skipped":
                return res.get("message", fallback)
            if res.get("status") == "error":
                return f"Analysis unavailable: {res.get('error', 'unknown error')}"
            return fallback

        biz_summary    = _summary(biz_res, "Business analysis not performed.")
        fin_summary    = _summary(fin_res, "Financial analysis not performed.")
        market_summary = _summary(market_res, "Market analysis not performed.")
        scheme_summary = _summary(scheme_res, "Scheme matching not performed.")

        # Try AI synthesis
        final_advice: Dict[str, Any] = {}

        # Phase 10 — build language/accessibility instruction
        lang            = state.get("language") or "en"
        simple_lang     = bool(state.get("simple_language", False))
        lang_instruction = build_language_instruction(lang, simple_lang)

        if ai_service.is_available():
            prompt = SYNTHESIZER_PROMPT.format(
                grounding         = GROUNDING_INSTRUCTION,
                question          = question,
                available_capital = f"₹{capital:,.0f}" if capital else "Not specified",
                location          = location,
                business_summary  = biz_summary[:800],
                finance_summary   = fin_summary[:600],
                market_summary    = market_summary[:600],
                scheme_summary    = scheme_summary[:600],
                language_instruction = lang_instruction,
            )
            ai_text = await ai_service.generate(prompt, temperature=0.4)
            if ai_text:
                final_advice = _extract_structured_advice(ai_text)
            else:
                final_advice = _fallback_advice(state)
        else:
            final_advice = _fallback_advice(state)

        final_advice["disclaimer"] = DISCLAIMER

    except Exception as exc:
        logger.exception("Synthesizer error: %s", exc)
        errors.append(f"Synthesizer error: {exc}")
        final_advice = _fallback_advice(state)
        final_advice["disclaimer"] = DISCLAIMER

    return {**state, "final_advice": final_advice, "errors": errors}
