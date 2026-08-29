"""
Financial Calculator — deterministic business financial planning engine.

ALL results are ESTIMATES for planning purposes only.
Actual costs, revenue, and profits may vary significantly.

No AI/LLM is used here — all calculations are explicit, transparent Python formulas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InvestmentAllocation:
    equipment: float
    initial_inventory: float
    business_setup: float
    licensing: float
    marketing: float
    working_capital: float
    emergency_reserve: float
    total_allocated: float
    available_capital: float
    funding_gap: float          # > 0 means capital is insufficient
    is_feasible: bool

    @property
    def allocation_dict(self) -> dict:
        return {
            "Equipment":          self.equipment,
            "Initial Inventory":  self.initial_inventory,
            "Business Setup":     self.business_setup,
            "Licensing / Other":  self.licensing,
            "Marketing":          self.marketing,
            "Working Capital":    self.working_capital,
            "Emergency Reserve":  self.emergency_reserve,
        }


@dataclass
class ScenarioResult:
    name: str                    # Conservative / Expected / Optimistic
    monthly_revenue: float
    monthly_expenses: float
    monthly_profit: float
    annual_revenue: float
    annual_profit: float
    profit_margin_pct: float     # 0–100


@dataclass
class BreakEvenResult:
    fixed_costs_monthly: float
    variable_cost_ratio: float   # 0.0–1.0
    contribution_margin_ratio: float
    break_even_revenue: float    # monthly
    assumed: bool                # True if we used assumed values


@dataclass
class CashFlowMonth:
    month: int
    revenue: float
    expenses: float
    profit: float
    cumulative_cash_flow: float


@dataclass
class HealthScoreBreakdown:
    budget_sufficiency: float     # 0–20
    profitability: float          # 0–25
    roi_score: float              # 0–20
    payback_score: float          # 0–15
    emergency_reserve_score: float# 0–10
    expense_ratio_score: float    # 0–10
    total: float                  # 0–100
    status: str                   # Excellent / Good / Fair / Needs Attention
    strengths: List[str]
    risks: List[str]
    recommendations: List[str]


@dataclass
class RiskIndicator:
    name: str
    level: str          # Low / Medium / High
    explanation: str


@dataclass
class FullFinancialAnalysis:
    business_id: str
    business_name: str
    available_capital: float
    investment: InvestmentAllocation
    conservative: ScenarioResult
    expected: ScenarioResult
    optimistic: ScenarioResult
    roi_pct: float
    payback_months: Optional[float]
    payback_feasible: bool
    payback_note: str
    break_even: BreakEvenResult
    health: HealthScoreBreakdown
    risks: List[RiskIndicator]
    cash_flow: List[CashFlowMonth]
    disclaimer: str = (
        "⚠️ Financial projections are estimates for planning purposes only. "
        "Actual costs, revenue, and profits may vary."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Investment Planner
# ─────────────────────────────────────────────────────────────────────────────

# Allocation ratios (fraction of recommended investment, not of capital)
_DEFAULT_ALLOC_RATIOS = {
    "equipment":         0.35,
    "initial_inventory": 0.15,
    "business_setup":    0.10,
    "licensing":         0.025,
    "marketing":         0.05,
    "working_capital":   0.20,
    "emergency_reserve": 0.125,
}

def plan_investment(
    available_capital: float,
    min_investment: float,
    max_investment: float,
    emergency_reserve_pct: float = 0.125,  # 12.5% of capital
    working_capital_pct: float = 0.20,
) -> InvestmentAllocation:
    """
    Allocate available_capital across business start-up categories.

    Uses the average of min/max investment as the target.
    Respects available_capital — never over-allocates.
    """
    if available_capital < 0:
        available_capital = 0.0

    # Target is the min needed; cap at available capital
    target = min(min_investment, available_capital) if available_capital > 0 else min_investment
    budget = min(available_capital, max_investment)  # never spend more than max

    # Reserve and working capital are anchored to available capital
    emergency_reserve = round(available_capital * emergency_reserve_pct, 2)
    working_capital   = round(available_capital * working_capital_pct, 2)
    deployable        = max(0, available_capital - emergency_reserve - working_capital)

    # Remaining ratios (must sum to 1.0 after removing wc + reserve)
    core_ratios = {
        "equipment":         0.47,
        "initial_inventory": 0.20,
        "business_setup":    0.14,
        "licensing":         0.03,
        "marketing":         0.06,
    }
    # Normalise (already sum to ~0.90 but let's be safe)
    ratio_sum = sum(core_ratios.values())
    equipment         = round(deployable * core_ratios["equipment"]         / ratio_sum, 2)
    initial_inventory = round(deployable * core_ratios["initial_inventory"] / ratio_sum, 2)
    business_setup    = round(deployable * core_ratios["business_setup"]    / ratio_sum, 2)
    licensing         = round(deployable * core_ratios["licensing"]         / ratio_sum, 2)
    marketing         = round(deployable * core_ratios["marketing"]         / ratio_sum, 2)

    total_allocated = (
        equipment + initial_inventory + business_setup +
        licensing + marketing + working_capital + emergency_reserve
    )

    # Fix rounding drift
    drift = round(available_capital - total_allocated, 2)
    working_capital = round(working_capital + drift, 2)
    total_allocated = round(total_allocated + drift, 2)

    funding_gap = round(max(0, min_investment - available_capital), 2)

    return InvestmentAllocation(
        equipment=equipment,
        initial_inventory=initial_inventory,
        business_setup=business_setup,
        licensing=licensing,
        marketing=marketing,
        working_capital=working_capital,
        emergency_reserve=emergency_reserve,
        total_allocated=total_allocated,
        available_capital=available_capital,
        funding_gap=funding_gap,
        is_feasible=(funding_gap == 0),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Scenario Engine
# ─────────────────────────────────────────────────────────────────────────────

_SCENARIO_ADJUSTMENTS = {
    "Conservative": {"revenue_mult": 0.70, "expense_mult": 1.15},
    "Expected":     {"revenue_mult": 1.00, "expense_mult": 1.00},
    "Optimistic":   {"revenue_mult": 1.30, "expense_mult": 0.90},
}


def compute_scenario(
    name: str,
    revenue_min: float,
    revenue_max: float,
    expense_min: float,
    expense_max: float,
) -> ScenarioResult:
    """
    Compute a named scenario from the Phase 2 business revenue/expense range.
    Conservative skews to min revenue / max expenses.
    Optimistic skews to max revenue / min expenses.
    Expected uses the midpoints.
    """
    adj = _SCENARIO_ADJUSTMENTS[name]

    base_revenue = (revenue_min + revenue_max) / 2
    base_expense = (expense_min + expense_max) / 2

    monthly_revenue  = round(base_revenue * adj["revenue_mult"],  2)
    monthly_expenses = round(base_expense  * adj["expense_mult"],  2)

    # Conservative uses lower end of revenue range
    if name == "Conservative":
        monthly_revenue  = round(revenue_min * 0.85, 2)
        monthly_expenses = round(expense_max  * 1.10, 2)
    elif name == "Optimistic":
        monthly_revenue  = round(revenue_max * 1.05, 2)
        monthly_expenses = round(expense_min  * 0.92, 2)

    monthly_profit  = round(monthly_revenue - monthly_expenses, 2)
    annual_revenue  = round(monthly_revenue * 12, 2)
    annual_profit   = round(monthly_profit  * 12, 2)

    if monthly_revenue > 0:
        margin = round((monthly_profit / monthly_revenue) * 100, 1)
    else:
        margin = 0.0

    return ScenarioResult(
        name=name,
        monthly_revenue=monthly_revenue,
        monthly_expenses=monthly_expenses,
        monthly_profit=monthly_profit,
        annual_revenue=annual_revenue,
        annual_profit=annual_profit,
        profit_margin_pct=margin,
    )


def compute_all_scenarios(
    revenue_min: float, revenue_max: float,
    expense_min: float, expense_max: float,
) -> tuple[ScenarioResult, ScenarioResult, ScenarioResult]:
    return (
        compute_scenario("Conservative", revenue_min, revenue_max, expense_min, expense_max),
        compute_scenario("Expected",     revenue_min, revenue_max, expense_min, expense_max),
        compute_scenario("Optimistic",   revenue_min, revenue_max, expense_min, expense_max),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. ROI
# ─────────────────────────────────────────────────────────────────────────────

def compute_roi(annual_net_profit: float, initial_investment: float) -> float:
    """
    ROI (%) = (Annual Net Profit / Initial Investment) × 100
    Returns 0.0 if investment is 0 or negative.
    """
    if initial_investment <= 0:
        return 0.0
    return round((annual_net_profit / initial_investment) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Payback Period
# ─────────────────────────────────────────────────────────────────────────────

def compute_payback(
    initial_investment: float,
    monthly_profit: float,
) -> tuple[Optional[float], bool, str]:
    """
    Returns (months, feasible, note).
    months = None when not computable.
    """
    if initial_investment <= 0:
        return (0.0, True, "No investment required — immediate positive return.")
    if monthly_profit <= 0:
        if monthly_profit == 0:
            return (None, False, "Payback period cannot be estimated: zero monthly profit projected.")
        return (None, False, "Payback period cannot be estimated: business is projected to lose money each month.")
    months = round(initial_investment / monthly_profit, 1)
    note = f"Estimated payback in {months} months ({math.ceil(months / 12)} year(s))."
    return (months, True, note)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Break-Even Analysis
# ─────────────────────────────────────────────────────────────────────────────

def compute_break_even(
    monthly_expenses: float,
    fixed_cost_ratio: float = 0.55,
    variable_cost_ratio: Optional[float] = None,
) -> BreakEvenResult:
    """
    Break-Even Revenue = Fixed Costs / Contribution Margin Ratio
    Contribution Margin = 1 − Variable Cost Ratio

    If variable_cost_ratio is not provided, we estimate it as (1 - fixed_cost_ratio).
    Clearly labels when assumptions are used.
    """
    assumed = variable_cost_ratio is None

    if assumed:
        variable_cost_ratio = round(1.0 - fixed_cost_ratio, 4)

    variable_cost_ratio = max(0.01, min(0.99, variable_cost_ratio))  # clamp

    contribution_margin = round(1.0 - variable_cost_ratio, 4)
    fixed_costs = round(monthly_expenses * fixed_cost_ratio, 2)

    if contribution_margin <= 0:
        break_even_revenue = float('inf')
    else:
        break_even_revenue = round(fixed_costs / contribution_margin, 2)

    return BreakEvenResult(
        fixed_costs_monthly=fixed_costs,
        variable_cost_ratio=variable_cost_ratio,
        contribution_margin_ratio=contribution_margin,
        break_even_revenue=break_even_revenue,
        assumed=assumed,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Cash Flow Projection (12 months)
# ─────────────────────────────────────────────────────────────────────────────

def project_cash_flow(
    initial_monthly_revenue: float,
    initial_monthly_expenses: float,
    months: int = 12,
    monthly_revenue_growth_rate: float = 0.02,   # 2% per month default
    monthly_expense_growth_rate: float = 0.005,  # 0.5% per month
    ramp_up_months: int = 2,                     # first N months at 70% revenue
    ramp_up_factor: float = 0.70,
) -> List[CashFlowMonth]:
    """
    Generate month-by-month projections with optional ramp-up and growth.
    """
    projections: List[CashFlowMonth] = []
    cumulative = 0.0

    for m in range(1, months + 1):
        growth_factor = (1 + monthly_revenue_growth_rate) ** (m - 1)
        expense_factor = (1 + monthly_expense_growth_rate) ** (m - 1)

        revenue  = initial_monthly_revenue  * growth_factor
        expenses = initial_monthly_expenses * expense_factor

        # Ramp-up in early months
        if m <= ramp_up_months:
            revenue = round(revenue * ramp_up_factor, 2)

        revenue  = round(revenue, 2)
        expenses = round(expenses, 2)
        profit   = round(revenue - expenses, 2)
        cumulative = round(cumulative + profit, 2)

        projections.append(CashFlowMonth(
            month=m,
            revenue=revenue,
            expenses=expenses,
            profit=profit,
            cumulative_cash_flow=cumulative,
        ))

    return projections


# ─────────────────────────────────────────────────────────────────────────────
# 7. Financial Health Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_health_score(
    available_capital: float,
    min_investment: float,
    expected: ScenarioResult,
    roi_pct: float,
    payback_months: Optional[float],
    emergency_reserve: float,
    monthly_expenses: float,
) -> HealthScoreBreakdown:
    """
    Transparent 0–100 financial health score with category breakdown.

    Budget Sufficiency     0–20
    Profitability          0–25
    ROI Score              0–20
    Payback Score          0–15
    Emergency Reserve      0–10
    Expense Ratio          0–10
    ─────────────────────────────
    Total                  0–100
    """
    strengths: List[str] = []
    risks: List[str]     = []
    recs: List[str]      = []

    # ── Budget sufficiency (0–20) ─────────────────────────────────────────────
    if min_investment <= 0:
        budget_score = 20.0
    else:
        ratio = available_capital / min_investment
        if ratio >= 1.5:
            budget_score = 20.0; strengths.append("Ample capital above minimum investment")
        elif ratio >= 1.0:
            budget_score = 15.0; strengths.append("Capital meets minimum investment")
        elif ratio >= 0.8:
            budget_score = 8.0;  risks.append("Capital slightly below minimum investment"); recs.append("Consider raising ₹{:,.0f} more before starting".format(min_investment - available_capital))
        elif ratio >= 0.5:
            budget_score = 3.0;  risks.append("Significant capital shortfall"); recs.append("Explore MUDRA loan or government schemes")
        else:
            budget_score = 0.0;  risks.append("Capital is critically insufficient for this business")

    # ── Profitability (0–25) ──────────────────────────────────────────────────
    margin = expected.profit_margin_pct
    if margin >= 30:
        profitability = 25.0; strengths.append("Excellent profit margin (≥ 30%)")
    elif margin >= 20:
        profitability = 20.0; strengths.append("Good profit margin (20–30%)")
    elif margin >= 10:
        profitability = 13.0
    elif margin >= 0:
        profitability = 5.0;  risks.append("Very thin profit margin (< 10%)")
    else:
        profitability = 0.0;  risks.append("Projected monthly loss — expenses exceed revenue"); recs.append("Review pricing strategy and cost reduction options")

    # ── ROI (0–20) ────────────────────────────────────────────────────────────
    if roi_pct >= 50:
        roi_score = 20.0; strengths.append("Excellent ROI (≥ 50%/year)")
    elif roi_pct >= 25:
        roi_score = 15.0; strengths.append("Good ROI (25–50%/year)")
    elif roi_pct >= 10:
        roi_score = 9.0
    elif roi_pct >= 0:
        roi_score = 3.0;  risks.append("Low ROI (< 10%/year)")
    else:
        roi_score = 0.0;  risks.append("Negative ROI projected")

    # ── Payback (0–15) ───────────────────────────────────────────────────────
    if payback_months is None:
        payback_score = 0.0; risks.append("Payback period cannot be estimated (zero/negative profit)")
    elif payback_months <= 12:
        payback_score = 15.0; strengths.append(f"Short payback period ({payback_months:.0f} months)")
    elif payback_months <= 24:
        payback_score = 10.0
    elif payback_months <= 36:
        payback_score = 5.0;  recs.append("Payback period is long — consider ways to increase revenue")
    else:
        payback_score = 2.0;  risks.append("Very long payback period (> 3 years)")

    # ── Emergency reserve (0–10) ─────────────────────────────────────────────
    reserve_months = (emergency_reserve / monthly_expenses) if monthly_expenses > 0 else 0
    if reserve_months >= 3:
        reserve_score = 10.0; strengths.append("Adequate emergency reserve (≥ 3 months)")
    elif reserve_months >= 1.5:
        reserve_score = 6.0
    elif reserve_months >= 0.5:
        reserve_score = 2.0;  risks.append("Emergency reserve below 1 month of expenses"); recs.append("Build emergency fund to at least 3 months of expenses")
    else:
        reserve_score = 0.0;  risks.append("No meaningful emergency reserve")

    # ── Expense ratio (0–10) ─────────────────────────────────────────────────
    if expected.monthly_revenue > 0:
        expense_ratio = expected.monthly_expenses / expected.monthly_revenue
        if expense_ratio <= 0.6:
            expense_ratio_score = 10.0
        elif expense_ratio <= 0.75:
            expense_ratio_score = 7.0
        elif expense_ratio <= 0.9:
            expense_ratio_score = 3.0;  recs.append("Expenses are high relative to revenue — look for cost savings")
        else:
            expense_ratio_score = 0.0;  risks.append("Expenses consume > 90% of revenue")
    else:
        expense_ratio_score = 0.0

    total = round(
        budget_score + profitability + roi_score +
        payback_score + reserve_score + expense_ratio_score,
        1,
    )

    if total >= 80:
        status = "Excellent"
    elif total >= 60:
        status = "Good"
    elif total >= 40:
        status = "Fair"
    else:
        status = "Needs Attention"

    return HealthScoreBreakdown(
        budget_sufficiency=budget_score,
        profitability=profitability,
        roi_score=roi_score,
        payback_score=payback_score,
        emergency_reserve_score=reserve_score,
        expense_ratio_score=expense_ratio_score,
        total=total,
        status=status,
        strengths=strengths,
        risks=risks,
        recommendations=recs,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. Risk Indicators
# ─────────────────────────────────────────────────────────────────────────────

def compute_risk_indicators(
    available_capital: float,
    min_investment: float,
    expected: ScenarioResult,
    payback_months: Optional[float],
    emergency_reserve: float,
    monthly_expenses: float,
) -> List[RiskIndicator]:
    indicators: List[RiskIndicator] = []

    # Capital risk
    if available_capital < min_investment:
        gap = min_investment - available_capital
        indicators.append(RiskIndicator(
            name="Startup Capital",
            level="High",
            explanation=f"Capital is ₹{gap:,.0f} below the minimum investment of ₹{min_investment:,.0f}.",
        ))
    elif available_capital < min_investment * 1.2:
        indicators.append(RiskIndicator(
            name="Startup Capital",
            level="Medium",
            explanation="Capital barely covers the minimum investment. Little buffer for overruns.",
        ))
    else:
        indicators.append(RiskIndicator(
            name="Startup Capital",
            level="Low",
            explanation="Capital comfortably covers startup requirements.",
        ))

    # Profitability risk
    if expected.monthly_profit < 0:
        indicators.append(RiskIndicator(
            name="Profitability",
            level="High",
            explanation="Expected scenario projects a monthly loss. Review pricing and cost structure.",
        ))
    elif expected.profit_margin_pct < 10:
        indicators.append(RiskIndicator(
            name="Profitability",
            level="Medium",
            explanation=f"Profit margin is only {expected.profit_margin_pct:.1f}%. Any cost increase may turn the business unprofitable.",
        ))
    else:
        indicators.append(RiskIndicator(
            name="Profitability",
            level="Low",
            explanation=f"Profit margin of {expected.profit_margin_pct:.1f}% provides a reasonable buffer.",
        ))

    # Payback risk
    if payback_months is None:
        indicators.append(RiskIndicator(
            name="Payback Period",
            level="High",
            explanation="Cannot estimate payback — business does not project positive monthly profit.",
        ))
    elif payback_months > 36:
        indicators.append(RiskIndicator(
            name="Payback Period",
            level="High",
            explanation=f"Payback is {payback_months:.0f} months — capital tied up for a very long time.",
        ))
    elif payback_months > 18:
        indicators.append(RiskIndicator(
            name="Payback Period",
            level="Medium",
            explanation=f"Payback of {payback_months:.0f} months is acceptable but long.",
        ))
    else:
        indicators.append(RiskIndicator(
            name="Payback Period",
            level="Low",
            explanation=f"Payback in {payback_months:.0f} months is favourable.",
        ))

    # Emergency reserve risk
    reserve_months = (emergency_reserve / monthly_expenses) if monthly_expenses > 0 else 0
    if reserve_months < 1:
        indicators.append(RiskIndicator(
            name="Emergency Reserve",
            level="High",
            explanation="Reserve covers less than 1 month of expenses. Very vulnerable to disruptions.",
        ))
    elif reserve_months < 2:
        indicators.append(RiskIndicator(
            name="Emergency Reserve",
            level="Medium",
            explanation=f"Reserve covers {reserve_months:.1f} month(s). Aim for 3 months.",
        ))
    else:
        indicators.append(RiskIndicator(
            name="Emergency Reserve",
            level="Low",
            explanation=f"Reserve covers {reserve_months:.1f} months of expenses.",
        ))

    return indicators


# ─────────────────────────────────────────────────────────────────────────────
# 9. Full Analysis Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def full_analysis(
    business_id: str,
    business_name: str,
    available_capital: float,
    min_investment: float,
    max_investment: float,
    revenue_min: float,
    revenue_max: float,
    expense_min: float,
    expense_max: float,
    # Optional overrides
    emergency_reserve_pct: float = 0.125,
    working_capital_pct: float = 0.20,
    monthly_revenue_growth: float = 0.02,
    monthly_expense_growth: float = 0.005,
    fixed_cost_ratio: float = 0.55,
    variable_cost_ratio: Optional[float] = None,
) -> FullFinancialAnalysis:
    """Single entry point that runs all calculators and returns a complete analysis."""

    investment = plan_investment(
        available_capital=available_capital,
        min_investment=min_investment,
        max_investment=max_investment,
        emergency_reserve_pct=emergency_reserve_pct,
        working_capital_pct=working_capital_pct,
    )

    conservative, expected, optimistic = compute_all_scenarios(
        revenue_min, revenue_max, expense_min, expense_max
    )

    roi = compute_roi(expected.annual_profit, min_investment)
    payback_months, payback_ok, payback_note = compute_payback(min_investment, expected.monthly_profit)

    break_even = compute_break_even(
        monthly_expenses=expected.monthly_expenses,
        fixed_cost_ratio=fixed_cost_ratio,
        variable_cost_ratio=variable_cost_ratio,
    )

    cash_flow = project_cash_flow(
        initial_monthly_revenue=expected.monthly_revenue,
        initial_monthly_expenses=expected.monthly_expenses,
        monthly_revenue_growth_rate=monthly_revenue_growth,
        monthly_expense_growth_rate=monthly_expense_growth,
    )

    health = compute_health_score(
        available_capital=available_capital,
        min_investment=min_investment,
        expected=expected,
        roi_pct=roi,
        payback_months=payback_months,
        emergency_reserve=investment.emergency_reserve,
        monthly_expenses=expected.monthly_expenses,
    )

    risks = compute_risk_indicators(
        available_capital=available_capital,
        min_investment=min_investment,
        expected=expected,
        payback_months=payback_months,
        emergency_reserve=investment.emergency_reserve,
        monthly_expenses=expected.monthly_expenses,
    )

    return FullFinancialAnalysis(
        business_id=business_id,
        business_name=business_name,
        available_capital=available_capital,
        investment=investment,
        conservative=conservative,
        expected=expected,
        optimistic=optimistic,
        roi_pct=roi,
        payback_months=payback_months,
        payback_feasible=payback_ok,
        payback_note=payback_note,
        break_even=break_even,
        health=health,
        risks=risks,
        cash_flow=cash_flow,
    )
