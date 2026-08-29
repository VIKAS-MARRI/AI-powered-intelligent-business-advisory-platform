"""
Phase 9 — Action Plan Engine.
Generates deterministic, prioritised next-action recommendations based on
real user data from Phases 1–8. Never invents advice.

Actions are grounded in:
  - Profile completeness
  - Financial progress records
  - Business goals
  - Saved businesses
  - Advisory sessions
  - Interaction history

Each action links back to the correct platform page.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

# ── Action templates ──────────────────────────────────────────────────────────

def _action(
    title: str,
    description: str,
    category: str,
    priority: str,
    impact: str,
    effort: str,
    phase: str,
    url: str,
) -> Dict[str, Any]:
    return {
        "id":               str(uuid.uuid4()),
        "title":            title,
        "description":      description,
        "category":         category,
        "priority":         priority,
        "impact":           impact,
        "estimated_effort": effort,
        "related_phase":    phase,
        "action_url":       url,
        "status":           "pending",
    }


def generate_action_plan(
    user_profile:          Dict[str, Any],
    financial_records:     List[Dict],
    goals:                 List[Dict],
    saved_businesses:      List[Dict],
    advisory_sessions:     List[Dict],
    interactions:          List[Dict],
    profile_completeness:  int,
    financial_analytics:   Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a prioritised list of next actions.
    Returns at most 8 actions, sorted critical→high→medium→low.
    All actions are grounded in real user data.
    """
    actions: List[Dict[str, Any]] = []

    capital   = user_profile.get("available_capital")
    skills    = user_profile.get("skills")
    state     = user_profile.get("state")
    interests = user_profile.get("business_interests")

    # ── 1. Profile completeness ───────────────────────────────────────────────
    if profile_completeness < 50:
        actions.append(_action(
            "Complete your entrepreneur profile",
            "Add your skills, capital, location, and business interests to unlock personalised recommendations.",
            "profile", "critical", "high", "5 minutes", "Phase 1", "/profile",
        ))
    elif profile_completeness < 80:
        actions.append(_action(
            "Enhance your entrepreneur profile",
            "Add more details (monthly income goal, experience) to improve recommendation accuracy.",
            "profile", "medium", "medium", "5 minutes", "Phase 1", "/profile",
        ))

    # ── 2. No financial records ───────────────────────────────────────────────
    if not financial_records:
        actions.append(_action(
            "Record your first financial data",
            "Start tracking revenue and expenses monthly to unlock analytics and progress insights.",
            "finance", "high", "high", "10 minutes", "Phase 9", "/financial-progress",
        ))
    elif len(financial_records) < 3:
        actions.append(_action(
            "Add more financial records",
            f"You have {len(financial_records)} record(s). Add at least 3 months of data for trend analysis.",
            "finance", "medium", "high", "5 minutes", "Phase 9", "/financial-progress",
        ))

    # ── 3. No goals set ───────────────────────────────────────────────────────
    if not goals:
        actions.append(_action(
            "Create your first business goal",
            "Set a goal (revenue target, savings goal, or scheme application) to start tracking your journey.",
            "business", "high", "high", "5 minutes", "Phase 9", "/goals",
        ))
    else:
        overdue_goals = [g for g in goals if g.get("is_overdue")]
        if overdue_goals:
            actions.append(_action(
                f"Review {len(overdue_goals)} overdue goal(s)",
                "Some of your goals are past their target date. Update progress or adjust timelines.",
                "business", "high", "medium", "10 minutes", "Phase 9", "/goals",
            ))
        in_progress = [g for g in goals if g.get("status") == "in_progress"]
        if in_progress:
            g = in_progress[0]
            actions.append(_action(
                f"Update progress on '{g.get('title', 'goal')}'",
                "Record your latest progress to keep your tracking accurate and streak going.",
                "business", "medium", "medium", "2 minutes", "Phase 9", "/goals",
            ))

    # ── 4. No saved businesses ────────────────────────────────────────────────
    if not saved_businesses and not interests:
        actions.append(_action(
            "Explore personalised business recommendations",
            "Get AI-powered recommendations matched to your skills, capital, and location.",
            "business", "high", "high", "10 minutes", "Phase 8", "/recommendations",
        ))
    elif not saved_businesses:
        actions.append(_action(
            "Save a business recommendation",
            "Shortlist businesses that interest you to compare options and plan next steps.",
            "business", "medium", "medium", "5 minutes", "Phase 8", "/recommendations",
        ))

    # ── 5. No advisory session yet ────────────────────────────────────────────
    if not advisory_sessions:
        actions.append(_action(
            "Ask the AI Advisor",
            "Get personalised AI guidance on business selection, finance, and local market conditions.",
            "business", "medium", "high", "5 minutes", "Phase 7", "/advisor",
        ))

    # ── 6. Capital available but no analysis ─────────────────────────────────
    if capital and capital > 50000 and not advisory_sessions:
        actions.append(_action(
            "Run a financial feasibility analysis",
            f"You have ₹{capital:,.0f} available. Analyse a business's break-even, ROI, and profit projections.",
            "finance", "medium", "high", "10 minutes", "Phase 3", "/financial-analysis",
        ))

    # ── 7. Check government schemes ───────────────────────────────────────────
    if state:
        actions.append(_action(
            "Find government schemes for your state",
            f"Explore MUDRA, PMEGP, and state schemes available in {state} to fund your business.",
            "government_support", "medium", "high", "15 minutes", "Phase 6", "/scheme-support",
        ))
    else:
        actions.append(_action(
            "Explore government support schemes",
            "Discover MUDRA loans, PMEGP grants, and other schemes that can reduce your investment burden.",
            "government_support", "low", "high", "15 minutes", "Phase 6", "/scheme-support",
        ))

    # ── 8. Financial trend declining ─────────────────────────────────────────
    if financial_analytics and financial_analytics.get("profit_trend") == "declining":
        actions.append(_action(
            "Review declining profit trend",
            "Your profits show a declining trend. Use the Financial Analysis tool to identify root causes.",
            "finance", "high", "high", "20 minutes", "Phase 3", "/financial-analysis",
        ))

    # ── 9. Market intelligence ────────────────────────────────────────────────
    if saved_businesses and not interactions:
        actions.append(_action(
            "Check local market intelligence",
            "Analyse your area's competition, population, and infrastructure before investing.",
            "market", "medium", "medium", "10 minutes", "Phase 5", "/market-intelligence",
        ))

    # ── 10. Investment optimizer ─────────────────────────────────────────────
    if capital and capital > 100000:
        actions.append(_action(
            "Optimise your investment portfolio",
            f"With ₹{capital:,.0f} capital, run the Investment Optimizer to find the best allocation.",
            "finance", "low", "high", "10 minutes", "Phase 4", "/investment-optimizer",
        ))

    # Sort: critical > high > medium > low
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda a: priority_order.get(a["priority"], 9))

    return actions[:8]   # Return top 8 actions
