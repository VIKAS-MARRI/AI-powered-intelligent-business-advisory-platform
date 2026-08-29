"""
Scheme Matching Engine — Phase 6 Government Scheme Intelligence.

Scores and ranks government schemes against a user's business type,
financial profile, and location using transparent, deterministic formulas.

Score weights (configurable):
    Business Relevance      35%
    Sector Match            20%
    Investment Compatibility 20%
    Location Eligibility    15%
    Profile Eligibility     10%
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Weight configuration ─────────────────────────────────────────────────────

WEIGHTS: Dict[str, float] = {
    "business_relevance":       0.35,
    "sector_match":             0.20,
    "investment_compatibility": 0.20,
    "location_eligibility":     0.15,
    "profile_eligibility":      0.10,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


# ── Eligibility status constants ─────────────────────────────────────────────

ELIGIBLE_LIKELY     = "🟢 Likely Eligible"
ELIGIBLE_POSSIBLE   = "🟡 Possible Eligibility — Verify Requirements"
ELIGIBLE_UNLIKELY   = "🔴 Likely Not Eligible"
ELIGIBLE_NEED_INFO  = "⚪ More Information Required"

DISCLAIMER = (
    "Scheme recommendations are generated based on available profile, business, "
    "financial, and scheme information. Eligibility, benefits, funding amounts, "
    "and application requirements may change. Always verify the latest requirements "
    "through official government sources before applying. RuralBiz AI does not "
    "guarantee eligibility, approval, loans, subsidies, or financial assistance."
)


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class MatchRequest:
    """Inputs for scheme matching."""
    business_id:          str
    business_name:        str
    business_category:    str
    business_type:        str              # e.g. "Service", "Manufacturing"
    estimated_investment: float
    available_capital:    float
    state:                Optional[str]    = None
    user_age:             Optional[int]   = None
    is_woman:             Optional[bool]  = None
    is_sc_st:             Optional[bool]  = None
    is_rural:             Optional[bool]  = None
    is_youth:             Optional[bool]  = None
    experience_years:     Optional[int]   = None


@dataclass
class ScoreBreakdown:
    business_relevance:       float = 0.0
    sector_match:             float = 0.0
    investment_compatibility: float = 0.0
    location_eligibility:     float = 0.0
    profile_eligibility:      float = 0.0
    total:                    float = 0.0


@dataclass
class EligibilityFlag:
    status:              str                  # one of ELIGIBLE_* constants
    reasons:             List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)


@dataclass
class SchemeMatch:
    scheme_id:         str
    scheme_name:       str
    scheme_slug:       str
    category:          str
    sector:            str
    data_status:       str
    key_benefit:       str
    official_url:      str
    score_breakdown:   ScoreBreakdown
    eligibility:       EligibilityFlag
    match_reasons:     List[str]
    funding_relevance: str    # "Loan" | "Subsidy" | "Both" | "Support"
    tags:              List[str] = field(default_factory=list)


@dataclass
class FundingGapAnalysis:
    estimated_investment: float
    available_capital:    float
    funding_gap:          float
    gap_percentage:       float
    has_gap:              bool
    gap_label:            str


@dataclass
class MatchResult:
    request:           MatchRequest
    funding_gap:       FundingGapAnalysis
    matches:           List[SchemeMatch]
    best_overall:      Optional[str]       # scheme_id
    best_loan:         Optional[str]       # scheme_id
    best_subsidy:      Optional[str]       # scheme_id
    best_rural:        Optional[str]       # scheme_id
    disclaimer:        str = DISCLAIMER


# ── Sector mapping ────────────────────────────────────────────────────────────

# Maps business category / type keywords → scheme sector preferences
BUSINESS_SECTOR_MAP: Dict[str, List[str]] = {
    "agriculture":    ["Agriculture"],
    "farming":        ["Agriculture"],
    "dairy":          ["Agriculture", "Food Processing"],
    "poultry":        ["Agriculture", "Food Processing"],
    "fishery":        ["Agriculture"],
    "horticulture":   ["Agriculture"],
    "food":           ["Food Processing", "MSME"],
    "bakery":         ["Food Processing", "MSME"],
    "pickle":         ["Food Processing"],
    "processing":     ["Food Processing", "MSME"],
    "tailoring":      ["MSME", "Manufacturing"],
    "clothing":       ["MSME", "Manufacturing"],
    "garment":        ["MSME", "Manufacturing"],
    "weaving":        ["MSME", "Manufacturing"],
    "handicraft":     ["MSME", "Manufacturing"],
    "pottery":        ["MSME", "Manufacturing"],
    "craft":          ["MSME"],
    "manufacturing":  ["MSME", "Manufacturing"],
    "grocery":        ["MSME", "General"],
    "kirana":         ["MSME", "General"],
    "retail":         ["MSME", "General"],
    "general":        ["General"],
    "services":       ["General", "MSME"],
    "beauty":         ["MSME", "General"],
    "salon":          ["MSME"],
    "electronics":    ["MSME", "Manufacturing"],
    "hardware":       ["MSME"],
    "technology":     ["General"],
    "education":      ["General"],
    "coaching":       ["General"],
    "medical":        ["General"],
    "pharmacy":       ["General"],
    "transport":      ["General"],
}


def _infer_sectors(business_name: str, business_category: str, business_type: str) -> List[str]:
    """Return likely scheme sectors for this business."""
    text = f"{business_name} {business_category} {business_type}".lower()
    sectors: set = set()
    for kw, sec_list in BUSINESS_SECTOR_MAP.items():
        if kw in text:
            sectors.update(sec_list)
    if not sectors:
        sectors.add("General")
    return list(sectors)


# ── Individual scorers ────────────────────────────────────────────────────────

def _business_relevance_score(scheme, req: MatchRequest) -> float:
    """
    0–100: How closely does the scheme's business_categories match the request?
    """
    scheme_cats = set(c.strip().lower() for c in scheme.business_categories.split(","))
    text = f"{req.business_name} {req.business_category} {req.business_type}".lower()

    matched = sum(1 for cat in scheme_cats if cat and cat in text)
    if matched == 0:
        # Check reverse: any request word in scheme categories
        req_words = set(text.split())
        matched = sum(1 for cat in scheme_cats if any(w in cat for w in req_words if len(w) > 3))

    if matched >= 3:   return 100.0
    if matched == 2:   return 75.0
    if matched == 1:   return 50.0
    return 10.0


def _sector_match_score(scheme, req: MatchRequest) -> float:
    """
    0–100: Scheme sector vs inferred business sectors.
    """
    inferred = _infer_sectors(req.business_name, req.business_category, req.business_type)
    scheme_sector = scheme.sector.lower()

    if scheme.sector == "General":
        return 70.0  # General schemes apply broadly
    if scheme.sector in inferred or any(scheme_sector in s.lower() for s in inferred):
        return 100.0
    # Partial match — General always gives partial
    if "general" in [s.lower() for s in inferred]:
        return 60.0
    return 20.0


def _investment_compatibility_score(scheme, req: MatchRequest) -> float:
    """
    0–100: Does the required investment fit within the scheme's supported range?
    """
    inv = req.estimated_investment
    lo  = scheme.minimum_investment or 0
    hi  = scheme.maximum_investment or float("inf")

    if lo <= inv <= hi:
        return 100.0

    if inv < lo:
        # Investment below minimum — may still partly benefit
        ratio = inv / lo
        return round(max(10.0, ratio * 60.0), 1)

    # Investment above max — scheme may not cover the full amount
    ratio = hi / inv
    return round(max(10.0, ratio * 70.0), 1)


def _location_eligibility_score(scheme, req: MatchRequest) -> float:
    """
    0–100: Does the scheme apply to the user's state?
    """
    if scheme.location_scope == "National":
        return 100.0

    if not req.state:
        return 60.0  # No state info — unknown

    scheme_states = [s.strip().lower() for s in scheme.states.split(",")]
    if "all" in scheme_states:
        return 100.0

    state_norm = req.state.lower().strip()
    if state_norm in scheme_states:
        return 100.0

    return 10.0  # State-specific, doesn't match


def _profile_eligibility_score(scheme, req: MatchRequest) -> tuple[float, EligibilityFlag]:
    """
    0–100: User profile-based eligibility assessment.
    Returns (score, EligibilityFlag).
    """
    score         = 50.0   # Neutral default
    reasons:       list[str] = []
    missing:       list[str] = []
    red_flags:     list[str] = []

    # Age check
    if scheme.minimum_age is not None:
        if req.user_age is None:
            missing.append("Your age (to verify age eligibility)")
        elif req.user_age < scheme.minimum_age:
            red_flags.append(f"Age below scheme minimum ({scheme.minimum_age} years)")
        else:
            score += 10
            reasons.append(f"✓ Age meets minimum requirement ({scheme.minimum_age}+ years)")

    if scheme.maximum_age is not None and req.user_age is not None:
        if req.user_age > scheme.maximum_age:
            red_flags.append(f"Age above scheme maximum ({scheme.maximum_age} years)")
        else:
            reasons.append(f"✓ Age within scheme range (max {scheme.maximum_age} years)")

    # Women-specific
    if scheme.is_women_specific:
        if req.is_woman is None:
            missing.append("Gender information (this scheme is for women entrepreneurs)")
        elif req.is_woman:
            score += 20
            reasons.append("✓ Women-specific scheme — matches your profile")
        else:
            red_flags.append("This scheme is specifically for women entrepreneurs")
            score -= 40

    # SC/ST specific
    if scheme.is_sc_st_specific:
        if req.is_sc_st is None:
            missing.append("SC/ST status (this scheme prioritises SC/ST beneficiaries)")
        elif req.is_sc_st:
            score += 20
            reasons.append("✓ SC/ST preference scheme — matches your profile")
        else:
            score -= 10  # Still possible, just lower priority

    # Rural specific
    if scheme.is_rural_specific:
        if req.is_rural is None:
            missing.append("Whether you are based in a rural area (this scheme targets rural entrepreneurs)")
        elif req.is_rural:
            score += 15
            reasons.append("✓ Rural scheme — matches your rural location")
        else:
            score -= 15

    # Youth specific
    if scheme.is_youth_specific:
        if req.is_youth is None or req.user_age is None:
            missing.append("Age information (this scheme targets youth entrepreneurs)")
        elif req.user_age <= 35:
            score += 10
            reasons.append("✓ Youth entrepreneur — eligible for youth-focused scheme")

    score = max(0.0, min(100.0, score))

    # Classify eligibility
    if red_flags:
        if len(red_flags) >= 2 or (scheme.is_women_specific and not req.is_woman):
            status = ELIGIBLE_UNLIKELY
        else:
            status = ELIGIBLE_POSSIBLE
        reasons = [f"⚠️ {r}" for r in red_flags] + reasons
    elif missing:
        status = ELIGIBLE_NEED_INFO if not reasons else ELIGIBLE_POSSIBLE
    elif score >= 60:
        status = ELIGIBLE_LIKELY
    else:
        status = ELIGIBLE_POSSIBLE

    if not reasons and not red_flags:
        reasons = ["Based on available profile information, this scheme may be applicable"]

    return score, EligibilityFlag(status=status, reasons=reasons, missing_information=missing)


# ── Total score ───────────────────────────────────────────────────────────────

def _compute_match(scheme, req: MatchRequest) -> SchemeMatch:
    br  = _business_relevance_score(scheme, req)
    sm  = _sector_match_score(scheme, req)
    ic  = _investment_compatibility_score(scheme, req)
    le  = _location_eligibility_score(scheme, req)
    pe, elig = _profile_eligibility_score(scheme, req)

    total = (
        br  * WEIGHTS["business_relevance"] +
        sm  * WEIGHTS["sector_match"] +
        ic  * WEIGHTS["investment_compatibility"] +
        le  * WEIGHTS["location_eligibility"] +
        pe  * WEIGHTS["profile_eligibility"]
    )
    total = round(min(100.0, max(0.0, total)), 1)

    breakdown = ScoreBreakdown(
        business_relevance       = round(br  * WEIGHTS["business_relevance"],       1),
        sector_match             = round(sm  * WEIGHTS["sector_match"],             1),
        investment_compatibility = round(ic  * WEIGHTS["investment_compatibility"], 1),
        location_eligibility     = round(le  * WEIGHTS["location_eligibility"],     1),
        profile_eligibility      = round(pe  * WEIGHTS["profile_eligibility"],      1),
        total                    = total,
    )

    # Match reasons
    reasons: list[str] = []
    if br >= 75: reasons.append("✓ Matches your business category")
    if sm >= 80: reasons.append("✓ Sector aligns with your business type")
    if ic >= 80: reasons.append("✓ Investment amount is compatible with scheme range")
    if le == 100: reasons.append("✓ Scheme is available in your location")
    reasons.extend(elig.reasons[:3])

    # Funding relevance label
    if scheme.maximum_loan_amount and scheme.maximum_subsidy_amount:
        funding_relevance = "Both"
    elif scheme.maximum_loan_amount:
        funding_relevance = "Loan"
    elif scheme.maximum_subsidy_amount or scheme.subsidy_percentage:
        funding_relevance = "Subsidy"
    else:
        funding_relevance = "Support"

    # Tags
    tags: list[str] = []
    if scheme.is_women_specific: tags.append("Women")
    if scheme.is_sc_st_specific: tags.append("SC/ST")
    if scheme.is_rural_specific: tags.append("Rural")
    if scheme.is_youth_specific: tags.append("Youth")

    return SchemeMatch(
        scheme_id         = scheme.id,
        scheme_name       = scheme.name,
        scheme_slug       = scheme.slug,
        category          = scheme.category,
        sector            = scheme.sector,
        data_status       = scheme.data_status,
        key_benefit       = scheme.key_benefit or scheme.short_description[:120],
        official_url      = scheme.official_url,
        score_breakdown   = breakdown,
        eligibility       = elig,
        match_reasons     = reasons,
        funding_relevance = funding_relevance,
        tags              = tags,
    )


# ── Funding gap ────────────────────────────────────────────────────────────────

def compute_funding_gap(estimated_investment: float, available_capital: float) -> FundingGapAnalysis:
    gap = max(0.0, estimated_investment - available_capital)
    gap_pct = (gap / estimated_investment * 100) if estimated_investment > 0 else 0.0
    has_gap = gap > 0

    if not has_gap:
        label = "No funding gap — capital covers the estimated investment"
    elif gap_pct <= 25:
        label = "Small gap — a moderate loan or subsidy may bridge this"
    elif gap_pct <= 60:
        label = "Moderate gap — loan or subsidy support may be needed"
    else:
        label = "Large gap — multiple support schemes or significant loan may be required"

    return FundingGapAnalysis(
        estimated_investment = estimated_investment,
        available_capital    = available_capital,
        funding_gap          = gap,
        gap_percentage       = round(gap_pct, 1),
        has_gap              = has_gap,
        gap_label            = label,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def match_schemes(
    schemes: list,
    req:     MatchRequest,
    top_n:   int = 10,
) -> MatchResult:
    """
    Match and rank all active schemes for a given MatchRequest.

    Parameters:
        schemes  — list of Scheme ORM objects (already loaded)
        req      — MatchRequest with business + profile + financial info
        top_n    — number of top matches to return

    Returns a MatchResult with ranked SchemeMatch objects.
    """
    matches: list[SchemeMatch] = []
    for scheme in schemes:
        if not scheme.is_active:
            continue
        m = _compute_match(scheme, req)
        matches.append(m)

    # Sort by total score descending
    matches.sort(key=lambda m: m.score_breakdown.total, reverse=True)
    top = matches[:top_n]

    # Special category winners
    def _best(category: str | None, funding: str | None) -> Optional[str]:
        filtered = [
            m for m in top
            if (category is None or m.category == category) and
               (funding is None or m.funding_relevance in [funding, "Both"])
        ]
        return filtered[0].scheme_id if filtered else None

    best_loan    = _best(None, "Loan")
    best_subsidy = _best(None, "Subsidy")
    best_rural   = next((m.scheme_id for m in top if "Rural" in m.tags or m.score_breakdown.total >= 50
                         and m.eligibility.status != ELIGIBLE_UNLIKELY), None)

    gap = compute_funding_gap(req.estimated_investment, req.available_capital)

    return MatchResult(
        request      = req,
        funding_gap  = gap,
        matches      = top,
        best_overall = top[0].scheme_id if top else None,
        best_loan    = best_loan,
        best_subsidy = best_subsidy,
        best_rural   = best_rural,
    )


def compare_schemes(
    schemes: list,
    scheme_ids: list[str],
    req: Optional[MatchRequest] = None,
) -> list[SchemeMatch]:
    """
    Return SchemeMatch objects for a set of scheme IDs.
    If req is provided, compute match scores; otherwise return neutral matches.
    """
    scheme_map = {s.id: s for s in schemes}
    result = []
    for sid in scheme_ids[:4]:  # max 4
        scheme = scheme_map.get(sid)
        if scheme and scheme.is_active:
            if req:
                result.append(_compute_match(scheme, req))
            else:
                # Build a minimal neutral match for comparison display
                result.append(SchemeMatch(
                    scheme_id         = scheme.id,
                    scheme_name       = scheme.name,
                    scheme_slug       = scheme.slug,
                    category          = scheme.category,
                    sector            = scheme.sector,
                    data_status       = scheme.data_status,
                    key_benefit       = scheme.key_benefit or "",
                    official_url      = scheme.official_url,
                    score_breakdown   = ScoreBreakdown(),
                    eligibility       = EligibilityFlag(status=ELIGIBLE_NEED_INFO),
                    match_reasons     = [],
                    funding_relevance = "Support",
                ))
    return result
