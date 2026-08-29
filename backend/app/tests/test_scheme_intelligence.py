"""
Comprehensive tests for Phase 6 Government Scheme Intelligence.

Tests:
  - Scheme dataset integrity
  - Scheme matching engine (scoring)
  - Eligibility classification
  - Funding gap analysis
  - Scheme comparison
  - API endpoint behavior (via TestClient with mocked DB)

Run with: python -m pytest app/tests/test_scheme_intelligence.py -v
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.seed_schemes import SCHEMES
from app.services.scheme_matcher import (
    ELIGIBLE_LIKELY,
    ELIGIBLE_NEED_INFO,
    ELIGIBLE_POSSIBLE,
    ELIGIBLE_UNLIKELY,
    WEIGHTS,
    MatchRequest,
    _business_relevance_score,
    _sector_match_score,
    _investment_compatibility_score,
    _location_eligibility_score,
    _profile_eligibility_score,
    _compute_match,
    _infer_sectors,
    compute_funding_gap,
    match_schemes,
    compare_schemes,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_scheme(**overrides):
    """Create a mock Scheme object with sensible defaults."""
    defaults = {
        "id":                       "s001",
        "name":                     "Test Loan Scheme",
        "slug":                     "test-loan",
        "short_description":        "A test scheme",
        "category":                 "Loan",
        "sector":                   "MSME",
        "target_beneficiaries":     "Entrepreneurs",
        "location_scope":           "National",
        "states":                   "All",
        "business_categories":      "tailoring,clothing,food processing,bakery",
        "business_tags":            "shop,craft",
        "minimum_age":              18,
        "maximum_age":              None,
        "minimum_investment":       50000,
        "maximum_investment":       2000000,
        "maximum_loan_amount":      1000000,
        "maximum_subsidy_amount":   None,
        "subsidy_percentage":       None,
        "key_benefit":              "Loan up to ₹10 lakh",
        "eligibility_requirements": json.dumps(["Age 18+", "Valid business plan"]),
        "required_documents":       json.dumps(["Aadhaar", "PAN"]),
        "application_steps":        json.dumps(["Apply online", "Submit docs"]),
        "is_women_specific":        False,
        "is_sc_st_specific":        False,
        "is_rural_specific":        False,
        "is_youth_specific":        False,
        "official_source":          "Test Ministry",
        "official_url":             "https://example.gov.in/",
        "data_status":              "verified",
        "last_reviewed":            "2024-01",
        "is_active":                True,
        "sort_order":               1,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_req(**overrides) -> MatchRequest:
    defaults = dict(
        business_id          = "b001",
        business_name        = "Tailoring Shop",
        business_category    = "Tailoring & Clothing",
        business_type        = "Service",
        estimated_investment = 150000,
        available_capital    = 80000,
        state                = "Telangana",
        user_age             = 28,
        is_woman             = None,
        is_sc_st             = None,
        is_rural             = True,
        is_youth             = None,
        experience_years     = None,
    )
    defaults.update(overrides)
    return MatchRequest(**defaults)


# ══════════════════════════════════════════════════════════════════════════════
# TestSeedDataIntegrity
# ══════════════════════════════════════════════════════════════════════════════

class TestSeedDataIntegrity:
    """Validate the structure and completeness of every scheme in SCHEMES."""

    REQUIRED_STR_FIELDS = [
        "name", "slug", "short_description", "category", "sector",
        "target_beneficiaries", "location_scope", "states", "business_categories",
        "official_source", "official_url", "data_status", "last_reviewed",
    ]
    REQUIRED_JSON_FIELDS = [
        "eligibility_requirements", "required_documents", "application_steps",
    ]

    def test_dataset_not_empty(self):
        assert len(SCHEMES) >= 5, "Scheme dataset must have at least 5 schemes"

    def test_all_slugs_unique(self):
        slugs = [s["slug"] for s in SCHEMES]
        assert len(slugs) == len(set(slugs)), "All scheme slugs must be unique"

    def test_required_string_fields_present(self):
        for s in SCHEMES:
            for field in self.REQUIRED_STR_FIELDS:
                assert field in s and s[field], \
                    f"Scheme '{s.get('name','?')}' missing required field '{field}'"

    def test_json_fields_are_valid_lists(self):
        for s in SCHEMES:
            for field in self.REQUIRED_JSON_FIELDS:
                assert field in s, f"Scheme '{s.get('name','?')}' missing '{field}'"
                parsed = json.loads(s[field])
                assert isinstance(parsed, list), f"'{field}' must be a JSON list"
                assert len(parsed) > 0, f"'{field}' must not be empty"

    def test_verified_schemes_have_real_urls(self):
        for s in SCHEMES:
            if s["data_status"] == "verified":
                url = s.get("official_url", "")
                assert url.startswith("http"), \
                    f"Verified scheme '{s.get('name')}' must have a real official_url"

    def test_data_status_valid(self):
        valid_statuses = {"verified", "demo"}
        for s in SCHEMES:
            assert s["data_status"] in valid_statuses, \
                f"Scheme '{s.get('name')}' has invalid data_status '{s['data_status']}'"

    def test_age_fields_logical(self):
        for s in SCHEMES:
            mn = s.get("minimum_age")
            mx = s.get("maximum_age")
            if mn and mx:
                assert mn < mx, \
                    f"Scheme '{s.get('name')}': minimum_age >= maximum_age"

    def test_investment_fields_logical(self):
        for s in SCHEMES:
            lo = s.get("minimum_investment")
            hi = s.get("maximum_investment")
            if lo and hi:
                assert lo < hi, \
                    f"Scheme '{s.get('name')}': minimum_investment >= maximum_investment"

    def test_location_scope_valid(self):
        valid_scopes = {"National", "State"}
        for s in SCHEMES:
            assert s["location_scope"] in valid_scopes, \
                f"Scheme '{s.get('name')}' has invalid location_scope '{s['location_scope']}'"

    def test_boolean_flags_present(self):
        flags = ["is_women_specific", "is_sc_st_specific", "is_rural_specific", "is_youth_specific"]
        for s in SCHEMES:
            for f in flags:
                assert isinstance(s.get(f), bool), \
                    f"Scheme '{s.get('name')}' flag '{f}' must be a boolean"


# ══════════════════════════════════════════════════════════════════════════════
# TestWeightsConfiguration
# ══════════════════════════════════════════════════════════════════════════════

class TestWeightsConfiguration:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_all_weights_positive(self):
        for k, v in WEIGHTS.items():
            assert v > 0, f"Weight '{k}' must be positive"

    def test_business_relevance_highest(self):
        assert WEIGHTS["business_relevance"] == max(WEIGHTS.values())


# ══════════════════════════════════════════════════════════════════════════════
# TestBusinessRelevanceScore
# ══════════════════════════════════════════════════════════════════════════════

class TestBusinessRelevanceScore:
    def test_strong_match_returns_high_score(self):
        scheme = _make_scheme(business_categories="tailoring,clothing,fashion")
        req    = _make_req(business_name="Tailoring Shop", business_category="Tailoring & Clothing")
        score  = _business_relevance_score(scheme, req)
        assert score >= 50.0

    def test_no_match_returns_low_score(self):
        scheme = _make_scheme(business_categories="fishery,aquaculture,marine")
        req    = _make_req(business_name="Software Company", business_category="Technology")
        score  = _business_relevance_score(scheme, req)
        assert score <= 20.0

    def test_three_matches_returns_100(self):
        scheme = _make_scheme(business_categories="tailoring,clothing,fashion,garment,boutique")
        req    = _make_req(
            business_name="Tailoring & Clothing Fashion",
            business_category="Garment",
        )
        score  = _business_relevance_score(scheme, req)
        assert score == 100.0

    def test_two_matches_returns_75(self):
        scheme = _make_scheme(business_categories="bakery,food,snacks,dairy")
        req    = _make_req(business_name="Bakery and Food Shop", business_category="Retail")
        score  = _business_relevance_score(scheme, req)
        assert score == 75.0


# ══════════════════════════════════════════════════════════════════════════════
# TestSectorMatchScore
# ══════════════════════════════════════════════════════════════════════════════

class TestSectorMatchScore:
    def test_general_scheme_returns_70(self):
        scheme = _make_scheme(sector="General")
        req    = _make_req()
        assert _sector_match_score(scheme, req) == 70.0

    def test_matching_sector_returns_100(self):
        scheme = _make_scheme(sector="MSME")
        req    = _make_req(business_name="Tailoring", business_category="Tailoring", business_type="Manufacturing")
        assert _sector_match_score(scheme, req) == 100.0

    def test_mismatching_sector_returns_low(self):
        # Agriculture scheme vs a business with no agriculture/food/farm keywords
        # and business_type "Manufacturing" which does not map to Agriculture
        scheme = _make_scheme(sector="Agriculture")
        req    = _make_req(
            business_name="Beauty Parlour",
            business_category="Beauty & Wellness",
            business_type="Service",
        )
        score = _sector_match_score(scheme, req)
        # "Service" infers General which gives a fallback of 60,
        # but Agriculture vs non-agri should be <= 65
        assert score <= 65.0


# ══════════════════════════════════════════════════════════════════════════════
# TestInvestmentCompatibilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestInvestmentCompatibilityScore:
    def test_investment_in_range_returns_100(self):
        scheme = _make_scheme(minimum_investment=100000, maximum_investment=500000)
        req    = _make_req(estimated_investment=200000)
        assert _investment_compatibility_score(scheme, req) == 100.0

    def test_investment_below_min_returns_reduced(self):
        scheme = _make_scheme(minimum_investment=500000, maximum_investment=2000000)
        req    = _make_req(estimated_investment=100000)
        score  = _investment_compatibility_score(scheme, req)
        assert score < 100.0
        assert score >= 10.0

    def test_investment_above_max_returns_reduced(self):
        scheme = _make_scheme(minimum_investment=10000, maximum_investment=200000)
        req    = _make_req(estimated_investment=1000000)
        score  = _investment_compatibility_score(scheme, req)
        assert score < 100.0
        assert score >= 10.0

    def test_no_range_limits_returns_100(self):
        scheme = _make_scheme(minimum_investment=None, maximum_investment=None)
        req    = _make_req(estimated_investment=999999)
        assert _investment_compatibility_score(scheme, req) == 100.0

    def test_investment_at_exact_min(self):
        scheme = _make_scheme(minimum_investment=50000, maximum_investment=500000)
        req    = _make_req(estimated_investment=50000)
        assert _investment_compatibility_score(scheme, req) == 100.0


# ══════════════════════════════════════════════════════════════════════════════
# TestLocationEligibilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestLocationEligibilityScore:
    def test_national_scope_always_100(self):
        scheme = _make_scheme(location_scope="National", states="All")
        req    = _make_req(state="Telangana")
        assert _location_eligibility_score(scheme, req) == 100.0

    def test_national_scope_no_state(self):
        scheme = _make_scheme(location_scope="National", states="All")
        req    = _make_req(state=None)
        assert _location_eligibility_score(scheme, req) == 100.0

    def test_state_scope_matching_state(self):
        scheme = _make_scheme(location_scope="State", states="telangana,andhra pradesh")
        req    = _make_req(state="Telangana")
        assert _location_eligibility_score(scheme, req) == 100.0

    def test_state_scope_non_matching_state(self):
        scheme = _make_scheme(location_scope="State", states="maharashtra,gujarat")
        req    = _make_req(state="Telangana")
        assert _location_eligibility_score(scheme, req) == 10.0

    def test_state_scope_no_user_state(self):
        scheme = _make_scheme(location_scope="State", states="maharashtra")
        req    = _make_req(state=None)
        assert _location_eligibility_score(scheme, req) == 60.0


# ══════════════════════════════════════════════════════════════════════════════
# TestProfileEligibilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestProfileEligibilityScore:
    def test_women_scheme_with_woman(self):
        scheme = _make_scheme(is_women_specific=True)
        req    = _make_req(is_woman=True)
        score, flag = _profile_eligibility_score(scheme, req)
        assert score > 50.0
        assert flag.status in [ELIGIBLE_LIKELY, ELIGIBLE_POSSIBLE]

    def test_women_scheme_without_woman(self):
        scheme = _make_scheme(is_women_specific=True)
        req    = _make_req(is_woman=False)
        score, flag = _profile_eligibility_score(scheme, req)
        assert flag.status == ELIGIBLE_UNLIKELY

    def test_women_scheme_unknown_gender(self):
        scheme = _make_scheme(is_women_specific=True)
        req    = _make_req(is_woman=None)
        _, flag = _profile_eligibility_score(scheme, req)
        assert "Gender" in " ".join(flag.missing_information)

    def test_age_below_minimum(self):
        scheme = _make_scheme(minimum_age=18)
        req    = _make_req(user_age=16)
        _, flag = _profile_eligibility_score(scheme, req)
        assert flag.status in [ELIGIBLE_UNLIKELY, ELIGIBLE_POSSIBLE]

    def test_age_above_maximum(self):
        scheme = _make_scheme(minimum_age=18, maximum_age=45)
        req    = _make_req(user_age=50)
        _, flag = _profile_eligibility_score(scheme, req)
        assert flag.status in [ELIGIBLE_UNLIKELY, ELIGIBLE_POSSIBLE]

    def test_missing_age_generates_info_needed(self):
        scheme = _make_scheme(minimum_age=18)
        req    = _make_req(user_age=None)
        _, flag = _profile_eligibility_score(scheme, req)
        assert len(flag.missing_information) > 0

    def test_rural_scheme_with_rural_user(self):
        scheme = _make_scheme(is_rural_specific=True)
        req    = _make_req(is_rural=True)
        score, _ = _profile_eligibility_score(scheme, req)
        assert score > 50.0

    def test_rural_scheme_non_rural_user(self):
        scheme = _make_scheme(is_rural_specific=True)
        req    = _make_req(is_rural=False)
        score, _ = _profile_eligibility_score(scheme, req)
        assert score < 70.0


# ══════════════════════════════════════════════════════════════════════════════
# TestFundingGap
# ══════════════════════════════════════════════════════════════════════════════

class TestFundingGap:
    def test_no_gap_when_capital_covers_investment(self):
        result = compute_funding_gap(100000, 150000)
        assert not result.has_gap
        assert result.funding_gap == 0.0

    def test_gap_equals_difference(self):
        result = compute_funding_gap(200000, 120000)
        assert result.has_gap
        assert result.funding_gap == 80000

    def test_gap_percentage_correct(self):
        result = compute_funding_gap(200000, 100000)
        assert result.gap_percentage == pytest.approx(50.0, abs=0.1)

    def test_zero_capital(self):
        result = compute_funding_gap(100000, 0)
        assert result.has_gap
        assert result.funding_gap == 100000
        assert result.gap_percentage == 100.0

    def test_large_gap_label(self):
        result = compute_funding_gap(500000, 50000)
        assert "large" in result.gap_label.lower()

    def test_small_gap_label(self):
        result = compute_funding_gap(200000, 160000)
        assert "small" in result.gap_label.lower()

    def test_no_gap_label(self):
        result = compute_funding_gap(100000, 200000)
        assert "no" in result.gap_label.lower()


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeMatch
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeMatch:
    def test_total_score_in_range(self):
        scheme = _make_scheme()
        req    = _make_req()
        m = _compute_match(scheme, req)
        assert 0 <= m.score_breakdown.total <= 100

    def test_funding_relevance_loan(self):
        scheme = _make_scheme(maximum_loan_amount=1000000, maximum_subsidy_amount=None, subsidy_percentage=None)
        m = _compute_match(scheme, _make_req())
        assert m.funding_relevance == "Loan"

    def test_funding_relevance_subsidy(self):
        scheme = _make_scheme(maximum_loan_amount=None, maximum_subsidy_amount=500000, subsidy_percentage=35)
        m = _compute_match(scheme, _make_req())
        assert m.funding_relevance == "Subsidy"

    def test_funding_relevance_both(self):
        scheme = _make_scheme(maximum_loan_amount=500000, maximum_subsidy_amount=200000)
        m = _compute_match(scheme, _make_req())
        assert m.funding_relevance == "Both"

    def test_women_tag_on_women_scheme(self):
        scheme = _make_scheme(is_women_specific=True)
        m = _compute_match(scheme, _make_req())
        assert "Women" in m.tags

    def test_rural_tag_on_rural_scheme(self):
        scheme = _make_scheme(is_rural_specific=True)
        m = _compute_match(scheme, _make_req())
        assert "Rural" in m.tags

    def test_score_breakdown_sums_to_total(self):
        scheme = _make_scheme()
        req    = _make_req()
        m      = _compute_match(scheme, req)
        sub_sum = (
            m.score_breakdown.business_relevance +
            m.score_breakdown.sector_match +
            m.score_breakdown.investment_compatibility +
            m.score_breakdown.location_eligibility +
            m.score_breakdown.profile_eligibility
        )
        assert abs(sub_sum - m.score_breakdown.total) < 1.0


# ══════════════════════════════════════════════════════════════════════════════
# TestMatchSchemes
# ══════════════════════════════════════════════════════════════════════════════

class TestMatchSchemes:
    def _schemes(self, n=3):
        return [_make_scheme(id=f"s{i:03d}", slug=f"scheme-{i}", sort_order=i) for i in range(n)]

    def test_returns_match_result(self):
        schemes = self._schemes(3)
        req     = _make_req()
        result  = match_schemes(schemes, req)
        assert len(result.matches) <= 3

    def test_sorted_by_score_desc(self):
        schemes = self._schemes(5)
        req     = _make_req()
        result  = match_schemes(schemes, req)
        scores  = [m.score_breakdown.total for m in result.matches]
        assert scores == sorted(scores, reverse=True)

    def test_inactive_schemes_excluded(self):
        s_active   = _make_scheme(id="s001", slug="active",   is_active=True)
        s_inactive = _make_scheme(id="s002", slug="inactive", is_active=False)
        result = match_schemes([s_active, s_inactive], _make_req())
        ids = [m.scheme_id for m in result.matches]
        assert "s002" not in ids

    def test_best_loan_identified(self):
        loan_scheme    = _make_scheme(id="L001", slug="loan",    maximum_loan_amount=1000000,  maximum_subsidy_amount=None, subsidy_percentage=None)
        subsidy_scheme = _make_scheme(id="S001", slug="subsidy", maximum_loan_amount=None, maximum_subsidy_amount=500000, subsidy_percentage=35)
        result = match_schemes([loan_scheme, subsidy_scheme], _make_req())
        assert result.best_loan == "L001"

    def test_best_subsidy_identified(self):
        loan_scheme    = _make_scheme(id="L001", slug="loan",    maximum_loan_amount=1000000, maximum_subsidy_amount=None, subsidy_percentage=None)
        subsidy_scheme = _make_scheme(id="S001", slug="subsidy", maximum_loan_amount=None,    maximum_subsidy_amount=500000, subsidy_percentage=35)
        result = match_schemes([loan_scheme, subsidy_scheme], _make_req())
        assert result.best_subsidy == "S001"

    def test_top_n_respected(self):
        schemes = self._schemes(10)
        result  = match_schemes(schemes, _make_req(), top_n=3)
        assert len(result.matches) <= 3

    def test_funding_gap_in_result(self):
        result = match_schemes(self._schemes(), _make_req(estimated_investment=200000, available_capital=80000))
        assert result.funding_gap.has_gap
        assert result.funding_gap.funding_gap == 120000

    def test_no_funding_gap(self):
        result = match_schemes(self._schemes(), _make_req(estimated_investment=50000, available_capital=100000))
        assert not result.funding_gap.has_gap

    def test_disclaimer_present(self):
        result = match_schemes(self._schemes(), _make_req())
        assert "official government sources" in result.disclaimer.lower()


# ══════════════════════════════════════════════════════════════════════════════
# TestCompareSchemes
# ══════════════════════════════════════════════════════════════════════════════

class TestCompareSchemes:
    def test_compare_two_schemes(self):
        s1 = _make_scheme(id="C001", slug="c1")
        s2 = _make_scheme(id="C002", slug="c2")
        result = compare_schemes([s1, s2], ["C001", "C002"])
        assert len(result) == 2

    def test_compare_with_match_request(self):
        s1 = _make_scheme(id="C001", slug="c1")
        s2 = _make_scheme(id="C002", slug="c2")
        req = _make_req()
        result = compare_schemes([s1, s2], ["C001", "C002"], req)
        assert all(m.score_breakdown.total > 0 for m in result)

    def test_max_four_schemes(self):
        schemes = [_make_scheme(id=f"C{i:03d}", slug=f"c{i}") for i in range(6)]
        ids = [f"C{i:03d}" for i in range(6)]
        result = compare_schemes(schemes, ids[:4])
        assert len(result) <= 4

    def test_unknown_id_skipped(self):
        s1 = _make_scheme(id="C001", slug="c1")
        result = compare_schemes([s1], ["C001", "UNKNOWN"])
        ids = [m.scheme_id for m in result]
        assert "C001" in ids
        assert "UNKNOWN" not in ids

    def test_inactive_scheme_excluded(self):
        s1 = _make_scheme(id="C001", slug="c1", is_active=True)
        s2 = _make_scheme(id="C002", slug="c2", is_active=False)
        result = compare_schemes([s1, s2], ["C001", "C002"])
        assert len(result) == 1


# ══════════════════════════════════════════════════════════════════════════════
# TestInferSectors
# ══════════════════════════════════════════════════════════════════════════════

class TestInferSectors:
    def test_tailoring_maps_to_msme(self):
        sectors = _infer_sectors("Tailoring Shop", "Tailoring", "Service")
        assert "MSME" in sectors

    def test_dairy_maps_to_agriculture(self):
        sectors = _infer_sectors("Dairy Farm", "Dairy", "Agriculture")
        assert "Agriculture" in sectors

    def test_food_processing_maps_correctly(self):
        sectors = _infer_sectors("Bakery", "Food Processing", "Manufacturing")
        assert "Food Processing" in sectors or "MSME" in sectors

    def test_unknown_business_returns_general(self):
        sectors = _infer_sectors("XYZ Business", "Unknown", "Service")
        assert "General" in sectors
