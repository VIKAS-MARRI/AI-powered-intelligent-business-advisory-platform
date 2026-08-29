"""
Phase 9 API routes — Goals, Financial Progress, Analytics, Actions, Timeline.
All endpoints are JWT-protected. Users only access their own data.

Routers:
  goals_router    → /goals
  progress_router → /progress/financial
  analytics_router → /analytics
  actions_router  → /actions
  activity_router → /activity
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.db import get_db
from app.models.action_item import ActionItem
from app.models.activity import ActivityLog
from app.models.financial_progress import FinancialProgressRecord
from app.models.goal import BusinessGoal
from app.models.phase8 import RecommendationInteraction, SavedBusiness
from app.models.advisory import AdvisorySession
from app.models.user import User
from app.schemas.phase9 import (
    ActionItemOut, ActionPlanOut, ActionStatusUpdate,
    ActivityOut, DashboardAnalyticsOut, FinancialAnalyticsOut,
    FinancialRecordCreate, FinancialRecordListOut,
    FinancialRecordOut, FinancialRecordUpdate, FinancialTrendPoint,
    GoalAnalyticsOut, GoalCreate, GoalListOut, GoalOut,
    GoalProgressUpdate, GoalUpdate, ProgressScoreOut, TimelineOut,
)
from app.services.analytics_engine import (
    compute_financial_analytics, compute_financial_insights,
    compute_goal_analytics, compute_progress_score,
)
from app.services.action_plan_engine import generate_action_plan
from app.services.recommendation_engine import profile_completeness

logger = logging.getLogger(__name__)

# ── Routers ───────────────────────────────────────────────────────────────────
goals_router    = APIRouter(prefix="/goals",             tags=["Phase 9 — Goals"])
progress_router = APIRouter(prefix="/progress",          tags=["Phase 9 — Financial Progress"])
analytics_router = APIRouter(prefix="/analytics",        tags=["Phase 9 — Analytics"])
actions_router  = APIRouter(prefix="/actions",           tags=["Phase 9 — Action Plan"])
activity_router = APIRouter(prefix="/activity",          tags=["Phase 9 — Timeline"])

VALID_STATUSES       = {"pending", "completed", "dismissed"}
VALID_GOAL_STATUSES  = {"not_started", "in_progress", "completed", "overdue"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow():
    return datetime.now(timezone.utc)


async def _log_activity(
    db: AsyncSession,
    user_id: str,
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> None:
    log = ActivityLog(
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        description=description,
        reference_id=reference_id,
    )
    db.add(log)
    # commit handled by caller


def _goal_to_out(g: BusinessGoal) -> GoalOut:
    return GoalOut(
        id=g.id, user_id=g.user_id, title=g.title,
        description=g.description, goal_type=g.goal_type,
        status=g.status, priority=g.priority,
        target_value=g.target_value, current_value=g.current_value,
        unit=g.unit, start_date=g.start_date, target_date=g.target_date,
        progress_percentage=g.progress_percentage,
        days_remaining=g.days_remaining,
        is_overdue=g.is_overdue,
        created_at=g.created_at, updated_at=g.updated_at,
    )


def _record_to_out(r: FinancialProgressRecord) -> FinancialRecordOut:
    return FinancialRecordOut(
        id=r.id, user_id=r.user_id, business_id=r.business_id,
        record_date=r.record_date, revenue=r.revenue, expenses=r.expenses,
        profit=r.profit, customers=r.customers, investment=r.investment,
        savings=r.savings, inventory_cost=r.inventory_cost,
        notes=r.notes, created_at=r.created_at, updated_at=r.updated_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
# GOALS
# ══════════════════════════════════════════════════════════════════════════════

@goals_router.post("", response_model=GoalOut, status_code=201, summary="Create a business goal")
async def create_goal(
    body: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> GoalOut:
    goal = BusinessGoal(
        user_id=current_user.id,
        **body.model_dump(exclude_none=True),
    )
    # Auto-set in_progress if current_value > 0
    if goal.current_value and goal.current_value > 0:
        goal.status = "in_progress"
    db.add(goal)
    await _log_activity(db, current_user.id, "goal_created", f"Goal created: {goal.title}", reference_id=goal.id)
    await db.commit()
    await db.refresh(goal)
    return _goal_to_out(goal)


@goals_router.get("", response_model=GoalListOut, summary="List all goals")
async def list_goals(
    status_filter:   Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> GoalListOut:
    q = select(BusinessGoal).where(BusinessGoal.user_id == current_user.id)
    if status_filter:
        q = q.where(BusinessGoal.status == status_filter)
    if priority_filter:
        q = q.where(BusinessGoal.priority == priority_filter)
    q = q.order_by(desc(BusinessGoal.created_at))
    result = await db.execute(q)
    goals = list(result.scalars().all())

    # Auto-update overdue status
    updated = False
    for g in goals:
        if g.is_overdue and g.status not in ("completed", "overdue"):
            g.status = "overdue"
            updated = True
    if updated:
        await db.commit()

    return GoalListOut(items=[_goal_to_out(g) for g in goals], total=len(goals))


@goals_router.get("/{goal_id}", response_model=GoalOut, summary="Get a specific goal")
async def get_goal(
    goal_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> GoalOut:
    result = await db.execute(
        select(BusinessGoal).where(
            and_(BusinessGoal.id == goal_id, BusinessGoal.user_id == current_user.id)
        )
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    return _goal_to_out(goal)


@goals_router.patch("/{goal_id}", response_model=GoalOut, summary="Update a goal")
async def update_goal(
    body: GoalUpdate,
    goal_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> GoalOut:
    result = await db.execute(
        select(BusinessGoal).where(
            and_(BusinessGoal.id == goal_id, BusinessGoal.user_id == current_user.id)
        )
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(goal, field, value)
    await db.commit()
    await db.refresh(goal)
    return _goal_to_out(goal)


@goals_router.delete("/{goal_id}", status_code=204, response_model=None, summary="Delete a goal")
async def delete_goal(
    goal_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(BusinessGoal).where(
            and_(BusinessGoal.id == goal_id, BusinessGoal.user_id == current_user.id)
        )
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Goal not found")


@goals_router.post("/{goal_id}/progress", response_model=GoalOut, summary="Update goal progress")
async def update_goal_progress(
    body: GoalProgressUpdate,
    goal_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> GoalOut:
    result = await db.execute(
        select(BusinessGoal).where(
            and_(BusinessGoal.id == goal_id, BusinessGoal.user_id == current_user.id)
        )
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(404, "Goal not found")

    goal.current_value = body.current_value
    # Auto-update status
    if goal.target_value and goal.current_value >= goal.target_value:
        goal.status = "completed"
        await _log_activity(db, current_user.id, "goal_completed",
                            f"Goal completed: {goal.title}", reference_id=goal.id)
    elif goal.current_value > 0:
        goal.status = "in_progress"
        await _log_activity(db, current_user.id, "goal_updated",
                            f"Goal progress updated: {goal.title}", reference_id=goal.id)

    await db.commit()
    await db.refresh(goal)
    return _goal_to_out(goal)


# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL PROGRESS
# ══════════════════════════════════════════════════════════════════════════════

@progress_router.post("/financial", response_model=FinancialRecordOut, status_code=201,
                      summary="Add a financial progress record")
async def add_financial_record(
    body: FinancialRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
) -> FinancialRecordOut:
    data = body.model_dump(exclude_none=True)
    # Compute profit safely
    rev  = data.get("revenue",  0) or 0
    exp  = data.get("expenses", 0) or 0
    data["profit"] = round(rev - exp, 2)

    record = FinancialProgressRecord(user_id=current_user.id, **data)
    db.add(record)
    await _log_activity(db, current_user.id, "financial_record_added",
                        f"Financial record added for {body.record_date}",
                        reference_id=record.id)
    await db.commit()
    await db.refresh(record)
    return _record_to_out(record)


@progress_router.get("/financial", response_model=FinancialRecordListOut,
                     summary="List financial progress records")
async def list_financial_records(
    from_date:    Optional[date] = Query(None),
    to_date:      Optional[date] = Query(None),
    limit:        int            = Query(24, ge=1, le=100),
    offset:       int            = Query(0, ge=0),
    current_user: User           = Depends(get_current_user),
    db:           AsyncSession   = Depends(get_db),
) -> FinancialRecordListOut:
    q = select(FinancialProgressRecord).where(
        FinancialProgressRecord.user_id == current_user.id
    )
    if from_date:
        q = q.where(FinancialProgressRecord.record_date >= from_date)
    if to_date:
        q = q.where(FinancialProgressRecord.record_date <= to_date)
    q = q.order_by(desc(FinancialProgressRecord.record_date)).offset(offset).limit(limit)

    result = await db.execute(q)
    records = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(FinancialProgressRecord).where(
            FinancialProgressRecord.user_id == current_user.id
        )
    )
    total = count_result.scalar() or 0

    return FinancialRecordListOut(items=[_record_to_out(r) for r in records], total=total)


@progress_router.patch("/financial/{record_id}", response_model=FinancialRecordOut,
                       summary="Update a financial record")
async def update_financial_record(
    body:      FinancialRecordUpdate,
    record_id: str         = Path(...),
    current_user: User     = Depends(get_current_user),
    db: AsyncSession       = Depends(get_db),
) -> FinancialRecordOut:
    result = await db.execute(
        select(FinancialProgressRecord).where(
            and_(FinancialProgressRecord.id == record_id,
                 FinancialProgressRecord.user_id == current_user.id)
        )
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "Record not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    # Recompute profit
    rev = record.revenue or 0
    exp = record.expenses or 0
    record.profit = round(rev - exp, 2)
    await db.commit()
    await db.refresh(record)
    return _record_to_out(record)


@progress_router.delete("/financial/{record_id}", status_code=204, response_model=None,
                        summary="Delete a financial record")
async def delete_financial_record(
    record_id:    str        = Path(...),
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(FinancialProgressRecord).where(
            and_(FinancialProgressRecord.id == record_id,
                 FinancialProgressRecord.user_id == current_user.id)
        )
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Record not found")


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

async def _load_analytics_data(db: AsyncSession, user_id: str):
    """Load all data needed for analytics in one function."""
    rec_result = await db.execute(
        select(FinancialProgressRecord)
        .where(FinancialProgressRecord.user_id == user_id)
        .order_by(FinancialProgressRecord.record_date)
    )
    records = list(rec_result.scalars().all())

    goal_result = await db.execute(
        select(BusinessGoal).where(BusinessGoal.user_id == user_id)
    )
    goals = list(goal_result.scalars().all())

    act_result = await db.execute(
        select(func.count()).select_from(ActivityLog).where(ActivityLog.user_id == user_id)
    )
    activity_count = act_result.scalar() or 0

    inter_result = await db.execute(
        select(func.count()).select_from(RecommendationInteraction)
        .where(RecommendationInteraction.user_id == user_id)
    )
    interactions_count = inter_result.scalar() or 0

    saved_result = await db.execute(
        select(SavedBusiness).where(SavedBusiness.user_id == user_id)
    )
    saved = list(saved_result.scalars().all())

    adv_result = await db.execute(
        select(AdvisorySession).where(AdvisorySession.user_id == user_id)
        .order_by(desc(AdvisorySession.created_at)).limit(5)
    )
    advisory = list(adv_result.scalars().all())

    return records, goals, activity_count, interactions_count, saved, advisory


@analytics_router.get("/dashboard", response_model=DashboardAnalyticsOut,
                      summary="Full analytics dashboard data")
async def analytics_dashboard(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> DashboardAnalyticsOut:
    records, goals, act_count, inter_count, saved, advisory = await _load_analytics_data(
        db, current_user.id
    )

    records_dicts = [
        {"record_date": r.record_date, "revenue": r.revenue,
         "expenses": r.expenses, "profit": r.profit}
        for r in records
    ]
    goals_dicts = [
        {"status": g.status, "priority": g.priority, "goal_type": g.goal_type,
         "is_overdue": g.is_overdue, "progress_percentage": g.progress_percentage}
        for g in goals
    ]
    # Debug: log shapes to help identify exceptions in compute functions
    logger.debug("analytics_dashboard: %d records, %d goals", len(records_dicts), len(goals_dicts))
    logger.debug("records_sample: %s", records_dicts[:3])
    logger.debug("goals_sample: %s", goals_dicts[:3])

    fin_analytics  = compute_financial_analytics(records_dicts)
    goal_analytics = compute_goal_analytics(goals_dicts)
    pcomp          = profile_completeness(current_user)
    progress_score = compute_progress_score(
        fin_analytics, goal_analytics, act_count, inter_count, pcomp
    )
    insights = compute_financial_insights(fin_analytics)

    # Recent activities
    act_result = await db.execute(
        select(ActivityLog).where(ActivityLog.user_id == current_user.id)
        .order_by(desc(ActivityLog.created_at)).limit(5)
    )
    recent_acts = list(act_result.scalars().all())
    recent_dicts = [
        {"id": a.id, "activity_type": a.activity_type, "title": a.title,
         "created_at": a.created_at.isoformat()}
        for a in recent_acts
    ]

    return DashboardAnalyticsOut(
        progress_score=ProgressScoreOut(**progress_score),
        financial_analytics=FinancialAnalyticsOut(
            **{k: v for k, v in fin_analytics.items()
               if k not in ("revenue_series", "expense_series", "profit_series")},
            revenue_series=[FinancialTrendPoint(**p) for p in fin_analytics.get("revenue_series", [])],
            expense_series=[FinancialTrendPoint(**p) for p in fin_analytics.get("expense_series", [])],
            profit_series=[FinancialTrendPoint(**p)  for p in fin_analytics.get("profit_series",  [])],
        ),
        goal_analytics=GoalAnalyticsOut(**goal_analytics),
        financial_insights=insights,
        recent_activities=recent_dicts,
    )


@analytics_router.get("/financial", response_model=FinancialAnalyticsOut,
                      summary="Financial analytics only")
async def analytics_financial(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> FinancialAnalyticsOut:
    rec_result = await db.execute(
        select(FinancialProgressRecord)
        .where(FinancialProgressRecord.user_id == current_user.id)
        .order_by(FinancialProgressRecord.record_date)
    )
    records = list(rec_result.scalars().all())
    records_dicts = [
        {"record_date": r.record_date, "revenue": r.revenue,
         "expenses": r.expenses, "profit": r.profit}
        for r in records
    ]
    fa = compute_financial_analytics(records_dicts)
    return FinancialAnalyticsOut(
        **{k: v for k, v in fa.items()
           if k not in ("revenue_series", "expense_series", "profit_series")},
        revenue_series=[FinancialTrendPoint(**p) for p in fa.get("revenue_series", [])],
        expense_series=[FinancialTrendPoint(**p) for p in fa.get("expense_series", [])],
        profit_series=[FinancialTrendPoint(**p)  for p in fa.get("profit_series",  [])],
    )


@analytics_router.get("/goals", response_model=GoalAnalyticsOut,
                      summary="Goal analytics only")
async def analytics_goals(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> GoalAnalyticsOut:
    result = await db.execute(
        select(BusinessGoal).where(BusinessGoal.user_id == current_user.id)
    )
    goals = list(result.scalars().all())
    goals_dicts = [
        {"status": g.status, "priority": g.priority, "goal_type": g.goal_type,
         "is_overdue": g.is_overdue}
        for g in goals
    ]
    return GoalAnalyticsOut(**compute_goal_analytics(goals_dicts))


@analytics_router.get("/progress-score", response_model=ProgressScoreOut,
                      summary="Entrepreneur progress score")
async def analytics_progress_score(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> ProgressScoreOut:
    records, goals, act_count, inter_count, *_ = await _load_analytics_data(db, current_user.id)
    records_dicts = [{"record_date": r.record_date, "revenue": r.revenue, "expenses": r.expenses, "profit": r.profit} for r in records]
    goals_dicts   = [{"status": g.status, "priority": g.priority, "goal_type": g.goal_type, "is_overdue": g.is_overdue, "progress_percentage": g.progress_percentage} for g in goals]
    fa = compute_financial_analytics(records_dicts)
    ga = compute_goal_analytics(goals_dicts)
    ps = compute_progress_score(fa, ga, act_count, inter_count, profile_completeness(current_user))
    return ProgressScoreOut(**ps)


@analytics_router.get("/trends", summary="Financial trend data")
async def analytics_trends(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    rec_result = await db.execute(
        select(FinancialProgressRecord)
        .where(FinancialProgressRecord.user_id == current_user.id)
        .order_by(FinancialProgressRecord.record_date).limit(24)
    )
    records = list(rec_result.scalars().all())
    fa = compute_financial_analytics([
        {"record_date": r.record_date, "revenue": r.revenue,
         "expenses": r.expenses, "profit": r.profit}
        for r in records
    ])
    return {
        "revenue_trend": fa.get("revenue_trend"),
        "expense_trend": fa.get("expense_trend"),
        "profit_trend":  fa.get("profit_trend"),
        "revenue_series": fa.get("revenue_series", []),
        "expense_series": fa.get("expense_series", []),
        "profit_series":  fa.get("profit_series",  []),
        "record_count":  fa.get("record_count", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# ACTION PLAN
# ══════════════════════════════════════════════════════════════════════════════

@actions_router.get("/next", response_model=ActionPlanOut, summary="Get AI next-action plan")
async def get_action_plan(
    current_user: User       = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> ActionPlanOut:
    records, goals, act_count, inter_count, saved, advisory = await _load_analytics_data(
        db, current_user.id
    )
    fa = compute_financial_analytics([
        {"record_date": r.record_date, "revenue": r.revenue,
         "expenses": r.expenses, "profit": r.profit}
        for r in records
    ])

    user_profile = {
        "available_capital":   current_user.available_capital,
        "skills":              current_user.skills,
        "state":               current_user.state,
        "business_interests":  current_user.business_interests,
    }
    goals_dicts   = [{"title": g.title, "status": g.status, "is_overdue": g.is_overdue} for g in goals]
    saved_dicts   = [{"business_id": s.business_id} for s in saved]
    adv_dicts     = [{"id": a.id} for a in advisory]

    # Load interactions count
    inter_result = await db.execute(
        select(RecommendationInteraction).where(RecommendationInteraction.user_id == current_user.id).limit(20)
    )
    interactions = list(inter_result.scalars().all())
    inter_dicts = [{"business_id": i.business_id, "type": i.interaction_type} for i in interactions]

    actions = generate_action_plan(
        user_profile=user_profile,
        financial_records=[{"revenue": r.revenue} for r in records],
        goals=goals_dicts,
        saved_businesses=saved_dicts,
        advisory_sessions=adv_dicts,
        interactions=inter_dicts,
        profile_completeness=profile_completeness(current_user),
        financial_analytics=fa,
    )
    return ActionPlanOut(actions=actions, generated=True, total=len(actions))


@actions_router.patch("/{action_id}/status", response_model=ActionItemOut,
                      summary="Update an action item status")
async def update_action_status(
    body:      ActionStatusUpdate,
    action_id: str         = Path(...),
    current_user: User     = Depends(get_current_user),
    db: AsyncSession       = Depends(get_db),
) -> ActionItemOut:
    if body.status not in VALID_STATUSES:
        raise HTTPException(422, f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    result = await db.execute(
        select(ActionItem).where(
            and_(ActionItem.id == action_id, ActionItem.user_id == current_user.id)
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(404, "Action item not found")
    item.status = body.status
    await db.commit()
    await db.refresh(item)
    return ActionItemOut.model_validate(item)


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY TIMELINE
# ══════════════════════════════════════════════════════════════════════════════

@activity_router.get("/timeline", response_model=TimelineOut, summary="Entrepreneur journey timeline")
async def get_timeline(
    limit:  int          = Query(20, ge=1, le=50),
    offset: int          = Query(0, ge=0),
    current_user: User   = Depends(get_current_user),
    db: AsyncSession     = Depends(get_db),
) -> TimelineOut:
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.user_id == current_user.id)
        .order_by(desc(ActivityLog.created_at)).offset(offset).limit(limit)
    )
    items = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    return TimelineOut(
        items=[ActivityOut.model_validate(a) for a in items],
        total=total,
    )
