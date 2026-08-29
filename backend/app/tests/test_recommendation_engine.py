"""
Unit tests for the recommendation engine.
Run with: python -m pytest app/tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from app.models.business import Business
from app.services.recommendation_engine import (
    score_budget,
    score_skills,
    score_interest,
    score_profit,
    score_risk,
    score_income_goal,
    score_business,
    profile_completeness,
    WEIGHTS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

from types import SimpleNamespace

def make_biz(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id="test-id",
        name="Test Business",
        category="Services",
        description="A test business for tailoring and sewing",
        business_type="Service",
        suitable_for_rural=True,
        min_investment=50000,
        max_investment=150000,
        estimated_monthly_revenue_min=20000,
        estimated_monthly_revenue_max=50000,
        estimated_monthly_expenses_min=10000,
        estimated_monthly_expenses_max=25000,
        estimated_monthly_profit_min=10000,
        estimated_monthly_profit_max=25000,
        risk_level="Medium",
        required_skills="Tailoring, Sewing, Customer service",
        risk_factors="Seasonal demand",
        key_challenges="Building clientele",
        setup_time_weeks_min=2,
        setup_time_weeks_max=4,
        is_demo_data=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)



class FakeUser:
    available_capital = None
    skills = None
    business_interests = None
    monthly_income_goal = None
    state = None
    district = None
    experience_years = None


# ─────────────────────────────────────────────────────────────────────────────
# Budget score tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBudgetScore:
    def test_capital_above_max(self):
        biz = make_biz(min_investment=50000, max_investment=100000)
        assert score_budget(150000, biz) == 100.0

    def test_capital_equals_max(self):
        biz = make_biz(min_investment=50000, max_investment=100000)
        assert score_budget(100000, biz) == 100.0

    def test_capital_between_min_and_max(self):
        biz = make_biz(min_investment=50000, max_investment=150000)
        score = score_budget(100000, biz)  # midpoint
        assert 70 < score < 100

    def test_capital_at_minimum(self):
        biz = make_biz(min_investment=50000, max_investment=150000)
        score = score_budget(50000, biz)
        assert score == pytest.approx(70.0)

    def test_capital_slightly_below_min(self):
        """80-99% of min → should score 30-70."""
        biz = make_biz(min_investment=100000, max_investment=200000)
        score = score_budget(90000, biz)  # 90% of min
        assert 30 <= score <= 70

    def test_capital_half_of_min(self):
        """50% of min → very low score."""
        biz = make_biz(min_investment=100000, max_investment=200000)
        score = score_budget(50000, biz)
        assert score <= 30

    def test_capital_very_low(self):
        """Much less than min → near 0."""
        biz = make_biz(min_investment=100000, max_investment=200000)
        score = score_budget(10000, biz)
        assert score < 15

    def test_no_capital(self):
        """None capital → neutral score 40."""
        biz = make_biz()
        assert score_budget(None, biz) == 40.0

    def test_zero_capital(self):
        """Zero capital → neutral score 40."""
        biz = make_biz()
        assert score_budget(0, biz) == 40.0

    def test_capital_exceeds_expensive_biz(self):
        """Capital ₹5 lakh, business needs ₹2-3 lakh → 100."""
        biz = make_biz(min_investment=200000, max_investment=300000)
        assert score_budget(500000, biz) == 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Skill score tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSkillScore:
    def test_perfect_skill_match(self):
        biz = make_biz(required_skills="Tailoring, Sewing, Customer service")
        score = score_skills("tailoring, sewing, customer service", biz)
        assert score >= 90

    def test_partial_skill_match(self):
        biz = make_biz(required_skills="Tailoring, Sewing, Design")
        score = score_skills("Tailoring", biz)
        assert 30 <= score <= 80

    def test_no_skill_match(self):
        biz = make_biz(required_skills="Welding, Mechanical")
        score = score_skills("Cooking, Baking", biz)
        assert score < 50

    def test_no_skills_entered(self):
        """No skills → neutral-low 35."""
        biz = make_biz()
        assert score_skills(None, biz) == 35.0
        assert score_skills("", biz) == 35.0

    def test_case_insensitive(self):
        biz = make_biz(required_skills="MOBILE REPAIR, Electronics")
        score = score_skills("mobile repair", biz)
        assert score >= 50

    def test_keyword_in_skill(self):
        """'mobile' in 'mobile repair' should count as a match."""
        biz = make_biz(required_skills="Mobile repair, Soldering")
        score = score_skills("mobile, soldering", biz)
        assert score >= 50


# ─────────────────────────────────────────────────────────────────────────────
# Interest match tests
# ─────────────────────────────────────────────────────────────────────────────

class TestInterestScore:
    def test_direct_match(self):
        biz = make_biz(name="Tailoring & Boutique", category="Services")
        score = score_interest("tailoring boutique", biz)
        assert score >= 70

    def test_no_interests(self):
        biz = make_biz()
        assert score_interest(None, biz) == 50.0
        assert score_interest("", biz) == 50.0

    def test_category_match(self):
        biz = make_biz(category="Agriculture & Allied", name="Dairy Farming")
        score = score_interest("dairy farming agriculture", biz)
        assert score >= 70

    def test_no_match(self):
        biz = make_biz(name="Welding Workshop", category="Manufacturing",
                       description="Heavy metal fabrication and structural work",
                       business_type="Manufacturing")
        score = score_interest("bakery cake cooking food", biz)
        assert score < 60


# ─────────────────────────────────────────────────────────────────────────────
# Profit potential tests
# ─────────────────────────────────────────────────────────────────────────────

class TestProfitScore:
    def test_high_margin(self):
        """40%+ margin → high score."""
        biz = make_biz(
            estimated_monthly_revenue_min=30000, estimated_monthly_revenue_max=50000,
            estimated_monthly_profit_min=15000, estimated_monthly_profit_max=25000,
        )
        assert score_profit(biz) >= 80

    def test_low_margin(self):
        """<10% margin → low score."""
        biz = make_biz(
            estimated_monthly_revenue_min=80000, estimated_monthly_revenue_max=100000,
            estimated_monthly_profit_min=5000,  estimated_monthly_profit_max=8000,
        )
        assert score_profit(biz) < 25

    def test_zero_revenue(self):
        biz = make_biz(
            estimated_monthly_revenue_min=0, estimated_monthly_revenue_max=0,
            estimated_monthly_profit_min=0, estimated_monthly_profit_max=0,
        )
        assert score_profit(biz) == 50.0


# ─────────────────────────────────────────────────────────────────────────────
# Risk score tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskScore:
    def test_no_preference_low(self):
        biz = make_biz(risk_level="Low")
        assert score_risk(biz, None) == 90.0

    def test_no_preference_medium(self):
        biz = make_biz(risk_level="Medium")
        assert score_risk(biz, None) == 75.0

    def test_no_preference_high(self):
        biz = make_biz(risk_level="High")
        assert score_risk(biz, None) == 55.0

    def test_preference_matches(self):
        biz = make_biz(risk_level="Low")
        assert score_risk(biz, "Low") == 100.0

    def test_adjacent_mismatch(self):
        biz = make_biz(risk_level="Medium")
        assert score_risk(biz, "Low") == 60.0

    def test_opposite_mismatch(self):
        biz = make_biz(risk_level="High")
        assert score_risk(biz, "Low") == 20.0

    def test_any_preference(self):
        biz = make_biz(risk_level="High")
        assert score_risk(biz, "Any") == 55.0


# ─────────────────────────────────────────────────────────────────────────────
# Income goal tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIncomeGoalScore:
    def test_goal_easily_met(self):
        biz = make_biz(estimated_monthly_profit_min=20000, estimated_monthly_profit_max=40000)
        score = score_income_goal(20000, biz)  # max_profit=40000, goal=20000 → ratio=2
        assert score == 100.0

    def test_goal_just_met(self):
        biz = make_biz(estimated_monthly_profit_min=18000, estimated_monthly_profit_max=22000)
        score = score_income_goal(20000, biz)  # ratio ~1.1
        assert 80 <= score <= 100

    def test_goal_nearly_met(self):
        biz = make_biz(estimated_monthly_profit_min=10000, estimated_monthly_profit_max=18000)
        score = score_income_goal(20000, biz)  # ratio 0.9
        assert 50 <= score < 80

    def test_goal_not_met(self):
        biz = make_biz(estimated_monthly_profit_min=5000, estimated_monthly_profit_max=10000)
        score = score_income_goal(30000, biz)  # ratio 0.33
        assert score < 30

    def test_no_goal(self):
        biz = make_biz()
        assert score_income_goal(None, biz) == 60.0

    def test_zero_goal(self):
        biz = make_biz()
        assert score_income_goal(0, biz) == 60.0


# ─────────────────────────────────────────────────────────────────────────────
# Final weighted score
# ─────────────────────────────────────────────────────────────────────────────

class TestFinalScore:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_score_in_range(self):
        biz = make_biz()
        scores = score_business(biz, 100000, "tailoring, sewing", "tailoring", 20000, None)
        assert 0 <= scores["final"] <= 100

    def test_no_profile_info(self):
        """With no profile info, should still return a valid score."""
        biz = make_biz()
        scores = score_business(biz, None, None, None, None, None)
        assert 0 <= scores["final"] <= 100

    def test_perfect_match_is_high(self):
        """Ideal profile for the business should yield a high score."""
        biz = make_biz(
            min_investment=50000, max_investment=100000,
            estimated_monthly_profit_min=20000, estimated_monthly_profit_max=30000,
            risk_level="Low",
            required_skills="Tailoring, Sewing",
        )
        scores = score_business(
            biz, 200000, "tailoring, sewing, cutting", "tailoring boutique", 20000, "Low"
        )
        assert scores["final"] >= 80

    def test_impossible_business_is_low(self):
        """Business needs ₹5 lakh, user has ₹20k → should be low score."""
        biz = make_biz(
            min_investment=500000, max_investment=1000000,
            required_skills="Engineering, Machinery",
        )
        scores = score_business(biz, 20000, "tailoring", "tailoring", 10000, None)
        assert scores["final"] < 50


# ─────────────────────────────────────────────────────────────────────────────
# Profile completeness
# ─────────────────────────────────────────────────────────────────────────────

class TestProfileCompleteness:
    def test_empty_profile(self):
        user = FakeUser()
        assert profile_completeness(user) == 0

    def test_full_profile(self):
        user = FakeUser()
        user.available_capital = 100000
        user.skills = "Tailoring"
        user.business_interests = "Boutique"
        user.monthly_income_goal = 20000
        user.state = "Telangana"
        user.district = "Hyderabad"
        user.experience_years = 3
        assert profile_completeness(user) == 100

    def test_partial_profile(self):
        user = FakeUser()
        user.available_capital = 100000
        user.skills = "Tailoring"
        # 2/7 fields
        pct = profile_completeness(user)
        assert 0 < pct < 50
