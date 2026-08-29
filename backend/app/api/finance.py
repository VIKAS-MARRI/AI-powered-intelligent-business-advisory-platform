"""
Finance API endpoints — Phase 3.

POST /finance/analyze              — full financial analysis for a business
POST /finance/cash-flow            — 12-month cash flow projection
GET  /finance/business/{id}        — quick analysis using user profile capital
"""
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.finance import (
    AnalyzeRequest,
    CashFlowRequest,
    FullAnalysisOut,
    CashFlowOut,
    InvestmentAllocationOut,
    ScenarioOut,
    BreakEvenOut,
    CashFlowMonthOut,
    HealthScoreOut,
    RiskIndicatorOut,
)
from app.services.financial_calculator import (
    full_analysis,
    project_cash_flow,
    InvestmentAllocation,
    ScenarioResult,
    BreakEvenResult,
    CashFlowMonth,
    HealthScoreBreakdown,
    RiskIndicator,
)

router = APIRouter(prefix="/finance", tags=["Finance"])


# ── Conversion helpers ────────────────────────────────────────────────────────

def _inv_out(inv: InvestmentAllocation) -> InvestmentAllocationOut:
    return InvestmentAllocationOut(
        equipment=inv.equipment,
        initial_inventory=inv.initial_inventory,
        business_setup=inv.business_setup,
        licensing=inv.licensing,
        marketing=inv.marketing,
        working_capital=inv.working_capital,
        emergency_reserve=inv.emergency_reserve,
        total_allocated=inv.total_allocated,
        available_capital=inv.available_capital,
        funding_gap=inv.funding_gap,
        is_feasible=inv.is_feasible,
        allocation_dict=inv.allocation_dict,
    )

def _scenario_out(s: ScenarioResult) -> ScenarioOut:
    return ScenarioOut(
        name=s.name,
        monthly_revenue=s.monthly_revenue,
        monthly_expenses=s.monthly_expenses,
        monthly_profit=s.monthly_profit,
        annual_revenue=s.annual_revenue,
        annual_profit=s.annual_profit,
        profit_margin_pct=s.profit_margin_pct,
    )

def _be_out(be: BreakEvenResult) -> BreakEvenOut:
    return BreakEvenOut(
        fixed_costs_monthly=be.fixed_costs_monthly,
        variable_cost_ratio=be.variable_cost_ratio,
        contribution_margin_ratio=be.contribution_margin_ratio,
        break_even_revenue=be.break_even_revenue,
        assumed=be.assumed,
    )

def _cfm_out(m: CashFlowMonth) -> CashFlowMonthOut:
    return CashFlowMonthOut(
        month=m.month,
        revenue=m.revenue,
        expenses=m.expenses,
        profit=m.profit,
        cumulative_cash_flow=m.cumulative_cash_flow,
    )

def _health_out(h: HealthScoreBreakdown) -> HealthScoreOut:
    return HealthScoreOut(
        budget_sufficiency=h.budget_sufficiency,
        profitability=h.profitability,
        roi_score=h.roi_score,
        payback_score=h.payback_score,
        emergency_reserve_score=h.emergency_reserve_score,
        expense_ratio_score=h.expense_ratio_score,
        total=h.total,
        status=h.status,
        strengths=h.strengths,
        risks=h.risks,
        recommendations=h.recommendations,
    )

def _risk_out(r: RiskIndicator) -> RiskIndicatorOut:
    return RiskIndicatorOut(name=r.name, level=r.level, explanation=r.explanation)


# ── Shared: fetch business from DB ────────────────────────────────────────────

async def _get_biz(business_id: str, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business '{business_id}' not found")
    return biz


# ── Shared: build FullAnalysisOut from calculator ────────────────────────────

def _build_analysis(biz: Business, capital: float, req_assumptions) -> FullAnalysisOut:
    a = req_assumptions
    result = full_analysis(
        business_id=biz.id,
        business_name=biz.name,
        available_capital=capital,
        min_investment=biz.min_investment,
        max_investment=biz.max_investment,
        revenue_min=biz.estimated_monthly_revenue_min,
        revenue_max=biz.estimated_monthly_revenue_max,
        expense_min=biz.estimated_monthly_expenses_min,
        expense_max=biz.estimated_monthly_expenses_max,
        emergency_reserve_pct=a.emergency_reserve_pct,
        working_capital_pct=a.working_capital_pct,
        monthly_revenue_growth=a.monthly_revenue_growth,
        monthly_expense_growth=a.monthly_expense_growth,
        fixed_cost_ratio=a.fixed_cost_ratio,
        variable_cost_ratio=a.variable_cost_ratio,
    )
    return FullAnalysisOut(
        business_id=result.business_id,
        business_name=result.business_name,
        available_capital=result.available_capital,
        investment=_inv_out(result.investment),
        conservative=_scenario_out(result.conservative),
        expected=_scenario_out(result.expected),
        optimistic=_scenario_out(result.optimistic),
        roi_pct=result.roi_pct,
        payback_months=result.payback_months,
        payback_feasible=result.payback_feasible,
        payback_note=result.payback_note,
        break_even=_be_out(result.break_even),
        health=_health_out(result.health),
        risks=[_risk_out(r) for r in result.risks],
        cash_flow=[_cfm_out(m) for m in result.cash_flow],
        disclaimer=result.disclaimer,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=FullAnalysisOut,
    summary="Full financial analysis for a business",
)
async def analyze(
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FullAnalysisOut:
    """
    Run the complete financial planning engine for the given business and capital.
    All calculations are deterministic — no AI/LLM involved.
    """
    biz = await _get_biz(body.business_id, db)
    return _build_analysis(biz, body.available_capital, body.assumptions)


@router.post(
    "/cash-flow",
    response_model=CashFlowOut,
    summary="12-month (or custom) cash flow projection",
)
async def cash_flow(
    body: CashFlowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CashFlowOut:
    """Generate a month-by-month cash flow projection."""
    # Validate business exists
    await _get_biz(body.business_id, db)

    months = project_cash_flow(
        initial_monthly_revenue=body.initial_monthly_revenue,
        initial_monthly_expenses=body.initial_monthly_expenses,
        months=body.months,
        monthly_revenue_growth_rate=body.monthly_revenue_growth,
        monthly_expense_growth_rate=body.monthly_expense_growth,
        ramp_up_months=body.ramp_up_months,
        ramp_up_factor=body.ramp_up_factor,
    )
    return CashFlowOut(
        business_id=body.business_id,
        months=[_cfm_out(m) for m in months],
    )


@router.get(
    "/business/{business_id}",
    response_model=FullAnalysisOut,
    summary="Quick financial analysis using user profile capital",
)
async def quick_analysis(
    business_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FullAnalysisOut:
    """
    Generate a financial analysis using the authenticated user's available_capital.
    Requires the user to have set available_capital in their profile.
    """
    capital = current_user.available_capital
    if not capital or capital <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please set your available capital in your profile first.",
        )
    biz = await _get_biz(business_id, db)

    from app.schemas.finance import FinancialAssumptions
    return _build_analysis(biz, capital, FinancialAssumptions())
