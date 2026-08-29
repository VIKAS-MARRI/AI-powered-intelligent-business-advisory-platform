"""
Comprehensive unit tests for Phase 4 Investment Optimizer.
Run with: python -m pytest app/tests/test_investment_optimizer.py -v

Tests cover:
  - Budget constraints (total ≤ available capital)
  - Minimum requirement enforcement
  - Insufficient capital detection
  - Strategy ordering (conservative vs balanced vs growth)
  - Edge cases (zero, negative, very low, very high capital)
  - Custom constraints
  - OR-Tools determinism
  - Single-strategy mode
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from app.services.investment_optimizer import (
    optimize_investment,
    optimize_single_strategy,
    _build_specs,
    _compute_minimum_required,
    _solve_one,
    IDX_RESERVE,
    IDX_WORKING,
    IDX_EQUIPMENT,
    IDX_MARKETING,
    CATEGORY_NAMES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

TAILORING = dict(
    business_id   = "biz-t01",
    business_name = "Tailoring & Boutique",
    available_capital = 200_000,
    min_investment    = 15_000,
    max_investment    = 60_000,
)

DAIRY = dict(
    business_id   = "biz-d01",
    business_name = "Dairy Farming",
    available_capital = 150_000,
    min_investment    = 80_000,
    max_investment    = 200_000,
)

KIRANA_TIGHT = dict(
    business_id   = "biz-k01",
    business_name = "Kirana Store",
    available_capital = 5_000,       # very low — insufficient
    min_investment    = 80_000,
    max_investment    = 250_000,
)


# ─────────────────────────────────────────────────────────────────────────────
# TestBudgetConstraints
# ─────────────────────────────────────────────────────────────────────────────

class TestBudgetConstraints:
    """Total allocation must never exceed available capital."""

    def test_total_never_exceeds_capital_tailoring(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert s.total_allocated <= TAILORING["available_capital"] + 1, (
                f"{s.name}: allocated {s.total_allocated} > capital {TAILORING['available_capital']}"
            )

    def test_total_never_exceeds_capital_dairy(self):
        res = optimize_investment(**DAIRY)
        for s in res.strategies:
            assert s.total_allocated <= DAIRY["available_capital"] + 1

    def test_remaining_capital_non_negative(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert s.remaining_capital >= -1, f"{s.name} remaining {s.remaining_capital} < 0"

    def test_remaining_equals_capital_minus_allocated(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            expected = TAILORING["available_capital"] - s.total_allocated
            assert abs(s.remaining_capital - expected) < 2, (
                f"{s.name}: remaining mismatch"
            )

    def test_all_allocations_non_negative(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            for a in s.allocations:
                assert a.allocated >= 0, f"{s.name}/{a.name}: negative allocation"

    def test_allocation_dict_matches_list(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            for a in s.allocations:
                assert abs(s.allocation_dict[a.name] - a.allocated) < 1


# ─────────────────────────────────────────────────────────────────────────────
# TestMinimumRequirements
# ─────────────────────────────────────────────────────────────────────────────

class TestMinimumRequirements:
    """Each category allocation ≥ its minimum when capital is sufficient."""

    def test_minimums_respected_tailoring(self):
        specs = _build_specs(
            available_capital = TAILORING["available_capital"],
            min_investment    = TAILORING["min_investment"],
            max_investment    = TAILORING["max_investment"],
        )
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            for a, spec in zip(s.allocations, specs):
                assert a.allocated >= spec.minimum - 1, (
                    f"{s.name}/{a.name}: {a.allocated} < min {spec.minimum}"
                )

    def test_minimums_respected_dairy(self):
        specs = _build_specs(
            available_capital = DAIRY["available_capital"],
            min_investment    = DAIRY["min_investment"],
            max_investment    = DAIRY["max_investment"],
        )
        res = optimize_investment(**DAIRY)
        for s in res.strategies:
            for a, spec in zip(s.allocations, specs):
                assert a.allocated >= spec.minimum - 1


# ─────────────────────────────────────────────────────────────────────────────
# TestInsufficientCapital
# ─────────────────────────────────────────────────────────────────────────────

class TestInsufficientCapital:
    """Correctly detect and report under-funded scenarios."""

    def test_status_is_insufficient(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert res.status == "insufficient_capital"

    def test_no_strategies_returned_when_insufficient(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert res.strategies == []

    def test_funding_gap_positive(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert res.funding_gap > 0

    def test_insufficient_info_present(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert res.insufficient_info is not None
        assert res.insufficient_info.funding_gap > 0

    def test_suggestions_provided(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert len(res.insufficient_info.suggestions) >= 3

    def test_available_capital_returned_correctly(self):
        res = optimize_investment(**KIRANA_TIGHT)
        assert res.available_capital == KIRANA_TIGHT["available_capital"]

    def test_zero_capital_is_insufficient(self):
        res = optimize_investment(
            business_id="biz-x", business_name="Test",
            available_capital=1,   # gt=0 in schema but here we test service directly
            min_investment=50_000, max_investment=100_000,
        )
        assert res.status == "insufficient_capital"

    def test_exact_minimum_capital_is_feasible(self):
        """If available capital == minimum required, status should be optimal."""
        specs = _build_specs(
            available_capital=200_000,
            min_investment=15_000,
            max_investment=60_000,
        )
        min_req = _compute_minimum_required(specs)
        res = optimize_investment(
            business_id="biz-x", business_name="Test",
            available_capital=min_req,
            min_investment=15_000, max_investment=60_000,
        )
        assert res.status == "optimal"


# ─────────────────────────────────────────────────────────────────────────────
# TestStrategies
# ─────────────────────────────────────────────────────────────────────────────

class TestStrategies:
    """Verify that strategy priorities produce the expected relative allocations."""

    def _get(self, strategy_name: str, cat_idx: int) -> float:
        res = optimize_investment(**TAILORING)
        s = next(s for s in res.strategies if s.name == strategy_name)
        return s.allocations[cat_idx].allocated

    def test_three_strategies_returned(self):
        res = optimize_investment(**TAILORING)
        assert len(res.strategies) == 3
        names = {s.name for s in res.strategies}
        assert names == {"conservative", "balanced", "growth"}

    def test_conservative_has_higher_reserve_than_growth(self):
        cons_reserve  = self._get("conservative", IDX_RESERVE)
        growth_reserve = self._get("growth",       IDX_RESERVE)
        assert cons_reserve >= growth_reserve, (
            f"Conservative reserve ({cons_reserve}) should be >= Growth reserve ({growth_reserve})"
        )

    def test_growth_has_higher_equipment_than_conservative(self):
        growth_equip = self._get("growth",       IDX_EQUIPMENT)
        cons_equip   = self._get("conservative", IDX_EQUIPMENT)
        assert growth_equip >= cons_equip

    def test_growth_has_higher_marketing_than_conservative(self):
        growth_mkt = self._get("growth",       IDX_MARKETING)
        cons_mkt   = self._get("conservative", IDX_MARKETING)
        assert growth_mkt >= cons_mkt

    def test_conservative_has_higher_working_capital_than_growth(self):
        cons_wc  = self._get("conservative", IDX_WORKING)
        growth_wc = self._get("growth",      IDX_WORKING)
        assert cons_wc >= growth_wc

    def test_risk_level_ordering(self):
        res = optimize_investment(**TAILORING)
        risk_map = {s.name: s.risk_level for s in res.strategies}
        # conservative ≤ balanced ≤ growth in risk
        order = {"Low": 0, "Medium": 1, "High": 2}
        assert order[risk_map["conservative"]] <= order[risk_map["balanced"]]
        assert order[risk_map["balanced"]]     <= order[risk_map["growth"]]

    def test_optimization_score_in_range(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert 0 <= s.optimization_score <= 100, (
                f"{s.name} score {s.optimization_score} out of range"
            )

    def test_all_strategies_have_explanations(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert len(s.explanations) >= 3

    def test_all_strategies_have_tradeoffs(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert len(s.tradeoffs) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# TestRecommendedStrategy
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendedStrategy:
    def test_default_recommended_is_balanced(self):
        res = optimize_investment(**TAILORING)
        assert res.recommended_strategy == "balanced"

    def test_risk_preference_conservative(self):
        res = optimize_investment(**TAILORING, risk_preference="conservative")
        assert res.recommended_strategy == "conservative"

    def test_risk_preference_growth(self):
        res = optimize_investment(**TAILORING, risk_preference="growth")
        assert res.recommended_strategy == "growth"

    def test_invalid_preference_defaults_to_balanced(self):
        res = optimize_investment(**TAILORING, risk_preference="invalid_xyz")
        assert res.recommended_strategy == "balanced"


# ─────────────────────────────────────────────────────────────────────────────
# TestCustomConstraints
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomConstraints:
    def test_min_emergency_reserve_respected(self):
        min_res = 30_000.0
        res = optimize_investment(**TAILORING, min_emergency_reserve=min_res)
        for s in res.strategies:
            reserve = s.allocations[IDX_RESERVE].allocated
            assert reserve >= min_res - 1, (
                f"{s.name}: reserve {reserve} < min {min_res}"
            )

    def test_min_working_capital_respected(self):
        min_wc = 40_000.0
        res = optimize_investment(**TAILORING, min_working_capital=min_wc)
        for s in res.strategies:
            wc = s.allocations[IDX_WORKING].allocated
            assert wc >= min_wc - 1, (
                f"{s.name}: working_capital {wc} < min {min_wc}"
            )

    def test_max_marketing_budget_respected(self):
        max_mkt = 5_000.0
        res = optimize_investment(**TAILORING, max_marketing_budget=max_mkt)
        for s in res.strategies:
            mkt = s.allocations[IDX_MARKETING].allocated
            assert mkt <= max_mkt + 1, (
                f"{s.name}: marketing {mkt} > max {max_mkt}"
            )

    def test_combined_constraints(self):
        res = optimize_investment(
            **TAILORING,
            min_emergency_reserve = 20_000,
            min_working_capital   = 30_000,
            max_marketing_budget  = 10_000,
        )
        assert res.status == "optimal"
        for s in res.strategies:
            assert s.allocations[IDX_RESERVE].allocated  >= 19_999
            assert s.allocations[IDX_WORKING].allocated  >= 29_999
            assert s.allocations[IDX_MARKETING].allocated <= 10_001


# ─────────────────────────────────────────────────────────────────────────────
# TestEdgeCases
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_very_high_capital(self):
        """With very high capital all strategies should be optimal."""
        res = optimize_investment(
            business_id="biz-x", business_name="X",
            available_capital=10_000_000,
            min_investment=50_000, max_investment=200_000,
        )
        assert res.status == "optimal"
        assert len(res.strategies) == 3

    def test_capital_exactly_zero_is_insufficient(self):
        # Service receives 0 — service must detect it
        res = optimize_investment(
            business_id="biz-x", business_name="X",
            available_capital=0.01,  # smallest positive
            min_investment=50_000, max_investment=100_000,
        )
        assert res.status == "insufficient_capital"

    def test_equal_min_max_investment(self):
        """min == max investment should not crash."""
        res = optimize_investment(
            business_id="biz-x", business_name="X",
            available_capital=500_000,
            min_investment=100_000, max_investment=100_000,
        )
        assert res.status == "optimal"

    def test_very_low_capital_below_minimum(self):
        res = optimize_investment(
            business_id="biz-x", business_name="X",
            available_capital=100,
            min_investment=50_000, max_investment=100_000,
        )
        assert res.status == "insufficient_capital"
        assert res.funding_gap > 0


# ─────────────────────────────────────────────────────────────────────────────
# TestDeterminism (OR-Tools reproducibility)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminism:
    """Same input must always produce the same output."""

    def test_results_are_deterministic(self):
        res1 = optimize_investment(**TAILORING)
        res2 = optimize_investment(**TAILORING)
        for s1, s2 in zip(res1.strategies, res2.strategies):
            assert s1.name == s2.name
            assert abs(s1.total_allocated - s2.total_allocated) < 1
            for a1, a2 in zip(s1.allocations, s2.allocations):
                assert abs(a1.allocated - a2.allocated) < 1

    def test_dairy_deterministic(self):
        res1 = optimize_investment(**DAIRY)
        res2 = optimize_investment(**DAIRY)
        for s1, s2 in zip(res1.strategies, res2.strategies):
            assert abs(s1.total_allocated - s2.total_allocated) < 1

    def test_solver_direct_determinism(self):
        specs = _build_specs(200_000, 15_000, 60_000)
        allocs1 = _solve_one("balanced", 200_000, specs)
        allocs2 = _solve_one("balanced", 200_000, specs)
        assert allocs1 is not None
        assert allocs2 is not None
        for a1, a2 in zip(allocs1, allocs2):
            assert abs(a1 - a2) < 1


# ─────────────────────────────────────────────────────────────────────────────
# TestSingleStrategy
# ─────────────────────────────────────────────────────────────────────────────

class TestSingleStrategy:
    """optimize_single_strategy returns only the requested strategy."""

    def test_single_conservative(self):
        res = optimize_single_strategy(**TAILORING, strategy="conservative")
        # All three strategies are still returned (optimize_investment is called with
        # risk_preference, so full result comes back — but recommended matches)
        assert res.recommended_strategy == "conservative"

    def test_single_growth(self):
        res = optimize_single_strategy(**TAILORING, strategy="growth")
        assert res.recommended_strategy == "growth"

    def test_invalid_strategy_defaults_balanced(self):
        res = optimize_single_strategy(**TAILORING, strategy="xyz")
        assert res.recommended_strategy == "balanced"

    def test_insufficient_capital_single(self):
        res = optimize_single_strategy(**KIRANA_TIGHT, strategy="balanced")
        assert res.status == "insufficient_capital"


# ─────────────────────────────────────────────────────────────────────────────
# TestCategoryCount
# ─────────────────────────────────────────────────────────────────────────────

class TestCategoryCount:
    def test_seven_categories_in_result(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert len(s.allocations) == len(CATEGORY_NAMES) == 7

    def test_seven_entries_in_allocation_dict(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            assert len(s.allocation_dict) == 7

    def test_pct_of_total_sums_to_100(self):
        res = optimize_investment(**TAILORING)
        for s in res.strategies:
            total_pct = sum(a.pct_of_total for a in s.allocations)
            assert abs(total_pct - 100.0) < 1.0, (
                f"{s.name} pct sum {total_pct} ≠ 100"
            )


# ─────────────────────────────────────────────────────────────────────────────
# TestORToolsImport
# ─────────────────────────────────────────────────────────────────────────────

class TestORToolsImport:
    """Verify OR-Tools is installed and functional."""

    def test_ortools_import(self):
        from ortools.sat.python import cp_model  # noqa: F401
        assert True

    def test_cpsat_solver_creates_model(self):
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        x = model.new_int_var(0, 100, "x")
        model.maximize(x)
        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert status == cp_model.OPTIMAL
        assert solver.value(x) == 100

    def test_solver_returns_valid_solution(self):
        specs = _build_specs(200_000, 15_000, 60_000)
        allocs = _solve_one("balanced", 200_000, specs)
        assert allocs is not None
        assert len(allocs) == 7
        assert sum(allocs) <= 200_001   # ≤ available capital
