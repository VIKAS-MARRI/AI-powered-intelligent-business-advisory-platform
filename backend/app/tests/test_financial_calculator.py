"""
Comprehensive unit tests for the financial calculator (Phase 3).
Run with: python -m pytest app/tests/test_financial_calculator.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import math
import pytest
from app.services.financial_calculator import (
    plan_investment,
    compute_scenario,
    compute_all_scenarios,
    compute_roi,
    compute_payback,
    compute_break_even,
    project_cash_flow,
    compute_health_score,
    compute_risk_indicators,
    full_analysis,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

TAILORING = dict(
    business_id="biz-001",
    business_name="Tailoring & Boutique",
    available_capital=200000,
    min_investment=15000,
    max_investment=60000,
    revenue_min=15000,
    revenue_max=40000,
    expense_min=4000,
    expense_max=12000,
)

DAIRY = dict(
    business_id="biz-002",
    business_name="Dairy Farming",
    available_capital=150000,
    min_investment=80000,
    max_investment=200000,
    revenue_min=25000,
    revenue_max=60000,
    expense_min=15000,
    expense_max=35000,
)

# Under-capitalised case
KIRANA_TIGHT = dict(
    business_id="biz-003",
    business_name="Kirana Store",
    available_capital=50000,    # min is 80000 — capital shortage!
    min_investment=80000,
    max_investment=250000,
    revenue_min=80000,
    revenue_max=200000,
    expense_min=65000,
    expense_max=170000,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Investment Planning
# ─────────────────────────────────────────────────────────────────────────────

class TestInvestmentPlanning:
    def test_total_never_exceeds_capital(self):
        inv = plan_investment(200000, 15000, 60000)
        assert inv.total_allocated <= inv.available_capital + 0.01  # allow ₹0.01 rounding

    def test_feasible_when_capital_exceeds_min(self):
        inv = plan_investment(200000, 15000, 60000)
        assert inv.is_feasible is True
        assert inv.funding_gap == 0.0

    def test_funding_gap_when_capital_insufficient(self):
        inv = plan_investment(50000, 80000, 250000)
        assert inv.is_feasible is False
        assert inv.funding_gap == pytest.approx(30000, abs=1)

    def test_zero_funding_gap_when_exactly_enough(self):
        inv = plan_investment(80000, 80000, 250000)
        assert inv.is_feasible is True
        assert inv.funding_gap == 0.0

    def test_emergency_reserve_present(self):
        inv = plan_investment(200000, 15000, 60000)
        assert inv.emergency_reserve > 0

    def test_emergency_reserve_respects_pct(self):
        inv = plan_investment(200000, 15000, 60000, emergency_reserve_pct=0.10)
        assert inv.emergency_reserve == pytest.approx(20000, rel=0.01)

    def test_all_categories_positive(self):
        inv = plan_investment(200000, 15000, 60000)
        assert inv.equipment          >= 0
        assert inv.initial_inventory  >= 0
        assert inv.business_setup     >= 0
        assert inv.licensing          >= 0
        assert inv.marketing          >= 0
        assert inv.working_capital    >= 0
        assert inv.emergency_reserve  >= 0

    def test_allocation_dict_keys(self):
        inv = plan_investment(100000, 20000, 80000)
        expected_keys = {"Equipment", "Initial Inventory", "Business Setup",
                         "Licensing / Other", "Marketing", "Working Capital", "Emergency Reserve"}
        assert set(inv.allocation_dict.keys()) == expected_keys

    def test_zero_capital_handled(self):
        inv = plan_investment(0, 50000, 100000)
        assert inv.total_allocated == pytest.approx(0, abs=1)
        assert inv.is_feasible is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Scenario Engine
# ─────────────────────────────────────────────────────────────────────────────

class TestScenarios:
    def test_conservative_lower_revenue_than_expected(self):
        cons = compute_scenario("Conservative", 15000, 40000, 4000, 12000)
        exp  = compute_scenario("Expected",     15000, 40000, 4000, 12000)
        assert cons.monthly_revenue < exp.monthly_revenue

    def test_optimistic_higher_revenue_than_expected(self):
        opt = compute_scenario("Optimistic", 15000, 40000, 4000, 12000)
        exp = compute_scenario("Expected",   15000, 40000, 4000, 12000)
        assert opt.monthly_revenue > exp.monthly_revenue

    def test_annual_revenue_is_12x_monthly(self):
        s = compute_scenario("Expected", 15000, 40000, 4000, 12000)
        assert s.annual_revenue == pytest.approx(s.monthly_revenue * 12, rel=0.001)

    def test_annual_profit_is_12x_monthly(self):
        s = compute_scenario("Expected", 15000, 40000, 4000, 12000)
        assert s.annual_profit == pytest.approx(s.monthly_profit * 12, rel=0.001)

    def test_profit_formula(self):
        s = compute_scenario("Expected", 15000, 40000, 4000, 12000)
        assert s.monthly_profit == pytest.approx(s.monthly_revenue - s.monthly_expenses, rel=0.001)

    def test_profit_margin_formula(self):
        s = compute_scenario("Expected", 15000, 40000, 4000, 12000)
        if s.monthly_revenue > 0:
            expected_margin = (s.monthly_profit / s.monthly_revenue) * 100
            assert s.profit_margin_pct == pytest.approx(expected_margin, rel=0.01)

    def test_all_three_scenarios(self):
        c, e, o = compute_all_scenarios(15000, 40000, 4000, 12000)
        assert c.name == "Conservative"
        assert e.name == "Expected"
        assert o.name == "Optimistic"
        assert c.monthly_revenue < e.monthly_revenue < o.monthly_revenue

    def test_zero_revenue_margin_is_zero(self):
        s = compute_scenario("Expected", 0, 0, 1000, 2000)
        assert s.profit_margin_pct == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. ROI
# ─────────────────────────────────────────────────────────────────────────────

class TestROI:
    def test_basic_roi(self):
        # Annual profit ₹1,80,000 on ₹60,000 → 300%
        roi = compute_roi(180000, 60000)
        assert roi == pytest.approx(300.0, rel=0.01)

    def test_zero_investment_returns_zero(self):
        assert compute_roi(50000, 0) == 0.0

    def test_negative_investment_returns_zero(self):
        assert compute_roi(50000, -10000) == 0.0

    def test_negative_profit_gives_negative_roi(self):
        roi = compute_roi(-24000, 60000)
        assert roi < 0

    def test_zero_profit_gives_zero_roi(self):
        assert compute_roi(0, 60000) == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Payback Period
# ─────────────────────────────────────────────────────────────────────────────

class TestPayback:
    def test_basic_payback(self):
        months, ok, note = compute_payback(60000, 5000)
        assert ok is True
        assert months == pytest.approx(12.0, rel=0.01)

    def test_zero_profit(self):
        months, ok, note = compute_payback(60000, 0)
        assert ok is False
        assert months is None
        assert "zero" in note.lower()

    def test_negative_profit(self):
        months, ok, note = compute_payback(60000, -1000)
        assert ok is False
        assert months is None
        assert "los" in note.lower()

    def test_zero_investment(self):
        months, ok, note = compute_payback(0, 5000)
        assert ok is True
        assert months == 0.0

    def test_large_investment_long_payback(self):
        months, ok, note = compute_payback(500000, 5000)
        assert ok is True
        assert months == pytest.approx(100.0, rel=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Break-Even
# ─────────────────────────────────────────────────────────────────────────────

class TestBreakEven:
    def test_basic_break_even(self):
        # When variable_cost_ratio is NOT given, it is auto-derived as 1 - fixed_cost_ratio
        # fixed_costs = 10000 * 0.55 = 5500
        # variable_cost_ratio = 1 - 0.55 = 0.45
        # contribution_margin = 1 - 0.45 = 0.55
        # break_even = 5500 / 0.55 = 10000
        be = compute_break_even(monthly_expenses=10000, fixed_cost_ratio=0.55)
        assert be.fixed_costs_monthly == pytest.approx(5500, rel=0.01)
        expected_be = 5500 / 0.55   # CM = 1 - (1-0.55) = 0.55
        assert be.break_even_revenue == pytest.approx(expected_be, rel=0.01)

    def test_assumed_flag_when_no_variable_cost(self):
        be = compute_break_even(10000)
        assert be.assumed is True

    def test_explicit_variable_cost_not_assumed(self):
        be = compute_break_even(10000, variable_cost_ratio=0.40)
        assert be.assumed is False

    def test_variable_cost_clamped(self):
        be = compute_break_even(10000, variable_cost_ratio=0.0)   # should clamp to 0.01
        assert be.variable_cost_ratio >= 0.01

    def test_contribution_margin_complement(self):
        be = compute_break_even(10000, variable_cost_ratio=0.40)
        assert be.contribution_margin_ratio == pytest.approx(0.60, rel=0.01)

    def test_break_even_formula(self):
        be = compute_break_even(20000, variable_cost_ratio=0.50)
        fc = 20000 * 0.55
        cm = 1 - 0.50
        expected = fc / cm
        assert be.break_even_revenue == pytest.approx(expected, rel=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Cash Flow Projection
# ─────────────────────────────────────────────────────────────────────────────

class TestCashFlow:
    def test_returns_12_months(self):
        cf = project_cash_flow(30000, 15000)
        assert len(cf) == 12

    def test_custom_month_count(self):
        cf = project_cash_flow(30000, 15000, months=6)
        assert len(cf) == 6

    def test_month_numbers_sequential(self):
        cf = project_cash_flow(30000, 15000)
        for i, m in enumerate(cf, start=1):
            assert m.month == i

    def test_profit_formula_each_month(self):
        cf = project_cash_flow(30000, 15000, monthly_revenue_growth_rate=0, monthly_expense_growth_rate=0)
        for m in cf:
            assert m.profit == pytest.approx(m.revenue - m.expenses, abs=0.1)

    def test_cumulative_is_running_sum(self):
        cf = project_cash_flow(30000, 15000, monthly_revenue_growth_rate=0, monthly_expense_growth_rate=0)
        running = 0.0
        for m in cf:
            running += m.profit
            assert m.cumulative_cash_flow == pytest.approx(running, abs=1)

    def test_revenue_grows_over_time(self):
        cf = project_cash_flow(30000, 15000, monthly_revenue_growth_rate=0.05, monthly_expense_growth_rate=0)
        # After ramp-up months (default 2), revenue should be increasing
        assert cf[2].revenue < cf[11].revenue

    def test_ramp_up_lowers_early_revenue(self):
        cf_ramp    = project_cash_flow(30000, 15000, ramp_up_months=2, ramp_up_factor=0.70)
        cf_no_ramp = project_cash_flow(30000, 15000, ramp_up_months=0)
        assert cf_ramp[0].revenue < cf_no_ramp[0].revenue

    def test_zero_growth_flat_revenue(self):
        cf = project_cash_flow(30000, 15000, monthly_revenue_growth_rate=0, monthly_expense_growth_rate=0, ramp_up_months=0)
        revenues = [m.revenue for m in cf]
        assert all(abs(r - revenues[0]) < 0.1 for r in revenues)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Financial Health Score
# ─────────────────────────────────────────────────────────────────────────────

def _mock_expected(revenue=30000, expenses=12000):
    from types import SimpleNamespace
    profit = revenue - expenses
    margin = (profit / revenue * 100) if revenue > 0 else 0
    return SimpleNamespace(
        monthly_revenue=revenue,
        monthly_expenses=expenses,
        monthly_profit=profit,
        profit_margin_pct=margin,
        annual_profit=profit * 12,
    )


class TestHealthScore:
    def test_strong_business_scores_high(self):
        e = _mock_expected(40000, 10000)  # 75% margin
        h = compute_health_score(200000, 15000, e, roi_pct=90, payback_months=8,
                                  emergency_reserve=25000, monthly_expenses=10000)
        assert h.total >= 70
        assert h.status in ("Excellent", "Good")

    def test_weak_business_scores_low(self):
        e = _mock_expected(10000, 12000)  # loss
        h = compute_health_score(30000, 80000, e, roi_pct=-20, payback_months=None,
                                  emergency_reserve=1000, monthly_expenses=12000)
        assert h.total < 40
        assert h.status in ("Fair", "Needs Attention")

    def test_score_in_range(self):
        e = _mock_expected(30000, 20000)
        h = compute_health_score(100000, 50000, e, roi_pct=20, payback_months=24,
                                  emergency_reserve=10000, monthly_expenses=20000)
        assert 0 <= h.total <= 100

    def test_has_strengths_and_risks_lists(self):
        e = _mock_expected(30000, 20000)
        h = compute_health_score(100000, 50000, e, roi_pct=20, payback_months=24,
                                  emergency_reserve=10000, monthly_expenses=20000)
        assert isinstance(h.strengths, list)
        assert isinstance(h.risks, list)
        assert isinstance(h.recommendations, list)

    def test_insufficient_capital_gives_low_budget_score(self):
        e = _mock_expected(30000, 20000)
        h = compute_health_score(10000, 80000, e, roi_pct=10, payback_months=12,
                                  emergency_reserve=500, monthly_expenses=20000)
        assert h.budget_sufficiency == 0.0

    def test_payback_none_gives_zero_payback_score(self):
        e = _mock_expected(10000, 12000)  # loss → payback None
        h = compute_health_score(100000, 50000, e, roi_pct=-10, payback_months=None,
                                  emergency_reserve=10000, monthly_expenses=12000)
        assert h.payback_score == 0.0

    def test_excellent_status_threshold(self):
        e = _mock_expected(50000, 10000)  # 80% margin
        h = compute_health_score(500000, 15000, e, roi_pct=200, payback_months=3,
                                  emergency_reserve=100000, monthly_expenses=10000)
        assert h.status == "Excellent"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Risk Indicators
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskIndicators:
    def _expected(self, revenue=30000, expenses=12000):
        return _mock_expected(revenue, expenses)

    def test_returns_four_indicators(self):
        e = self._expected()
        risks = compute_risk_indicators(200000, 50000, e, 12, 25000, 12000)
        assert len(risks) == 4

    def test_capital_shortfall_is_high_risk(self):
        e = self._expected()
        risks = compute_risk_indicators(20000, 80000, e, 12, 1000, 12000)
        cap_risk = next(r for r in risks if r.name == "Startup Capital")
        assert cap_risk.level == "High"

    def test_capital_surplus_is_low_risk(self):
        e = self._expected()
        risks = compute_risk_indicators(200000, 50000, e, 12, 25000, 12000)
        cap_risk = next(r for r in risks if r.name == "Startup Capital")
        assert cap_risk.level == "Low"

    def test_loss_making_is_high_profitability_risk(self):
        e = self._expected(5000, 12000)  # loss
        risks = compute_risk_indicators(100000, 50000, e, None, 10000, 12000)
        prof_risk = next(r for r in risks if r.name == "Profitability")
        assert prof_risk.level == "High"

    def test_no_reserve_is_high_risk(self):
        e = self._expected()
        risks = compute_risk_indicators(100000, 50000, e, 12, 500, 12000)
        res_risk = next(r for r in risks if r.name == "Emergency Reserve")
        assert res_risk.level == "High"

    def test_all_levels_valid(self):
        e = self._expected()
        risks = compute_risk_indicators(200000, 80000, e, 24, 20000, 12000)
        for r in risks:
            assert r.level in ("Low", "Medium", "High")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Full Analysis Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class TestFullAnalysis:
    def test_tailoring_analysis(self):
        result = full_analysis(**TAILORING)
        assert result.business_id == "biz-001"
        assert result.expected.monthly_profit > 0
        assert 0 <= result.health.total <= 100
        assert len(result.cash_flow) == 12
        assert result.investment.is_feasible is True

    def test_dairy_analysis_feasible(self):
        """Dairy: capital=150k >= min=80k, so no funding gap."""
        result = full_analysis(**DAIRY)
        assert result.business_id == "biz-002"
        assert result.investment.is_feasible is True
        assert result.investment.funding_gap == 0.0

    def test_dairy_insufficient_when_capital_too_low(self):
        """Dairy with capital below minimum should show a gap."""
        low_cap = {**DAIRY, "available_capital": 40000}
        result = full_analysis(**low_cap)
        assert result.investment.is_feasible is False
        assert result.investment.funding_gap == pytest.approx(40000, abs=1)

    def test_kirana_insufficient_capital(self):
        result = full_analysis(**KIRANA_TIGHT)
        assert result.investment.is_feasible is False
        assert result.investment.funding_gap == pytest.approx(30000, abs=1)

    def test_disclaimer_present(self):
        result = full_analysis(**TAILORING)
        assert "estimate" in result.disclaimer.lower()

    def test_all_three_scenarios_present(self):
        result = full_analysis(**TAILORING)
        assert result.conservative.name == "Conservative"
        assert result.expected.name     == "Expected"
        assert result.optimistic.name   == "Optimistic"

    def test_optimistic_beats_conservative(self):
        result = full_analysis(**TAILORING)
        assert result.optimistic.monthly_profit > result.conservative.monthly_profit

    def test_roi_non_negative_for_profitable_business(self):
        result = full_analysis(**TAILORING)
        # Tailoring is highly profitable → ROI should be positive
        assert result.roi_pct > 0

    def test_twelve_month_cash_flow(self):
        result = full_analysis(**TAILORING)
        assert len(result.cash_flow) == 12

    def test_risk_indicators_present(self):
        result = full_analysis(**TAILORING)
        assert len(result.risks) == 4
