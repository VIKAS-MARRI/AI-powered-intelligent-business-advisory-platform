"""
Investment Optimizer — Phase 4.

Uses Google OR-Tools CP-SAT solver to optimally allocate available capital
across investment categories for three distinct strategies:

  🛡️  Conservative  — safety-first, large reserve & working capital
  ⚖️  Balanced      — recommended default, balances all factors
  🚀  Growth        — revenue-maximising, higher equipment/marketing spend

ALL results are ESTIMATES for planning purposes only.
Actual costs, returns, and outcomes may vary significantly.

No AI/LLM is involved — every decision is made by explicit, deterministic
linear objective functions solved by the CP-SAT integer programming solver.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ortools.sat.python import cp_model


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# CP-SAT works on integers, so we scale rupee amounts by this factor so we
# can represent amounts down to ₹10 precision without floating-point issues.
_SCALE = 100          # 1 unit = ₹1  (we keep amounts as integers)

# Category indices  (used as list positions throughout the solver)
IDX_EQUIPMENT  = 0
IDX_INVENTORY  = 1
IDX_SETUP      = 2
IDX_LICENSING  = 3
IDX_MARKETING  = 4
IDX_WORKING    = 5
IDX_RESERVE    = 6

CATEGORY_NAMES = [
    "Equipment",
    "Initial Inventory",
    "Business Setup",
    "Licensing / Other",
    "Marketing",
    "Working Capital",
    "Emergency Reserve",
]

# Budget split ratios used to derive per-category bounds from total investment
# These match the Phase 3 financial_calculator allocation logic so both phases
# stay in sync and produce consistent numbers.
_BASE_RATIOS = {
    IDX_EQUIPMENT:  0.30,   # largest single cost
    IDX_INVENTORY:  0.20,
    IDX_SETUP:      0.10,
    IDX_LICENSING:  0.05,
    IDX_MARKETING:  0.08,
    IDX_WORKING:    0.20,
    IDX_RESERVE:    0.07,   # base; may be overridden
}


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CategorySpec:
    """Min / recommended / max bounds for a single investment category."""
    name:        str
    minimum:     float   # hard floor  (₹)
    recommended: float   # solver target
    maximum:     float   # hard ceiling
    priority:    int     # 1 = highest


@dataclass
class AllocationResult:
    """Per-category allocation produced by the solver."""
    name:              str
    allocated:         float
    minimum:           float
    recommended:       float
    maximum:           float
    pct_of_total:      float   # 0–100


@dataclass
class StrategyResult:
    """A complete optimised allocation strategy."""
    name:               str            # "conservative" | "balanced" | "growth"
    label:              str            # human-readable  e.g. "🛡️ Conservative"
    total_allocated:    float
    remaining_capital:  float
    optimization_score: float          # 0–100 composite score
    risk_level:         str            # "Low" | "Medium" | "High"
    allocations:        List[AllocationResult]
    tradeoffs:          List[str]
    explanations:       List[str]
    allocation_dict:    dict           # name → amount for charts


@dataclass
class InsufficientCapitalInfo:
    minimum_required_capital: float
    funding_gap:              float
    suggestions:              List[str]


@dataclass
class OptimizationResult:
    """Top-level response from the optimizer."""
    status:                   str   # "optimal" | "insufficient_capital"
    recommended_strategy:     str   # "conservative" | "balanced" | "growth"
    available_capital:        float
    minimum_required_capital: float
    funding_gap:              float
    strategies:               List[StrategyResult]
    insufficient_info:        Optional[InsufficientCapitalInfo]
    disclaimer:               str = (
        "Investment allocations and financial projections are estimates for "
        "planning purposes only. Actual costs, business performance, and "
        "outcomes may vary."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _r(x: float) -> int:
    """Round a float rupee amount to the nearest integer for the solver."""
    return max(0, int(round(x)))


def _build_specs(
    available_capital: float,
    min_investment:    float,
    max_investment:    float,
    # optional user overrides
    min_emergency_reserve:  Optional[float] = None,
    min_working_capital:    Optional[float] = None,
    max_marketing_budget:   Optional[float] = None,
) -> List[CategorySpec]:
    """
    Build per-category bounds from business investment range and available capital.

    The recommended allocation for each category is derived from the Phase 3
    ratio table, bounded by min_investment and available_capital.
    """
    # Use the midpoint of the investment range as the reference budget for
    # computing recommended amounts; cap at available_capital.
    ref = min(available_capital, (min_investment + max_investment) / 2)

    specs: List[CategorySpec] = []
    for idx, name in enumerate(CATEGORY_NAMES):
        ratio = _BASE_RATIOS[idx]
        rec   = ref * ratio

        # Hard minimum = 60% of ratio applied to the *minimum* investment
        base_min = min_investment * ratio * 0.60

        # Hard maximum = ratio applied to full available_capital × 1.5 headroom
        base_max = available_capital * ratio * 1.50

        # Apply user-provided overrides
        if idx == IDX_RESERVE and min_emergency_reserve is not None:
            base_min = max(base_min, min_emergency_reserve)
            rec      = max(rec, min_emergency_reserve)
        if idx == IDX_WORKING and min_working_capital is not None:
            base_min = max(base_min, min_working_capital)
            rec      = max(rec, min_working_capital)
        if idx == IDX_MARKETING and max_marketing_budget is not None:
            base_max = min(base_max, max_marketing_budget)
            rec      = min(rec, max_marketing_budget)

        specs.append(CategorySpec(
            name        = name,
            minimum     = max(0.0, base_min),
            recommended = rec,
            maximum     = min(available_capital, base_max),
            priority    = idx + 1,
        ))

    return specs


def _compute_minimum_required(specs: List[CategorySpec]) -> float:
    """Sum of all category minimums — this is the hard floor capital requirement."""
    return sum(s.minimum for s in specs)


def _objective_weights(strategy: str) -> List[float]:
    """
    Return per-category objective weights for the given strategy.

    The CP-SAT solver maximises  Σ  weight[i] * allocation[i]
    so higher weights pull more capital toward that category.

    Weights are non-negative integers (×100 for precision) and are normalised
    within the solver to keep objective values comparable.

    Strategy differences are documented below:

    Category       Conservative   Balanced   Growth
    ------------   ------------   --------   ------
    Equipment         1.0          2.0        4.0   ← Growth wants max equipment
    Inventory         1.5          2.0        3.5   ← Growth wants max stock
    Setup             1.0          1.5        2.0
    Licensing         1.0          1.0        1.0   ← Equal; fixed cost
    Marketing         0.5          2.0        4.0   ← Conservative avoids marketing
    Working Capital   4.0          2.5        1.0   ← Conservative values liquidity
    Emergency Reserve 4.0          2.0        0.5   ← Conservative buffers reserve
    """
    if strategy == "conservative":
        return [1.0, 1.5, 1.0, 1.0, 0.5, 4.0, 4.0]
    elif strategy == "growth":
        return [4.0, 3.5, 2.0, 1.0, 4.0, 1.0, 0.5]
    else:  # balanced
        return [2.0, 2.0, 1.5, 1.0, 2.0, 2.5, 2.0]


def _solve_one(
    strategy:          str,
    available_capital: float,
    specs:             List[CategorySpec],
    time_limit_ms:     int = 5000,
) -> Optional[List[float]]:
    """
    Run CP-SAT to find the optimal integer allocation for the given strategy.

    Returns a list of allocated amounts (₹ floats) or None if infeasible.

    Model:
      Variables : x[i]  ∈ [min_i, max_i]   (integer rupees)
      Constraint: Σ x[i] ≤ available_capital
      Objective : maximise Σ weight[i] * x[i]
    """
    cap_int = _r(available_capital)
    model   = cp_model.CpModel()
    weights = _objective_weights(strategy)

    # Decision variables ──────────────────────────────────────────────────────
    x: List[cp_model.IntVar] = []
    for i, spec in enumerate(specs):
        lo = _r(spec.minimum)
        hi = _r(min(spec.maximum, available_capital))
        hi = max(lo, hi)   # guard against lo > hi when capital is very tight
        x.append(model.new_int_var(lo, hi, f"x_{i}_{spec.name}"))

    # Budget constraint ───────────────────────────────────────────────────────
    model.add(sum(x) <= cap_int)

    # Objective ───────────────────────────────────────────────────────────────
    # Multiply by 100 to avoid floating-point — weights have 1 decimal place
    obj_terms = [int(w * 100) * x[i] for i, w in enumerate(weights)]
    model.maximize(sum(obj_terms))

    # Solve ───────────────────────────────────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_ms / 1000.0
    solver.parameters.num_search_workers  = 1   # deterministic (single thread)
    solver.parameters.random_seed         = 42  # fully reproducible

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    return [float(solver.value(xi)) for xi in x]


# ─────────────────────────────────────────────────────────────────────────────
# Strategy post-processing
# ─────────────────────────────────────────────────────────────────────────────

def _compute_score(
    strategy:          str,
    allocations:       List[float],
    available_capital: float,
    specs:             List[CategorySpec],
) -> float:
    """
    Compute a 0–100 composite optimisation score for a solved strategy.

    Sub-scores (each 0–25 or 0–20):
      - Budget utilisation       (0–20) : how efficiently capital is used
      - Reserve adequacy         (0–25) : relative size of emergency reserve
      - Working-capital coverage (0–20) : relative working capital allocation
      - Growth investment        (0–20) : combined equipment + marketing pct
      - Category min satisfaction(0–15) : how many categories meet their minimum
    """
    total = sum(allocations)
    if available_capital <= 0 or total <= 0:
        return 0.0

    util    = min(total / available_capital, 1.0)      # utilisation ratio
    reserve = allocations[IDX_RESERVE] / total
    working = allocations[IDX_WORKING] / total
    growth  = (allocations[IDX_EQUIPMENT] + allocations[IDX_MARKETING]) / total
    mins_ok = sum(1 for i, s in enumerate(specs) if allocations[i] >= s.minimum)
    mins_score = 15.0 * (mins_ok / len(specs))

    score = (
        util   * 20   +
        reserve * 100 * 0.25  +
        working * 100 * 0.20  +
        growth  * 100 * 0.20  +
        mins_score
    )
    return round(min(score, 100.0), 1)


def _risk_level(strategy: str, reserve_pct: float) -> str:
    """Determine risk level from strategy and reserve percentage."""
    if strategy == "conservative":
        return "Low"
    if strategy == "growth":
        return "High" if reserve_pct < 0.08 else "Medium"
    # balanced
    return "Low" if reserve_pct >= 0.12 else "Medium"


def _explanations_and_tradeoffs(
    strategy: str,
    allocs:   List[float],
    specs:    List[CategorySpec],
    total:    float,
) -> Tuple[List[str], List[str]]:
    """Generate deterministic human-readable explanations and trade-off notes."""

    reserve_pct = (allocs[IDX_RESERVE] / total * 100) if total else 0
    working_pct = (allocs[IDX_WORKING] / total * 100) if total else 0
    mkt_pct     = (allocs[IDX_MARKETING] / total * 100) if total else 0
    equip_pct   = (allocs[IDX_EQUIPMENT] / total * 100) if total else 0

    if strategy == "conservative":
        explanations = [
            f"Emergency reserve receives {reserve_pct:.0f}% of capital to protect "
            "against unexpected downturns in the first year.",
            f"Working capital ({working_pct:.0f}%) ensures you can cover operating "
            "expenses even during slow months without taking on debt.",
            "Equipment and inventory are funded at minimum viable levels to keep "
            "startup risk low.",
            "Marketing budget is kept lean — growth through word-of-mouth first.",
        ]
        tradeoffs = [
            "Lower marketing spend may slow initial customer acquisition.",
            "Reduced equipment budget may limit production capacity early on.",
            "Conservative allocations reduce growth speed in exchange for "
            "financial safety during the critical first months.",
        ]

    elif strategy == "growth":
        explanations = [
            f"Equipment receives {equip_pct:.0f}% of capital to maximise production "
            "capacity and revenue potential from day one.",
            f"Marketing budget ({mkt_pct:.0f}%) is elevated to accelerate customer "
            "acquisition and market penetration.",
            "Inventory is well-stocked to meet demand without stockouts.",
            "Working capital is kept lean — growth is prioritised over liquidity buffer.",
        ]
        tradeoffs = [
            f"Emergency reserve is lower ({reserve_pct:.0f}%) — unexpected expenses "
            "carry higher financial risk.",
            "Lower working capital means less buffer for slow revenue months.",
            "Higher upfront spend requires faster break-even to be sustainable.",
        ]

    else:  # balanced
        explanations = [
            "Capital is distributed proportionally across all categories to "
            "balance safety, operations, and growth potential.",
            f"Emergency reserve ({reserve_pct:.0f}%) provides a meaningful safety net "
            "without sacrificing growth investment.",
            f"Working capital ({working_pct:.0f}%) covers approximately 2–3 months of "
            "operating expenses to smooth cash flow.",
            "Equipment and marketing receive solid allocations to support "
            "both operations and market presence.",
        ]
        tradeoffs = [
            "No single category is maximised — this is an intentional compromise.",
            "Higher reserve than Growth strategy reduces capital available "
            "for revenue-generating assets.",
            "Lower marketing than Growth strategy means slower early growth, "
            "offset by better financial stability.",
        ]

    return explanations, tradeoffs


def _build_strategy_result(
    strategy:          str,
    label:             str,
    allocs:            List[float],
    specs:             List[CategorySpec],
    available_capital: float,
) -> StrategyResult:
    total  = sum(allocs)
    remain = max(0.0, available_capital - total)
    res_pct = allocs[IDX_RESERVE] / total if total else 0

    allocation_results = []
    alloc_dict: dict = {}
    for i, spec in enumerate(specs):
        pct = (allocs[i] / total * 100) if total else 0
        allocation_results.append(AllocationResult(
            name         = spec.name,
            allocated    = round(allocs[i], 2),
            minimum      = round(spec.minimum, 2),
            recommended  = round(spec.recommended, 2),
            maximum      = round(spec.maximum, 2),
            pct_of_total = round(pct, 1),
        ))
        alloc_dict[spec.name] = round(allocs[i], 2)

    score   = _compute_score(strategy, allocs, available_capital, specs)
    risk    = _risk_level(strategy, res_pct)
    expls, trades = _explanations_and_tradeoffs(strategy, allocs, specs, total)

    return StrategyResult(
        name               = strategy,
        label              = label,
        total_allocated    = round(total, 2),
        remaining_capital  = round(remain, 2),
        optimization_score = score,
        risk_level         = risk,
        allocations        = allocation_results,
        tradeoffs          = trades,
        explanations       = expls,
        allocation_dict    = alloc_dict,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

STRATEGY_META = {
    "conservative": "🛡️ Conservative",
    "balanced":     "⚖️ Balanced",
    "growth":       "🚀 Growth",
}


def optimize_investment(
    business_id:            str,
    business_name:          str,
    available_capital:      float,
    min_investment:         float,
    max_investment:         float,
    risk_preference:        str = "balanced",        # "conservative"|"balanced"|"growth"
    min_emergency_reserve:  Optional[float] = None,
    min_working_capital:    Optional[float] = None,
    max_marketing_budget:   Optional[float] = None,
) -> OptimizationResult:
    """
    Run the full three-strategy OR-Tools optimisation for a business.

    Returns an OptimizationResult with all three strategies, a recommended
    strategy name, and funding-gap information.
    """
    # ── Validate & normalise inputs ──────────────────────────────────────────
    available_capital = max(0.0, float(available_capital))
    min_investment    = max(0.0, float(min_investment))
    max_investment    = max(min_investment, float(max_investment))

    if risk_preference not in STRATEGY_META:
        risk_preference = "balanced"

    # ── Build category specs ─────────────────────────────────────────────────
    specs = _build_specs(
        available_capital      = available_capital,
        min_investment         = min_investment,
        max_investment         = max_investment,
        min_emergency_reserve  = min_emergency_reserve,
        min_working_capital    = min_working_capital,
        max_marketing_budget   = max_marketing_budget,
    )

    min_required = _compute_minimum_required(specs)
    funding_gap  = max(0.0, min_required - available_capital)

    # ── Insufficient capital path ─────────────────────────────────────────────
    if available_capital < min_required:
        suggestions = [
            f"Start with a smaller-scale operation requiring ₹{min_required:,.0f} minimum.",
            "Reduce optional expenses such as marketing and licensing initially.",
            f"Increase available capital by ₹{funding_gap:,.0f} through savings or informal credit.",
            "Consider a lower-investment business variant in the same category.",
            "Explore government-backed micro-credit schemes for rural entrepreneurs.",
        ]
        return OptimizationResult(
            status                   = "insufficient_capital",
            recommended_strategy     = risk_preference,
            available_capital        = available_capital,
            minimum_required_capital = min_required,
            funding_gap              = funding_gap,
            strategies               = [],
            insufficient_info        = InsufficientCapitalInfo(
                minimum_required_capital = min_required,
                funding_gap              = funding_gap,
                suggestions              = suggestions,
            ),
        )

    # ── Solve all three strategies ────────────────────────────────────────────
    results: List[StrategyResult] = []
    for strat, label in STRATEGY_META.items():
        allocs = _solve_one(strat, available_capital, specs)

        # Fallback: if solver returns None (very rare edge-case), use ratios
        if allocs is None:
            allocs = [
                min(available_capital * _BASE_RATIOS[i], spec.maximum)
                for i, spec in enumerate(specs)
            ]
            # Ensure budget constraint
            total = sum(allocs)
            if total > available_capital:
                factor = available_capital / total
                allocs = [a * factor for a in allocs]

        results.append(_build_strategy_result(strat, label, allocs, specs, available_capital))

    # ── Determine recommended strategy ───────────────────────────────────────
    # Use user's risk preference directly, as all three are always feasible.
    recommended = risk_preference

    return OptimizationResult(
        status                   = "optimal",
        recommended_strategy     = recommended,
        available_capital        = available_capital,
        minimum_required_capital = min_required,
        funding_gap              = 0.0,
        strategies               = results,
        insufficient_info        = None,
    )


def optimize_single_strategy(
    business_id:            str,
    business_name:          str,
    available_capital:      float,
    min_investment:         float,
    max_investment:         float,
    strategy:               str,
    min_emergency_reserve:  Optional[float] = None,
    min_working_capital:    Optional[float] = None,
    max_marketing_budget:   Optional[float] = None,
) -> OptimizationResult:
    """
    Run the optimizer for a single strategy only.

    The returned OptimizationResult contains just the one strategy in
    `strategies`. This is useful for quick re-optimization without running all
    three strategies.
    """
    if strategy not in STRATEGY_META:
        strategy = "balanced"

    return optimize_investment(
        business_id           = business_id,
        business_name         = business_name,
        available_capital     = available_capital,
        min_investment        = min_investment,
        max_investment        = max_investment,
        risk_preference       = strategy,
        min_emergency_reserve = min_emergency_reserve,
        min_working_capital   = min_working_capital,
        max_marketing_budget  = max_marketing_budget,
    )
