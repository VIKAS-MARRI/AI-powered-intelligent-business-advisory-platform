"""
Investment Optimizer API endpoints — Phase 4.

POST /optimizer/optimize   — run all three strategies (conservative/balanced/growth)
POST /optimizer/strategy   — run a single named strategy

All endpoints require JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.optimizer import (
    OptimizeRequest,
    StrategyRequest,
    OptimizationResultOut,
    StrategyResultOut,
    AllocationResultOut,
    InsufficientCapitalInfoOut,
)
from app.services.investment_optimizer import (
    optimize_investment,
    optimize_single_strategy,
    OptimizationResult,
    StrategyResult,
)

router = APIRouter(prefix="/optimizer", tags=["Investment Optimizer"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_biz(business_id: str, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business '{business_id}' not found",
        )
    return biz


def _strategy_out(s: StrategyResult) -> StrategyResultOut:
    return StrategyResultOut(
        name               = s.name,
        label              = s.label,
        total_allocated    = s.total_allocated,
        remaining_capital  = s.remaining_capital,
        optimization_score = s.optimization_score,
        risk_level         = s.risk_level,
        allocations        = [
            AllocationResultOut(
                name         = a.name,
                allocated    = a.allocated,
                minimum      = a.minimum,
                recommended  = a.recommended,
                maximum      = a.maximum,
                pct_of_total = a.pct_of_total,
            )
            for a in s.allocations
        ],
        tradeoffs    = s.tradeoffs,
        explanations = s.explanations,
        allocation_dict = s.allocation_dict,
    )


def _result_out(r: OptimizationResult) -> OptimizationResultOut:
    insuf = None
    if r.insufficient_info:
        insuf = InsufficientCapitalInfoOut(
            minimum_required_capital = r.insufficient_info.minimum_required_capital,
            funding_gap              = r.insufficient_info.funding_gap,
            suggestions              = r.insufficient_info.suggestions,
        )
    return OptimizationResultOut(
        status                   = r.status,
        recommended_strategy     = r.recommended_strategy,
        available_capital        = r.available_capital,
        minimum_required_capital = r.minimum_required_capital,
        funding_gap              = r.funding_gap,
        strategies               = [_strategy_out(s) for s in r.strategies],
        insufficient_info        = insuf,
        disclaimer               = r.disclaimer,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/optimize",
    response_model=OptimizationResultOut,
    summary="Run all three investment strategies (Conservative / Balanced / Growth)",
)
async def optimize(
    body: OptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OptimizationResultOut:
    """
    Use Google OR-Tools to optimally allocate available capital across
    equipment, inventory, setup, licensing, marketing, working capital,
    and emergency reserve — for all three strategies in one call.

    All calculations are deterministic — no AI/LLM is involved.
    """
    biz = await _get_biz(body.business_id, db)
    result = optimize_investment(
        business_id           = biz.id,
        business_name         = biz.name,
        available_capital     = body.available_capital,
        min_investment        = biz.min_investment,
        max_investment        = biz.max_investment,
        risk_preference       = body.risk_preference,
        min_emergency_reserve = body.minimum_emergency_reserve,
        min_working_capital   = body.minimum_working_capital,
        max_marketing_budget  = body.maximum_marketing_budget,
    )
    return _result_out(result)


@router.post(
    "/strategy",
    response_model=OptimizationResultOut,
    summary="Run a single named investment strategy",
)
async def single_strategy(
    body: StrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OptimizationResultOut:
    """
    Optimise capital allocation for a single strategy (conservative, balanced,
    or growth). Returns the same response shape as /optimize but with only one
    strategy in the `strategies` list.
    """
    biz = await _get_biz(body.business_id, db)
    result = optimize_single_strategy(
        business_id           = biz.id,
        business_name         = biz.name,
        available_capital     = body.available_capital,
        min_investment        = biz.min_investment,
        max_investment        = biz.max_investment,
        strategy              = body.strategy,
        min_emergency_reserve = body.minimum_emergency_reserve,
        min_working_capital   = body.minimum_working_capital,
        max_marketing_budget  = body.maximum_marketing_budget,
    )
    return _result_out(result)
