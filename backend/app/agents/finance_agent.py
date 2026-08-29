"""
Finance Advisor Agent — Phase 7.

Uses Phase 3 full_analysis() for real deterministic financial calculations.
Gemini only narrates the computed numbers — never invents figures.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.prompts import FINANCE_AGENT_PROMPT, GROUNDING_INSTRUCTION, build_language_instruction
from app.agents.state import AgentState
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _format_finance_data(fd: Dict) -> str:
    lines = []
    if fd.get("investment_required"):
        lines.append(f"Investment Required: ₹{fd['investment_required']:,.0f}")
    if fd.get("available_capital"):
        lines.append(f"Available Capital: ₹{fd['available_capital']:,.0f}")
    if fd.get("funding_gap") is not None:
        lines.append(f"Funding Gap: ₹{fd['funding_gap']:,.0f}")
    if fd.get("monthly_revenue"):
        lines.append(f"Est. Monthly Revenue: ₹{fd['monthly_revenue']:,.0f}")
    if fd.get("monthly_profit"):
        lines.append(f"Est. Monthly Profit: ₹{fd['monthly_profit']:,.0f}")
    if fd.get("break_even_months"):
        lines.append(f"Break-Even Period: {fd['break_even_months']:.1f} months")
    if fd.get("annual_roi_pct"):
        lines.append(f"Annual ROI: {fd['annual_roi_pct']:.1f}%")
    return "\n".join(lines) if lines else "No financial data available."


async def finance_agent_node(state: AgentState) -> AgentState:
    """Finance agent: uses Phase 3 full_analysis for real financial calculations."""
    if "finance" not in state.get("required_agents", []):
        return state

    errors: List[str] = list(state.get("errors", []))
    result: Dict[str, Any] = {}

    try:
        from app.services.financial_calculator import full_analysis
        from sqlalchemy import select
        from app.models.business import Business

        capital     = state.get("available_capital") or 0
        business_id = state.get("business_id")
        question    = state.get("question", "")
        db          = state.get("_db")

        biz: Optional[Business] = None
        if db and business_id:
            res = await db.execute(select(Business).where(Business.id == business_id))
            biz = res.scalar_one_or_none()

        # Get business context from business_result
        biz_name = "Business"
        if biz:
            min_inv   = biz.min_investment
            max_inv   = biz.max_investment
            rev_min   = biz.estimated_monthly_revenue_min
            rev_max   = biz.estimated_monthly_revenue_max
            exp_min   = getattr(biz, 'estimated_monthly_expenses_min', rev_min * 0.6)
            exp_max   = getattr(biz, 'estimated_monthly_expenses_max', rev_max * 0.65)
            biz_id    = biz.id
            biz_name  = biz.name
        elif state.get("business_result") and (state["business_result"] or {}).get("top_business"):
            top      = state["business_result"]["top_business"]
            biz_id   = top.get("id", "advisor")
            biz_name = top.get("name", "Business")
            min_inv  = top.get("min_investment", 100000)
            max_inv  = top.get("max_investment", 200000)
            rev      = top.get("monthly_revenue", 15000)
            rev_min  = rev * 0.8
            rev_max  = rev * 1.2
            exp_min  = rev_min * 0.6
            exp_max  = rev_max * 0.65
        else:
            biz_id  = "advisor"
            min_inv = capital or 100000
            max_inv = min_inv * 1.5
            rev_min = min_inv * 0.12
            rev_max = min_inv * 0.18
            exp_min = rev_min * 0.6
            exp_max = rev_max * 0.65

        fa = full_analysis(
            business_id   = biz_id,
            business_name = biz_name,
            available_capital = capital,
            min_investment = min_inv,
            max_investment = max_inv,
            revenue_min    = rev_min,
            revenue_max    = rev_max,
            expense_min    = exp_min,
            expense_max    = exp_max,
        )

        # Extract key metrics from FullFinancialAnalysis dataclass
        be = fa.break_even
        roi = fa.roi_analysis
        plan = fa.investment_plan

        funding_gap = max(0.0, min_inv - capital)

        fd = {
            "business_name":       biz_name,
            "investment_required": min_inv,
            "available_capital":   capital,
            "funding_gap":         funding_gap,
            "monthly_revenue":     (rev_min + rev_max) / 2,
            "monthly_profit":      getattr(be, "monthly_net_profit", None),
            "break_even_months":   getattr(be, "break_even_months", None),
            "annual_roi_pct":      getattr(roi, "annual_roi_pct", None),
            "data_source":         "Phase 3 Financial Calculator (deterministic)",
        }
        result.update(fd)
        result["status"] = "success"

        # Optional AI explanation
        ai_explanation: Optional[str] = None
        if ai_service.is_available():
            lang_instruction = build_language_instruction(
                state.get("language") or "en",
                bool(state.get("simple_language", False)),
            )
            prompt = FINANCE_AGENT_PROMPT.format(
                grounding            = GROUNDING_INSTRUCTION,
                question             = question,
                available_capital    = f"₹{capital:,.0f}" if capital else "Not specified",
                business_name        = biz_name,
                finance_data         = _format_finance_data(fd),
                language_instruction = lang_instruction,
            )
            ai_explanation = await ai_service.generate(prompt)

        result["ai_explanation"] = ai_explanation

    except Exception as exc:
        logger.exception("Finance agent error: %s", exc)
        errors.append(f"Finance agent error: {exc}")
        result = {"status": "error", "error": str(exc)}

    return {**state, "finance_result": result, "errors": errors}
