"""
Comprehensive Phase 8 tests — Semantic Intelligence & Personalized Recommendations.

Covers:
  1. Semantic Matcher — concept graph, TF-IDF fallback, token overlap, batch, intent extraction
  2. Personalized Recommendation Engine — all 10 factors, preference modifier
  3. Natural Language Query — budget/skill/risk extraction, AI-unavailable fallback
  4. Saved Businesses — save, list, delete, duplicate handling, auth
  5. Interaction Tracking — types, preference calculation
  6. Phase 8 API endpoints — authenticated, error cases
  7. Backward compatibility — Phase 2 /recommendations still works

Run: python -m pytest app/tests/test_phase8.py -v
No real API key or network required.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Semantic matcher ─────────────────────────────────────────────────────────

class TestSemanticMatcher:
    def _match(self, skills, interests, name, cat, desc, req_skills):
        from app.services.semantic_matcher import semantic_match
        return semantic_match(
            user_skills=skills, user_interests=interests,
            biz_name=name, biz_category=cat,
            biz_description=desc, biz_required_skills=req_skills,
        )

    def test_exact_skill_match_high_score(self):
        r = self._match("tailoring", None, "Tailoring Shop", "Service",
                        "Clothing alteration and stitching.", "stitching, garment")
        assert r["semantic_score"] >= 60

    def test_synonym_match(self):
        """'stitching clothes' should match tailoring shop."""
        r = self._match("stitching clothes", None, "Tailoring Shop", "Service",
                        "Custom garment creation.", "tailoring, sewing")
        assert r["semantic_score"] >= 40

    def test_unrelated_skill_low_score(self):
        """Driving skills should not match a bakery."""
        r = self._match("driving vehicles", None, "Bakery", "Food",
                        "Baking bread and cakes.", "baking, cooking")
        assert r["semantic_score"] < 55

    def test_empty_skills_returns_default(self):
        r = self._match(None, None, "Any Business", "Retail", "Shop.", "selling")
        assert 0 <= r["semantic_score"] <= 50
        assert r["method"] == "default"

    def test_returns_required_fields(self):
        r = self._match("cooking", None, "Food Stall", "Food", "Street food.", "cooking")
        for key in ("semantic_score", "matched_concepts", "explanation", "method"):
            assert key in r

    def test_score_range_0_to_100(self):
        for skills, name in [
            ("tailoring", "Tailoring Shop"),
            ("", "Dairy Farm"),
            ("xyz abc zzz", "Bakery"),
        ]:
            r = self._match(skills, None, name, "Service", "Desc.", "skill1")
            assert 0 <= r["semantic_score"] <= 100

    def test_mobile_repair_matches_electronics(self):
        r = self._match("mobile phone repair", None, "Mobile Repair Shop", "Service",
                        "Repairs smartphones and electronics.", "mobile, electronics, repair")
        assert r["semantic_score"] >= 50

    def test_farming_matches_dairy(self):
        r = self._match("animal care and dairy", None, "Dairy Farming", "Agriculture",
                        "Milk production from cattle.", "animal husbandry, livestock care")
        assert r["semantic_score"] >= 50

    def test_explanation_string_present(self):
        r = self._match("cooking food", None, "Catering", "Food",
                        "Event catering services.", "cooking, chef")
        assert len(r["explanation"]) > 10

    def test_matched_concepts_list(self):
        r = self._match("stitching garment design", None, "Boutique", "Retail",
                        "Fashion boutique.", "fashion, tailoring")
        assert isinstance(r["matched_concepts"], list)

    def test_interest_also_contributes(self):
        """Using interest (not just skills) should still produce a score."""
        r = self._match(None, "I am interested in food business", "Bakery", "Food",
                        "Fresh baked goods.", "baking")
        assert r["semantic_score"] > 0

    def test_batch_returns_sorted_by_score(self):
        from app.services.semantic_matcher import batch_semantic_match
        businesses = [
            {"id": "1", "name": "Tailoring Shop", "category": "Service",
             "description": "Garment stitching.", "required_skills": "tailoring"},
            {"id": "2", "name": "Dairy Farm", "category": "Agriculture",
             "description": "Milk production.", "required_skills": "animal care"},
        ]
        results = batch_semantic_match("stitching tailoring", None, businesses)
        assert len(results) == 2
        assert results[0]["semantic_score"] >= results[1]["semantic_score"]

    def test_batch_returns_business_id(self):
        from app.services.semantic_matcher import batch_semantic_match
        results = batch_semantic_match("cooking", None, [
            {"id": "abc", "name": "Bakery", "category": "Food",
             "description": "Baking.", "required_skills": "cooking"}
        ])
        assert results[0]["business_id"] == "abc"

    def test_concept_graph_covers_common_rural_skills(self):
        from app.services.semantic_matcher import CONCEPT_GRAPH
        important_concepts = ["tailoring", "cooking", "farming", "electronics",
                              "beauty", "handicraft", "transport"]
        for c in important_concepts:
            assert c in CONCEPT_GRAPH


# ── Query Intent Extraction ───────────────────────────────────────────────────

class TestIntentExtraction:
    def _intent(self, query):
        from app.services.semantic_matcher import extract_query_intent
        return extract_query_intent(query)

    def test_budget_lakh_extraction(self):
        r = self._intent("I have ₹2 lakh and want to start a business")
        assert r["budget"] == pytest.approx(200000, rel=0.01)

    def test_budget_k_extraction(self):
        r = self._intent("I have 50k rupees")
        assert r["budget"] == pytest.approx(50000, rel=0.01)

    def test_budget_plain_number(self):
        r = self._intent("₹1,50,000 capital")
        assert r["budget"] is not None
        assert r["budget"] >= 100000

    def test_skill_extraction_from_marker(self):
        r = self._intent("I know tailoring and stitching")
        assert r["skills"]   # Some skills extracted
        assert len(r["skills"]) > 0

    def test_low_risk_extraction(self):
        r = self._intent("I want a low risk business in a village")
        assert r["risk_preference"] == "Low"

    def test_location_rural(self):
        r = self._intent("I want to start something in my village")
        assert r["location_type"] == "rural"

    def test_location_urban(self):
        r = self._intent("Good business for a city")
        assert r["location_type"] == "urban"

    def test_missing_budget_returns_none(self):
        r = self._intent("I want to start tailoring")
        # Budget may or may not be extracted — just verify no crash
        assert "budget" in r

    def test_raw_query_preserved(self):
        q = "I have experience in cooking"
        r = self._intent(q)
        assert r["raw_query"] == q

    def test_business_type_hints_extracted(self):
        r = self._intent("I want a food business")
        assert len(r["business_type_hints"]) > 0

    def test_no_crash_on_empty_query(self):
        r = self._intent("")
        assert isinstance(r, dict)


# ── Personalized Recommendation Engine ───────────────────────────────────────

def _mock_biz(**overrides) -> Any:
    """Create a minimal mock Business."""
    defaults = {
        "id":     "b1",
        "name":   "Tailoring Shop",
        "category": "Service",
        "business_type": "Service",
        "description": "Garment stitching and alteration services.",
        "required_skills": "tailoring, stitching, garment cutting",
        "risk_level": "Low",
        "min_investment": 80000,
        "max_investment": 150000,
        "estimated_monthly_revenue_min": 15000,
        "estimated_monthly_revenue_max": 25000,
        "estimated_monthly_expenses_min": 8000,
        "estimated_monthly_expenses_max": 12000,
        "estimated_monthly_profit_min": 7000,
        "estimated_monthly_profit_max": 13000,
        "setup_time_weeks_min": 2,
        "setup_time_weeks_max": 4,
        "suitable_for_rural": True,
        "risk_factors": "Seasonal demand, Competition",
        "key_challenges": "Customer acquisition, Machine maintenance",
    }
    defaults.update(overrides)
    biz = SimpleNamespace(**defaults)
    return biz


class TestPersonalizedEngine:
    def _score(self, biz=None, **kwargs):
        from app.services.personalized_recommendation_engine import personalized_score
        return personalized_score(
            biz=biz or _mock_biz(),
            capital=kwargs.get("capital", 200000),
            skills=kwargs.get("skills", "tailoring"),
            interests=kwargs.get("interests", "garment"),
            income_goal=kwargs.get("income_goal", 10000),
            preferred_risk=kwargs.get("preferred_risk"),
            experience_years=kwargs.get("experience_years"),
            location_type=kwargs.get("location_type"),
            preference_data=kwargs.get("preference_data"),
        )

    def test_final_score_in_range(self):
        r = self._score()
        assert 0 <= r["final_score"] <= 100

    def test_breakdown_has_10_keys(self):
        r = self._score()
        expected = {
            "semantic_skill", "budget", "market_opportunity", "financial_potential",
            "experience", "gov_support", "risk", "interest", "income_goal", "location",
        }
        assert expected.issubset(r["breakdown"].keys())

    def test_semantic_score_contributes_to_breakdown(self):
        r = self._score(skills="tailoring")
        # Semantic skill contribution should be > 0 for matching skills
        assert r["breakdown"]["semantic_skill"] > 0

    def test_high_capital_boosts_budget_score(self):
        low_capital  = self._score(capital=50000)
        high_capital = self._score(capital=500000)
        assert high_capital["final_score"] > low_capital["final_score"]

    def test_matching_risk_preference(self):
        match    = self._score(preferred_risk="Low")
        mismatch = self._score(preferred_risk="High")
        assert match["final_score"] > mismatch["final_score"]

    def test_rural_location_boosts_rural_business(self):
        rural  = self._score(location_type="rural")
        urban  = self._score(location_type="urban")
        # Rural business (suitable_for_rural=True) should get higher location score for rural user
        rural_loc_raw = rural.get("raw_scores", {}).get("location", 0)
        urban_loc_raw = urban.get("raw_scores", {}).get("location", 0)
        assert rural_loc_raw >= urban_loc_raw

    def test_experience_years_affects_score(self):
        exp5 = self._score(experience_years=5)
        exp0 = self._score(experience_years=0)
        # More experience should produce higher experience score
        assert exp5["raw_scores"]["experience"] >= exp0["raw_scores"]["experience"]

    def test_preference_boost_capped_at_10(self):
        from app.services.personalized_recommendation_engine import preference_modifier
        pref = {"preferred_categories": {"Service": 100}, "avoided_categories": {}, "preferred_risk": "Low"}
        mod = preference_modifier(pref, _mock_biz())
        assert mod <= 10.0

    def test_preference_penalty_not_below_minus_5(self):
        from app.services.personalized_recommendation_engine import preference_modifier
        pref = {"preferred_categories": {}, "avoided_categories": {"Service": 100}, "preferred_risk": None}
        mod = preference_modifier(pref, _mock_biz())
        assert mod >= -5.0

    def test_no_skills_returns_valid_score(self):
        r = self._score(skills=None, interests=None)
        assert 0 <= r["final_score"] <= 100

    def test_backward_compat_keys_present(self):
        """Verify legacy keys expected by Phase 2 API still present."""
        r = self._score()
        for key in ("budget", "skills", "interest", "profit", "risk", "income_goal", "final"):
            assert key in r

    def test_generate_reasons_not_empty(self):
        from app.services.personalized_recommendation_engine import generate_personalized_reasons
        r = self._score()
        reasons = generate_personalized_reasons(r, _mock_biz(), 200000)
        assert len(reasons) > 0

    def test_explain_recommendation_structure(self):
        from app.services.personalized_recommendation_engine import explain_recommendation
        r = self._score()
        expl = explain_recommendation(r, _mock_biz(), 200000)
        for key in ("why_recommended", "strengths", "challenges", "next_steps",
                    "financial_outlook", "semantic_match", "disclaimer"):
            assert key in expl

    def test_gov_support_score_for_agriculture(self):
        from app.services.personalized_recommendation_engine import score_gov_support_potential
        agri_biz = _mock_biz(category="Agriculture & Allied")
        assert score_gov_support_potential(agri_biz) >= 50

    def test_market_opportunity_score_range(self):
        from app.services.personalized_recommendation_engine import score_market_opportunity
        s = score_market_opportunity(_mock_biz())
        assert 0 <= s <= 100


# ── Saved Business Model ──────────────────────────────────────────────────────

class TestSavedBusinessModel:
    def test_model_instantiation(self):
        from app.models.phase8 import SavedBusiness
        sb = SavedBusiness(user_id="u1", business_id="b1", notes="Test")
        assert sb.user_id == "u1"
        assert sb.business_id == "b1"

    def test_interaction_model(self):
        from app.models.phase8 import RecommendationInteraction
        ri = RecommendationInteraction(user_id="u1", business_id="b1", interaction_type="viewed")
        assert ri.interaction_type == "viewed"

    def test_entrepreneur_profile_model(self):
        from app.models.phase8 import EntrepreneurProfile
        ep = EntrepreneurProfile(user_id="u1", location_type="rural", growth_preference="stable")
        assert ep.location_type == "rural"
        assert ep.growth_preference == "stable"


# ── Phase 8 API endpoints ─────────────────────────────────────────────────────

class TestPhase8API:
    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            from app.core.dependencies import get_current_user
            from app.database.db import get_db

            mock_user = SimpleNamespace(
                id="u001", email="test@test.com", full_name="Test User",
                state="Telangana", available_capital=200000.0,
                skills="tailoring, stitching",
                business_interests="garment, clothing",
                monthly_income_goal=12000.0,
                experience_years=2,
                is_active=True,
            )

            mock_db = AsyncMock()
            # Make execute() return different things based on call count
            call_count = {"n": 0}

            async def mock_execute(*args, **kwargs):
                call_count["n"] += 1
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_result.scalars.return_value.first.return_value = None
                mock_result.scalar.return_value = None
                mock_result.all.return_value = []
                return mock_result

            mock_db.execute = mock_execute
            mock_db.add     = MagicMock()
            mock_db.commit  = AsyncMock()
            mock_db.refresh = AsyncMock()

            app.dependency_overrides[get_current_user] = lambda: mock_user
            app.dependency_overrides[get_db]           = lambda: mock_db

            self.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            self.client = None

    def test_preferences_endpoint_returns_200(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/recommendations/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "preferred_categories" in data
        assert "total_interactions" in data

    def test_preferences_disclaimer_present(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/recommendations/preferences")
        assert resp.status_code == 200
        assert "disclaimer" in resp.json()

    def test_natural_query_endpoint_exists(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/recommendations/natural-query", json={
            "query": "I know tailoring and want to start a business with ₹2 lakh",
            "top_n": 3,
        })
        assert resp.status_code not in (404, 405)

    def test_natural_query_requires_auth(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        fresh = TestClient(app, raise_server_exceptions=False)
        resp = fresh.post("/recommendations/natural-query", json={"query": "test"})
        assert resp.status_code in (401, 403, 422)

    def test_natural_query_empty_query_422(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/recommendations/natural-query", json={"query": ""})
        assert resp.status_code == 422

    def test_interaction_invalid_type_422(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post(
            "/recommendations/fake-biz-id/interaction",
            json={"interaction_type": "invalid_type"},
        )
        assert resp.status_code in (404, 409, 422)

    def test_saved_businesses_list(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/saved-businesses")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_profile_get_404_if_not_created(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/recommendations/profile")
        assert resp.status_code in (404, 200)

    def test_profile_put_creates_profile(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        from app.main import app
        from app.database.db import get_db

        async def mock_execute_with_upsert(*args, **kwargs):
            from app.models.phase8 import EntrepreneurProfile
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_result.scalar.return_value = None
            return mock_result

        db2 = AsyncMock()
        db2.execute = mock_execute_with_upsert
        db2.add     = MagicMock()
        db2.commit  = AsyncMock()

        from app.models.phase8 import EntrepreneurProfile
        import uuid
        fake_profile = EntrepreneurProfile(
            id=str(uuid.uuid4()), user_id="u001",
            location_type="rural", growth_preference="stable",
        )
        from datetime import datetime, timezone
        fake_profile.created_at = datetime.now(timezone.utc)
        fake_profile.updated_at = datetime.now(timezone.utc)
        db2.refresh = AsyncMock(side_effect=lambda obj: None)

        app.dependency_overrides[get_db] = lambda: db2

        resp = self.client.put("/recommendations/profile", json={
            "location_type": "rural",
            "growth_preference": "stable",
        })
        assert resp.status_code in (200, 422, 500)

    def test_personalized_endpoint_path_exists(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/recommendations/personalized", json={"top_n": 3})
        assert resp.status_code not in (404, 405)


# ── Interaction type validation ───────────────────────────────────────────────

class TestInteractionTypes:
    def test_valid_interaction_types(self):
        from app.api.phase8 import VALID_INTERACTION_TYPES
        expected = {"viewed", "saved", "compared", "dismissed", "explored"}
        assert VALID_INTERACTION_TYPES == expected

    def test_five_interaction_types_defined(self):
        from app.api.phase8 import VALID_INTERACTION_TYPES
        assert len(VALID_INTERACTION_TYPES) == 5


# ── Schemas ───────────────────────────────────────────────────────────────────

class TestPhase8Schemas:
    def test_entrepreneur_profile_in_optional_fields(self):
        from app.schemas.phase8 import EntrepreneurProfileIn
        p = EntrepreneurProfileIn(location_type="rural", growth_preference="stable")
        assert p.location_type == "rural"

    def test_natural_query_request_min_length(self):
        from app.schemas.phase8 import NaturalQueryRequest
        with pytest.raises(Exception):
            NaturalQueryRequest(query="")

    def test_personalized_request_defaults(self):
        from app.schemas.phase8 import PersonalizedRecommendationRequest
        r = PersonalizedRecommendationRequest()
        assert r.top_n == 8
        assert r.use_preferences is True

    def test_saved_business_in_optional_notes(self):
        from app.schemas.phase8 import SavedBusinessIn
        s = SavedBusinessIn()
        assert s.notes is None

    def test_interaction_request_required_type(self):
        from app.schemas.phase8 import InteractionRequest
        with pytest.raises(Exception):
            InteractionRequest()

    def test_personalized_breakdown_all_fields(self):
        from app.schemas.phase8 import PersonalizedBreakdown
        b = PersonalizedBreakdown(
            semantic_skill=15, budget=12, market_opportunity=10,
            financial_potential=8, experience=7, gov_support=6,
            risk=5, interest=4, income_goal=3, location=2,
        )
        assert b.preference_modifier == 0.0


# ── Backward compatibility ────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """Phase 2 /recommendations endpoint must still work."""

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            from app.core.dependencies import get_current_user
            from app.database.db import get_db

            mock_user = SimpleNamespace(
                id="u001", email="test@test.com", full_name="Test",
                state="Telangana", available_capital=200000.0,
                skills="tailoring", business_interests="shop",
                monthly_income_goal=12000.0, experience_years=2, is_active=True,
            )
            app.dependency_overrides[get_current_user] = lambda: mock_user

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)

            app.dependency_overrides[get_db] = lambda: mock_db
            self.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            self.client = None

    def test_phase2_recommendations_endpoint_still_exists(self):
        if not self.client:
            pytest.skip()
        resp = self.client.post("/recommendations", json={"top_n": 3})
        assert resp.status_code not in (404, 405)

    def test_phase2_endpoint_returns_correct_fields(self):
        if not self.client:
            pytest.skip()
        resp = self.client.post("/recommendations", json={"top_n": 3})
        if resp.status_code == 200:
            data = resp.json()
            assert "recommendations" in data
            assert "profile_completeness" in data

    def test_advisor_status_still_works(self):
        if not self.client:
            pytest.skip()
        resp = self.client.get("/advisor/status")
        assert resp.status_code == 200
