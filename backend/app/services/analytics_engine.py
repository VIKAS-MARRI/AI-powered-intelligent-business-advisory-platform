"""
Phase 9 — Analytics Engine.
Computes financial analytics, goal analytics, progress scores, and trends
entirely from user-entered data. Never invents figures.

All calculations are transparent and deterministic.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ── Trend thresholds ──────────────────────────────────────────────────────────
TREND_IMPROVE_PCT =  5.0   # ≥5% growth → improving
TREND_DECLINE_PCT = -5.0   # ≤-5% growth → declining


def _pct_change(old: float, new: float) -> Optional[float]:
    if old == 0:
        return None
    return round((new - old) / abs(old) * 100, 1)


def _trend_label(pct: Optional[float]) -> str:
    if pct is None:
        return "insufficient_data"
    if pct >= TREND_IMPROVE_PCT:
        return "improving"
    if pct <= TREND_DECLINE_PCT:
        return "declining"
    return "stable"


# ── Financial analytics ───────────────────────────────────────────────────────

def compute_financial_analytics(records: List[Dict]) -> Dict[str, Any]:
    """
    Accepts a list of financial progress record dicts (sorted by date asc).
    Returns rich financial analytics with trend data.
    """
    if not records:
        return {
            "status": "insufficient_data",
            "message": "No financial records found. Add records via Financial Progress.",
            "total_revenue": 0, "total_expenses": 0, "total_profit": 0,
            "avg_monthly_revenue": 0, "avg_monthly_profit": 0, "avg_monthly_expenses": 0,
            "revenue_growth_pct": None, "expense_growth_pct": None, "profit_growth_pct": None,
            "revenue_trend": "insufficient_data",
            "expense_trend": "insufficient_data",
            "profit_trend": "insufficient_data",
            "record_count": 0,
            "period_months": 0,
            "best_period": None,
            "worst_period": None,
            "revenue_series": [],
            "expense_series": [],
            "profit_series":  [],
            "disclaimer": "⚠️ No financial records yet. Add records via Financial Progress to unlock analytics.",
        }

    revenues  = [r.get("revenue")  or 0.0 for r in records]
    expenses  = [r.get("expenses") or 0.0 for r in records]
    profits   = [r.get("profit")   or 0.0 for r in records]
    dates     = [r.get("record_date") for r in records]

    total_revenue  = sum(revenues)
    total_expenses = sum(expenses)
    total_profit   = sum(profits)
    n = len(records)

    avg_monthly_revenue  = round(total_revenue  / n, 2)
    avg_monthly_expenses = round(total_expenses / n, 2)
    avg_monthly_profit   = round(total_profit   / n, 2)

    # Growth: compare first half vs second half of records
    mid = n // 2
    if n >= 2:
        rev_old  = sum(revenues[:mid])  / max(mid, 1)
        rev_new  = sum(revenues[mid:])  / max(n - mid, 1)
        exp_old  = sum(expenses[:mid])  / max(mid, 1)
        exp_new  = sum(expenses[mid:])  / max(n - mid, 1)
        pro_old  = sum(profits[:mid])   / max(mid, 1)
        pro_new  = sum(profits[mid:])   / max(n - mid, 1)
        rev_growth = _pct_change(rev_old, rev_new)
        exp_growth = _pct_change(exp_old, exp_new)
        pro_growth = _pct_change(pro_old, pro_new)
    else:
        rev_growth = exp_growth = pro_growth = None

    # Best / worst period
    best_idx  = profits.index(max(profits))  if profits else 0
    worst_idx = profits.index(min(profits))  if profits else 0

    def _period_label(idx: int) -> Optional[str]:
        d = dates[idx]
        if d is None:
            return None
        if isinstance(d, str):
            return d[:7]   # YYYY-MM
        if isinstance(d, (date, datetime)):
            return d.strftime("%Y-%m")
        return str(d)

    # Period span in months
    period_months = n  # each record = ~1 period

    return {
        "status": "ok",
        "record_count":          n,
        "period_months":         period_months,
        "total_revenue":         round(total_revenue, 2),
        "total_expenses":        round(total_expenses, 2),
        "total_profit":          round(total_profit, 2),
        "avg_monthly_revenue":   avg_monthly_revenue,
        "avg_monthly_expenses":  avg_monthly_expenses,
        "avg_monthly_profit":    avg_monthly_profit,
        "revenue_growth_pct":    rev_growth,
        "expense_growth_pct":    exp_growth,
        "profit_growth_pct":     pro_growth,
        "revenue_trend":         _trend_label(rev_growth),
        "expense_trend":         _trend_label(exp_growth),
        "profit_trend":          _trend_label(pro_growth),
        "best_period":           _period_label(best_idx),
        "worst_period":          _period_label(worst_idx),
        "revenue_series":        [{"date": _period_label(i), "value": revenues[i]}  for i in range(n)],
        "expense_series":        [{"date": _period_label(i), "value": expenses[i]}  for i in range(n)],
        "profit_series":         [{"date": _period_label(i), "value": profits[i]}   for i in range(n)],
        "disclaimer": (
            "⚠️ These are entrepreneur-entered figures for tracking purposes only. "
            "Not verified financial data."
        ),
    }


# ── Goal analytics ────────────────────────────────────────────────────────────

def compute_goal_analytics(goals: List[Dict]) -> Dict[str, Any]:
    """Analyse a list of goal dicts."""
    if not goals:
        return {
            "total": 0, "completed": 0, "in_progress": 0,
            "not_started": 0, "overdue": 0,
            "completion_pct": 0.0,
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "by_type": {},
        }

    total       = len(goals)
    completed   = sum(1 for g in goals if g.get("status") == "completed")
    in_progress = sum(1 for g in goals if g.get("status") == "in_progress")
    not_started = sum(1 for g in goals if g.get("status") == "not_started")
    overdue     = sum(1 for g in goals if g.get("is_overdue", False))

    by_priority: Dict[str, int] = {}
    by_type:     Dict[str, int] = {}
    for g in goals:
        p = g.get("priority", "medium")
        by_priority[p] = by_priority.get(p, 0) + 1
        t = g.get("goal_type", "general")
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "total":          total,
        "completed":      completed,
        "in_progress":    in_progress,
        "not_started":    not_started,
        "overdue":        overdue,
        "completion_pct": round((completed / total) * 100, 1) if total > 0 else 0.0,
        "by_priority":    by_priority,
        "by_type":        by_type,
    }


# ── Progress Score ────────────────────────────────────────────────────────────

SCORE_WEIGHTS = {
    "financial_progress":    0.30,
    "goal_completion":       0.25,
    "business_activity":     0.20,
    "financial_consistency": 0.15,
    "growth_trend":          0.10,
}


def compute_progress_score(
    financial_analytics: Dict,
    goal_analytics:      Dict,
    activity_count:      int,
    interactions_count:  int,
    profile_complete_pct: int,
) -> Dict[str, Any]:
    """
    Compute transparent 0–100 entrepreneur progress score.
    Returns category scores, strengths, and improvement areas.
    """
    has_fin = financial_analytics.get("record_count", 0) > 0
    has_goals = goal_analytics.get("total", 0) > 0

    # 1. Financial Progress (30%)
    if has_fin:
        rec_count = financial_analytics["record_count"]
        avg_profit = financial_analytics.get("avg_monthly_profit", 0)
        # Up to 50 from having records (max 10 records = 50), up to 50 from profit
        record_score = min(50, rec_count * 5)
        profit_score = 50 if avg_profit > 0 else 0
        financial_progress_raw = min(100, record_score + profit_score)
    else:
        financial_progress_raw = 0.0

    # 2. Goal Completion (25%)
    if has_goals:
        completion_pct = goal_analytics.get("completion_pct", 0)
        in_progress_bonus = min(20, goal_analytics.get("in_progress", 0) * 10)
        goal_raw = min(100, completion_pct + in_progress_bonus)
    else:
        goal_raw = 0.0

    # 3. Business Activity (20%) — interactions + activities
    activity_raw = min(100, (activity_count + interactions_count) * 5)

    # 4. Financial Consistency (15%) — based on record count continuity
    if has_fin:
        rec_count = financial_analytics["record_count"]
        consistency_raw = min(100, rec_count * 10)  # 10 records = 100
    else:
        consistency_raw = 0.0

    # 5. Growth Trend (10%)
    trend_map = {"improving": 100, "stable": 60, "declining": 20, "insufficient_data": 0}
    profit_trend = financial_analytics.get("profit_trend", "insufficient_data")
    growth_raw = trend_map.get(profit_trend, 0)

    # Weighted sum
    raw_score = (
        financial_progress_raw    * SCORE_WEIGHTS["financial_progress"] +
        goal_raw                  * SCORE_WEIGHTS["goal_completion"] +
        activity_raw              * SCORE_WEIGHTS["business_activity"] +
        consistency_raw           * SCORE_WEIGHTS["financial_consistency"] +
        growth_raw                * SCORE_WEIGHTS["growth_trend"]
    )

    # Profile completeness bonus (up to +10)
    profile_bonus = round(profile_complete_pct / 10, 1)
    overall = round(min(100, raw_score + profile_bonus), 1)

    category_scores = {
        "financial_progress":    round(financial_progress_raw, 1),
        "goal_completion":       round(goal_raw, 1),
        "business_activity":     round(activity_raw, 1),
        "financial_consistency": round(consistency_raw, 1),
        "growth_trend":          round(growth_raw, 1),
    }

    # Strengths & improvement areas
    strengths, improvements = [], []
    if financial_progress_raw >= 60:
        strengths.append("Actively tracking financial progress")
    else:
        improvements.append("Start recording monthly revenue and expenses")

    if goal_raw >= 60:
        strengths.append("Good goal completion rate")
    elif has_goals:
        improvements.append("Work towards completing your active goals")
    else:
        improvements.append("Create your first business goal to start tracking")

    if activity_raw >= 50:
        strengths.append("Actively using the platform features")
    else:
        improvements.append("Explore more platform features (Market, Schemes, Finance)")

    if growth_raw >= 60:
        strengths.append("Business showing positive growth trend")
    elif has_fin:
        improvements.append("Focus on improving monthly profit margins")

    if profile_complete_pct >= 80:
        strengths.append("Entrepreneur profile well-completed")
    else:
        improvements.append("Complete your entrepreneur profile for better recommendations")

    confidence = "high" if has_fin and has_goals else "medium" if has_fin or has_goals else "low"

    return {
        "overall_score":    overall,
        "category_scores":  category_scores,
        "weights":          SCORE_WEIGHTS,
        "strengths":        strengths[:4],
        "improvement_areas": improvements[:4],
        "confidence":       confidence,
        "score_explanation": (
            f"Score = Financial Progress×30% + Goal Completion×25% + "
            f"Business Activity×20% + Financial Consistency×15% + Growth Trend×10% + "
            f"Profile Bonus (max 10 pts)"
        ),
        "disclaimer": (
            "⚠️ This score reflects platform activity and entrepreneur-entered data only. "
            "It is not a credit score or financial rating."
        ),
    }


# ── Financial insights ────────────────────────────────────────────────────────

def compute_financial_insights(financial_analytics: Dict) -> List[str]:
    """Generate educational financial insights from analytics data."""
    insights = []
    if financial_analytics.get("status") == "insufficient_data":
        return ["Add financial records to unlock personalized insights."]

    avg_profit   = financial_analytics.get("avg_monthly_profit", 0)
    avg_revenue  = financial_analytics.get("avg_monthly_revenue", 0)
    profit_trend = financial_analytics.get("profit_trend", "insufficient_data")
    exp_trend    = financial_analytics.get("expense_trend", "insufficient_data")

    if avg_revenue > 0:
        margin = (avg_profit / avg_revenue) * 100
        if margin >= 30:
            insights.append(f"Strong profit margin of {margin:.0f}% — well above average for rural businesses.")
        elif margin >= 15:
            insights.append(f"Healthy profit margin of {margin:.0f}%.")
        else:
            insights.append(f"Profit margin is {margin:.0f}%. Consider reviewing expenses to improve margins.")

    if profit_trend == "improving":
        insights.append("Your profits are trending upward — keep up the momentum!")
    elif profit_trend == "declining":
        insights.append("Profits are declining. Review your expenses and customer acquisition strategies.")

    if exp_trend == "improving":
        insights.append("Expenses are growing — review discretionary costs to maintain profitability.")
    elif exp_trend == "declining":
        insights.append("Good expense management — your costs are under control.")

    avg_savings = 0  # placeholder; would need savings data
    if avg_profit > 0:
        insights.append(
            f"Based on your avg monthly profit of ₹{avg_profit:,.0f}, "
            f"consider saving 20% (₹{avg_profit * 0.2:,.0f}/month) as a business buffer."
        )

    if not insights:
        insights.append("Keep adding monthly records to unlock personalized insights.")

    return insights[:5]
