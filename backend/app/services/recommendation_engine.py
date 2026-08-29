"""
Recommendation Engine — deterministic, explainable business scoring.

ALL financial figures used here are ESTIMATES for advisory purposes only.
They do NOT represent guaranteed business outcomes.

Scoring Formula:
    Final Score = Budget×30% + Skills×25% + Interest×15% + Profit×15% + Risk×10% + IncomeGoal×5%
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.models.business import Business

# ─────────────────────────────────────────────────────────────────────────────
# Score weights (must sum to 1.0)
# ─────────────────────────────────────────────────────────────────────────────
WEIGHTS = {
    "budget":      0.30,
    "skills":      0.25,
    "interest":    0.15,
    "profit":      0.15,
    "risk":        0.10,
    "income_goal": 0.05,
}

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2}


# ─────────────────────────────────────────────────────────────────────────────
# Individual scorers (each returns 0–100)
# ─────────────────────────────────────────────────────────────────────────────

def score_budget(capital: Optional[float], biz: Business) -> float:
    """
    How well does the user's capital fit the business investment requirement?

    - Capital ≥ max_investment                         → 100
    - Capital between min and max                      → 70–100 (linear)
    - Capital slightly below min (within 20%)          → 30–70
    - Capital < 50% of min                             → 0–10
    """
    if capital is None or capital <= 0:
        return 40.0   # Unknown — neutral

    if capital >= biz.max_investment:
        return 100.0

    if capital >= biz.min_investment:
        # Interpolate: min→70, max→100
        ratio = (capital - biz.min_investment) / max(biz.max_investment - biz.min_investment, 1)
        return round(70 + ratio * 30, 1)

    # Capital below minimum
    ratio = capital / biz.min_investment
    if ratio >= 0.8:
        return round(30 + (ratio - 0.8) / 0.2 * 40, 1)   # 30–70
    elif ratio >= 0.5:
        return round(10 + (ratio - 0.5) / 0.3 * 20, 1)   # 10–30
    else:
        return round(ratio * 20, 1)                        # 0–10


def score_skills(user_skills_raw: Optional[str], biz: Business) -> float:
    """
    Overlap between user skills and business required skills.
    Case-insensitive, tokenised matching.
    """
    if not user_skills_raw or not user_skills_raw.strip():
        return 35.0   # No skills listed — neutral-low

    def tokenise(text: str) -> set[str]:
        tokens = re.split(r"[,;\n]+", text.lower())
        result: set[str] = set()
        for t in tokens:
            words = re.findall(r"\b\w+\b", t)
            result.update(words)
            clean = t.strip()
            if clean:
                result.add(clean)
        return result

    user_tokens = tokenise(user_skills_raw)
    biz_tokens  = tokenise(biz.required_skills)

    if not biz_tokens:
        return 70.0

    matched = sum(
        1 for bt in biz_tokens
        if any(
            bt in ut or ut in bt or _keyword_overlap(bt, ut)
            for ut in user_tokens
        )
    )
    ratio = matched / len(biz_tokens)
    return round(min(100, ratio * 120), 1)   # slight boost so partial matches still score well


def _keyword_overlap(a: str, b: str) -> bool:
    """True if either string is a meaningful substring of the other (≥4 chars)."""
    if len(a) < 4 or len(b) < 4:
        return False
    return a in b or b in a


def score_interest(user_interests_raw: Optional[str], biz: Business) -> float:
    """
    Does the user express interest in this type of business?
    Matches against business name, category, and business_type.
    """
    if not user_interests_raw or not user_interests_raw.strip():
        return 50.0   # No interests stated — neutral

    interest_lower = user_interests_raw.lower()
    biz_text = f"{biz.name} {biz.category} {biz.business_type} {biz.description}".lower()

    keywords = re.findall(r"\b\w{3,}\b", interest_lower)
    matched = sum(1 for kw in keywords if kw in biz_text)

    if not keywords:
        return 50.0

    ratio = matched / len(keywords)
    return round(min(100, 40 + ratio * 80), 1)


def score_profit(biz: Business) -> float:
    """
    Profit potential score based on the estimated profit margin.
    margin = avg_profit / avg_revenue
    """
    avg_revenue = (biz.estimated_monthly_revenue_min + biz.estimated_monthly_revenue_max) / 2
    avg_profit  = (biz.estimated_monthly_profit_min  + biz.estimated_monthly_profit_max)  / 2

    if avg_revenue <= 0:
        return 50.0

    margin = avg_profit / avg_revenue
    # 0% → 0, 20% → 50, 40%+ → 100
    score = min(100, margin * 250)
    return round(max(0, score), 1)


def score_risk(biz: Business, preferred_risk: Optional[str] = None) -> float:
    """
    Risk compatibility.
    If user has no preference: Low→90, Medium→75, High→55.
    If user preference given: match gives 100, adjacent 60, opposite 20.
    """
    biz_risk = biz.risk_level

    if not preferred_risk or preferred_risk.lower() == "any":
        default = {"Low": 90, "Medium": 75, "High": 55}
        return float(default.get(biz_risk, 70))

    pref = preferred_risk.capitalize()
    biz_r = biz_risk.capitalize()

    if pref == biz_r:
        return 100.0
    diff = abs(RISK_ORDER.get(pref, 1) - RISK_ORDER.get(biz_r, 1))
    return {0: 100.0, 1: 60.0, 2: 20.0}.get(diff, 50.0)


def score_income_goal(income_goal: Optional[float], biz: Business) -> float:
    """
    Can this business plausibly meet the monthly income goal?
    Uses the upper end of the profit estimate.
    """
    if income_goal is None or income_goal <= 0:
        return 60.0

    max_profit = biz.estimated_monthly_profit_max
    if max_profit <= 0:
        return 10.0

    ratio = max_profit / income_goal
    if ratio >= 1.2:
        return 100.0
    elif ratio >= 1.0:
        return round(80 + (ratio - 1.0) / 0.2 * 20, 1)
    elif ratio >= 0.7:
        return round(50 + (ratio - 0.7) / 0.3 * 30, 1)
    elif ratio >= 0.4:
        return round(20 + (ratio - 0.4) / 0.3 * 30, 1)
    else:
        return round(ratio * 50, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Main scoring function
# ─────────────────────────────────────────────────────────────────────────────

def score_business(
    biz: Business,
    capital: Optional[float],
    skills: Optional[str],
    interests: Optional[str],
    income_goal: Optional[float],
    preferred_risk: Optional[str],
) -> dict:
    """
    Score a single business against the user's profile.
    Returns a dict with component scores and the final weighted score.
    """
    budget_s      = score_budget(capital, biz)
    skills_s      = score_skills(skills, biz)
    interest_s    = score_interest(interests, biz)
    profit_s      = score_profit(biz)
    risk_s        = score_risk(biz, preferred_risk)
    income_goal_s = score_income_goal(income_goal, biz)

    final = round(
        budget_s      * WEIGHTS["budget"]      +
        skills_s      * WEIGHTS["skills"]      +
        interest_s    * WEIGHTS["interest"]    +
        profit_s      * WEIGHTS["profit"]      +
        risk_s        * WEIGHTS["risk"]        +
        income_goal_s * WEIGHTS["income_goal"],
        1,
    )

    return {
        "budget":      budget_s,
        "skills":      skills_s,
        "interest":    interest_s,
        "profit":      profit_s,
        "risk":        risk_s,
        "income_goal": income_goal_s,
        "final":       final,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Reason generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_reasons(scores: dict, biz: Business, capital: Optional[float]) -> List[str]:
    """Generate human-readable explanations for the recommendation."""
    reasons: List[str] = []

    # Budget
    if scores["budget"] >= 80:
        reasons.append(f"Your capital comfortably covers the investment of ₹{biz.min_investment:,.0f}–₹{biz.max_investment:,.0f}")
    elif scores["budget"] >= 50:
        reasons.append(f"Your capital can cover the minimum investment of ₹{biz.min_investment:,.0f}")
    elif scores["budget"] < 30 and capital:
        reasons.append(f"⚠️ Investment may stretch your budget (₹{biz.min_investment:,.0f} min required)")

    # Skills
    if scores["skills"] >= 75:
        reasons.append(f"Your skills align well with requirements: {biz.required_skills[:80]}")
    elif scores["skills"] >= 45:
        reasons.append(f"You have some relevant skills; additional training may help")
    else:
        reasons.append(f"Consider upskilling in: {biz.required_skills[:60]}")

    # Profit
    avg_profit = (biz.estimated_monthly_profit_min + biz.estimated_monthly_profit_max) / 2
    reasons.append(
        f"Estimated monthly profit: ₹{biz.estimated_monthly_profit_min:,.0f}–₹{biz.estimated_monthly_profit_max:,.0f} (demo estimate)"
    )

    # Risk
    reasons.append(f"Risk level: {biz.risk_level}")

    # Interest match
    if scores["interest"] >= 70:
        reasons.append("Matches your stated business interests")

    # Income goal
    if scores["income_goal"] >= 80:
        reasons.append("Likely to meet your monthly income goal based on estimates")
    elif scores["income_goal"] < 40:
        reasons.append("⚠️ Profit estimates may fall short of your income goal")

    return reasons[:6]   # Cap at 6 reasons


# ─────────────────────────────────────────────────────────────────────────────
# Profile completeness
# ─────────────────────────────────────────────────────────────────────────────

def profile_completeness(user) -> int:
    """Return profile completeness as 0–100 integer."""
    fields = [
        user.available_capital,
        user.skills,
        user.business_interests,
        user.monthly_income_goal,
        user.state,
        user.district,
        user.experience_years,
    ]
    filled = sum(1 for f in fields if f is not None and str(f).strip() != "")
    return round((filled / len(fields)) * 100)
