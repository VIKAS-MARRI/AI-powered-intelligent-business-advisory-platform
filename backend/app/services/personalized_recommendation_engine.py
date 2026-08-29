"""
Personalized Recommendation Engine — Phase 8.

Upgrades the Phase 2 keyword engine with:
  - Semantic skill matching (20%)
  - Budget compatibility (15%)
  - Market opportunity heuristic (15%)
  - Financial potential (10%)
  - Experience relevance (10%)
  - Government scheme support potential (10%)
  - Risk compatibility (8%)
  - Interest match (5%)
  - Income goal match (4%)
  - Location suitability (3%)

All weights are configurable. Falls back gracefully when data is missing.
Returns transparent score breakdowns and explainable reasons.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.models.business import Business
from app.services.recommendation_engine import (
    score_budget,
    score_interest,
    score_profit,
    score_risk,
    score_income_goal,
)
from app.services.semantic_matcher import semantic_match

logger = logging.getLogger(__name__)

# ── Default weights (must sum to 1.0) ─────────────────────────────────────────
DEFAULT_WEIGHTS: Dict[str, float] = {
    "semantic_skill":    0.20,
    "budget":            0.15,
    "market_opportunity":0.15,
    "financial_potential":0.10,
    "experience":        0.10,
    "gov_support":       0.10,
    "risk":              0.08,
    "interest":          0.05,
    "income_goal":       0.04,
    "location":          0.03,
}

# ── Scheme category → business category alignment ─────────────────────────────
# Used to approximate government support potential without a live DB query.
SCHEME_ALIGNMENT: Dict[str, List[str]] = {
    "Agriculture & Allied":    ["PM-KISAN", "KCC", "NABARD", "animal husbandry"],
    "Food Processing":         ["PMFME", "food park", "FSSAI"],
    "Manufacturing":           ["PMEGP", "MSME loan", "Mudra"],
    "Retail":                  ["MUDRA", "stand-up india"],
    "Service":                 ["PMEGP", "MUDRA", "Startup India"],
    "Education":               ["skill india", "PMKVY"],
    "Healthcare":              ["Ayushman", "PMJAY"],
    "Digital/IT":              ["digital india", "startup india"],
    "Handicraft":              ["artisan card", "PMEGP", "weavers"],
}

# ── Difficulty → experience mapping ──────────────────────────────────────────
DIFFICULTY_EXP: Dict[str, int] = {
    "Beginner":     0,
    "Intermediate": 2,
    "Advanced":     5,
}


# ── Sub-scorers ───────────────────────────────────────────────────────────────

def score_semantic_skill(
    user_skills: Optional[str],
    user_interests: Optional[str],
    biz: Business,
) -> tuple[float, Dict]:
    """Semantic skill match 0–100. Returns (score, match_detail)."""
    result = semantic_match(
        user_skills          = user_skills,
        user_interests       = user_interests,
        biz_name             = biz.name,
        biz_category         = biz.category,
        biz_description      = biz.description,
        biz_required_skills  = biz.required_skills,
    )
    return result["semantic_score"], result


def score_market_opportunity(biz: Business) -> float:
    """
    Estimate market opportunity based on profit margin + risk.
    High-margin, low-risk → better opportunity.
    0–100.
    """
    avg_rev  = (biz.estimated_monthly_revenue_min + biz.estimated_monthly_revenue_max) / 2
    avg_prof = (biz.estimated_monthly_profit_min  + biz.estimated_monthly_profit_max)  / 2
    margin   = avg_prof / max(avg_rev, 1)

    # Risk modifier
    risk_bonus = {"Low": 15, "Medium": 0, "High": -15}.get(biz.risk_level, 0)

    # Setup speed bonus (faster setup → higher opportunity score)
    avg_setup = (biz.setup_time_weeks_min + biz.setup_time_weeks_max) / 2
    speed_bonus = max(0, 10 - avg_setup)

    base = min(85, margin * 200)   # 42.5% margin → 85
    return round(max(0, min(100, base + risk_bonus + speed_bonus)), 1)


def score_experience(
    user_experience_years: Optional[int],
    user_skills: Optional[str],
    biz: Business,
) -> float:
    """
    Experience relevance score.
    Combines years of experience with skill relevance to business difficulty.
    0–100.
    """
    exp_years = user_experience_years or 0

    # Approximate difficulty from setup time and risk
    if biz.risk_level == "Low" and biz.setup_time_weeks_max <= 4:
        difficulty = "Beginner"
    elif biz.risk_level == "High" or biz.setup_time_weeks_max >= 12:
        difficulty = "Advanced"
    else:
        difficulty = "Intermediate"

    required_years = DIFFICULTY_EXP.get(difficulty, 0)

    if exp_years >= required_years + 3:
        exp_score = 100.0
    elif exp_years >= required_years:
        exp_score = 75.0
    elif exp_years >= max(0, required_years - 1):
        exp_score = 55.0
    else:
        exp_score = 35.0

    return round(exp_score, 1)


def score_gov_support_potential(biz: Business) -> float:
    """
    Approximate government support availability based on business category.
    0–100.
    """
    cat = biz.category
    for category, schemes in SCHEME_ALIGNMENT.items():
        if category.lower() in cat.lower() or cat.lower() in category.lower():
            # More schemes → higher score
            return round(min(100, 40 + len(schemes) * 15), 1)

    # Rural businesses generally have some support
    if biz.suitable_for_rural:
        return 55.0
    return 40.0


def score_location_suitability(
    user_location_type: Optional[str],
    biz: Business,
) -> float:
    """
    Location compatibility: 0–100.
    If user is rural and business is rural-suitable → high.
    """
    if not user_location_type:
        if biz.suitable_for_rural:
            return 70.0
        return 60.0

    loc = user_location_type.lower()
    if loc == "rural" and biz.suitable_for_rural:
        return 95.0
    elif loc in ("semi_urban", "semi-urban") and biz.suitable_for_rural:
        return 80.0
    elif loc == "urban":
        return 70.0    # most businesses work in urban too
    elif not biz.suitable_for_rural:
        return 45.0    # rural user, non-rural business
    return 60.0


# ── Preference learning modifier ─────────────────────────────────────────────

def preference_modifier(
    user_preference_data: Optional[Dict],
    biz: Business,
) -> float:
    """
    Adjust score based on interaction history.
    Returns a modifier between -5 and +10.
    Transparent: limited small boost to avoid black-box behavior.
    """
    if not user_preference_data:
        return 0.0

    modifier = 0.0
    preferred_categories = user_preference_data.get("preferred_categories", {})
    avoided_categories   = user_preference_data.get("avoided_categories", {})

    # Boost for frequently explored categories (max +8)
    cat_explores = preferred_categories.get(biz.category, 0)
    modifier += min(8.0, cat_explores * 1.5)

    # Penalty for dismissed categories (max -5)
    cat_dismissals = avoided_categories.get(biz.category, 0)
    modifier -= min(5.0, cat_dismissals * 2.0)

    # Risk preference alignment
    preferred_risk = user_preference_data.get("preferred_risk")
    if preferred_risk and preferred_risk.lower() == biz.risk_level.lower():
        modifier += 3.0

    return round(max(-5.0, min(10.0, modifier)), 1)


# ── Main scoring function ─────────────────────────────────────────────────────

def personalized_score(
    biz:                   Business,
    capital:               Optional[float],
    skills:                Optional[str],
    interests:             Optional[str],
    income_goal:           Optional[float],
    preferred_risk:        Optional[str],
    experience_years:      Optional[int] = None,
    location_type:         Optional[str] = None,
    preference_data:       Optional[Dict] = None,
    weights:               Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Score a single business with the Phase 8 personalized engine.
    Returns transparent breakdown + final score.
    """
    W = weights or DEFAULT_WEIGHTS

    # Component scores (all 0–100)
    sem_score, sem_detail = score_semantic_skill(skills, interests, biz)
    budget_s     = score_budget(capital, biz)
    market_s     = score_market_opportunity(biz)
    financial_s  = score_profit(biz)
    exp_s        = score_experience(experience_years, skills, biz)
    gov_s        = score_gov_support_potential(biz)
    risk_s       = score_risk(biz, preferred_risk)
    interest_s   = score_interest(interests, biz)
    income_s     = score_income_goal(income_goal, biz)
    location_s   = score_location_suitability(location_type, biz)

    raw_final = (
        sem_score    * W["semantic_skill"]    +
        budget_s     * W["budget"]            +
        market_s     * W["market_opportunity"]+
        financial_s  * W["financial_potential"]+
        exp_s        * W["experience"]        +
        gov_s        * W["gov_support"]       +
        risk_s       * W["risk"]              +
        interest_s   * W["interest"]          +
        income_s     * W["income_goal"]       +
        location_s   * W["location"]
    )

    # Preference modifier (additive, capped)
    pref_mod  = preference_modifier(preference_data, biz)
    final     = round(max(0, min(100, raw_final + pref_mod)), 1)

    breakdown = {
        "semantic_skill":     round(sem_score    * W["semantic_skill"], 2),
        "budget":             round(budget_s     * W["budget"], 2),
        "market_opportunity": round(market_s     * W["market_opportunity"], 2),
        "financial_potential":round(financial_s  * W["financial_potential"], 2),
        "experience":         round(exp_s        * W["experience"], 2),
        "gov_support":        round(gov_s        * W["gov_support"], 2),
        "risk":               round(risk_s       * W["risk"], 2),
        "interest":           round(interest_s   * W["interest"], 2),
        "income_goal":        round(income_s     * W["income_goal"], 2),
        "location":           round(location_s   * W["location"], 2),
        "preference_modifier":pref_mod,
    }

    raw_scores = {
        "semantic_skill":     sem_score,
        "budget":             budget_s,
        "market_opportunity": market_s,
        "financial_potential":financial_s,
        "experience":         exp_s,
        "gov_support":        gov_s,
        "risk":               risk_s,
        "interest":           interest_s,
        "income_goal":        income_s,
        "location":           location_s,
    }

    return {
        "final_score":       final,
        "breakdown":         breakdown,
        "raw_scores":        raw_scores,
        "semantic_detail":   sem_detail,
        # Legacy compat: expose top 6 fields expected by Phase 2 API
        "budget":            budget_s,
        "skills":            sem_score,
        "interest":          interest_s,
        "profit":            financial_s,
        "risk":              risk_s,
        "income_goal":       income_s,
        "final":             final,
    }


def generate_personalized_reasons(
    scores:  Dict,
    biz:     Business,
    capital: Optional[float],
) -> List[str]:
    """Generate rich, explainable reasons for the recommendation."""
    reasons: List[str] = []
    raw = scores.get("raw_scores", {})

    # 1. Semantic skill match
    sem = scores.get("semantic_detail", {})
    sem_score = raw.get("semantic_skill", 0)
    if sem_score >= 70:
        concepts = sem.get("matched_concepts", [])
        if concepts:
            reasons.append(f"✓ Your skills in {', '.join(concepts[:2])} strongly match this business")
        else:
            reasons.append("✓ Your experience background aligns well with this business")
    elif sem_score >= 40:
        reasons.append("✓ Partial skill match — some relevant experience detected")
    else:
        reasons.append("⚠ Limited direct skill match — willingness to learn is important")

    # 2. Budget
    budget_s = raw.get("budget", 0)
    if budget_s >= 80:
        reasons.append(f"✓ Your capital comfortably covers the investment (₹{biz.min_investment:,.0f}–₹{biz.max_investment:,.0f})")
    elif budget_s >= 50:
        reasons.append(f"✓ Your capital meets the minimum requirement of ₹{biz.min_investment:,.0f}")
    elif capital:
        reasons.append(f"⚠ Investment may exceed your budget (₹{biz.min_investment:,.0f} required)")

    # 3. Profit potential
    avg_profit = (biz.estimated_monthly_profit_min + biz.estimated_monthly_profit_max) / 2
    reasons.append(
        f"📊 Estimated monthly profit: ₹{biz.estimated_monthly_profit_min:,.0f}–₹{biz.estimated_monthly_profit_max:,.0f} (estimate)"
    )

    # 4. Government support
    gov_s = raw.get("gov_support", 0)
    if gov_s >= 65:
        reasons.append(f"🏛️ Good government scheme support likely available for this category")

    # 5. Market opportunity
    mkt_s = raw.get("market_opportunity", 0)
    if mkt_s >= 70:
        reasons.append("📍 Strong market opportunity based on profit margins and risk profile")
    elif mkt_s >= 50:
        reasons.append("📍 Moderate market opportunity estimated")

    # 6. Risk
    reasons.append(f"⚡ Risk level: {biz.risk_level}")

    # 7. Income goal
    income_s = raw.get("income_goal", 0)
    if income_s >= 80:
        reasons.append("✓ Likely to meet your monthly income goal (based on estimates)")
    elif income_s < 40:
        reasons.append("⚠ Profit estimates may fall short of your income goal")

    return reasons[:7]


def explain_recommendation(scores: Dict, biz: Business, capital: Optional[float]) -> Dict:
    """
    Full structured explanation for the recommendation.
    """
    raw = scores.get("raw_scores", {})
    sem = scores.get("semantic_detail", {})
    reasons = generate_personalized_reasons(scores, biz, capital)

    strengths   = [r for r in reasons if r.startswith("✓")]
    challenges  = []
    if biz.key_challenges:
        challenges = [c.strip() for c in biz.key_challenges.split(",") if c.strip()][:3]

    next_steps = []
    if raw.get("market_opportunity", 0) < 60:
        next_steps.append("Validate local demand before investing")
    next_steps.append(f"Review total investment needed: ₹{biz.min_investment:,.0f}–₹{biz.max_investment:,.0f}")
    if raw.get("gov_support", 0) >= 55:
        next_steps.append("Explore government scheme eligibility (MUDRA, PMEGP, etc.)")
    if raw.get("semantic_skill", 0) < 50:
        next_steps.append(f"Consider skill-building in: {biz.required_skills[:60]}")
    next_steps.append("Use the Financial Analysis tool for detailed projections")

    return {
        "why_recommended":  reasons,
        "strengths":        strengths,
        "challenges":       challenges[:3],
        "next_steps":       next_steps[:5],
        "financial_outlook": {
            "min_investment":  biz.min_investment,
            "max_investment":  biz.max_investment,
            "monthly_profit_min": biz.estimated_monthly_profit_min,
            "monthly_profit_max": biz.estimated_monthly_profit_max,
            "risk_level":      biz.risk_level,
        },
        "semantic_match": {
            "score":          sem.get("semantic_score", 0),
            "concepts":       sem.get("matched_concepts", []),
            "explanation":    sem.get("explanation", ""),
        },
        "disclaimer": (
            "⚠️ All financial figures are estimates for advisory purposes only. "
            "Actual results depend on execution, local conditions, and market factors."
        ),
    }
