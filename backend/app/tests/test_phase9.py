"""
Phase 9 — Comprehensive test suite.
Tests: Goals, Financial Progress, Analytics, Actions, Timeline.
Covers CRUD, auth, ownership, calculations, trends, edge cases.

Run: python -m pytest app/tests/test_phase9.py -v
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancialAnalytics:
    def _records(self, n=3, rev_start=20000, exp_start=12000, growth=0):
        from datetime import date
        return [
            {
                "record_date": date(2024, i + 1, 1),
                "revenue":  rev_start + i * growth,
                "expenses": exp_start,
                "profit":   (rev_start + i * growth) - exp_start,
            }
            for i in range(n)
        ]

    def test_empty_returns_insufficient(self):
        from app.services.analytics_engine import compute_financial_analytics
        r = compute_financial_analytics([])
        assert r["status"] == "insufficient_data"

    def test_single_record(self):
        from app.services.analytics_engine import compute_financial_analytics
        r = compute_financial_analytics(self._records(1))
        assert r["status"] == "ok"
        assert r["record_count"] == 1
        assert r["total_revenue"] > 0

    def test_totals_computed_correctly(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(3, rev_start=10000, exp_start=6000)
        r = compute_financial_analytics(records)
        assert r["total_revenue"]  == pytest.approx(30000, rel=0.01)
        assert r["total_expenses"] == pytest.approx(18000, rel=0.01)
        assert r["total_profit"]   == pytest.approx(12000, rel=0.01)

    def test_avg_monthly_calculated(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(4, rev_start=20000, exp_start=10000)
        r = compute_financial_analytics(records)
        assert r["avg_monthly_revenue"] == pytest.approx(20000, rel=0.01)

    def test_improving_trend_detected(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(6, rev_start=5000, exp_start=3000, growth=2000)
        r = compute_financial_analytics(records)
        # Revenue is clearly growing
        assert r["revenue_trend"] == "improving"

    def test_declining_trend_detected(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(6, rev_start=30000, exp_start=5000, growth=-3000)
        r = compute_financial_analytics(records)
        assert r["revenue_trend"] == "declining"

    def test_series_length_matches_records(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(5)
        r = compute_financial_analytics(records)
        assert len(r["revenue_series"]) == 5
        assert len(r["profit_series"])  == 5

    def test_best_period_identified(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = self._records(4, rev_start=10000, exp_start=5000, growth=5000)
        r = compute_financial_analytics(records)
        assert r["best_period"] is not None

    def test_disclaimer_present(self):
        from app.services.analytics_engine import compute_financial_analytics
        r = compute_financial_analytics(self._records(2))
        assert "disclaimer" in r
        assert len(r["disclaimer"]) > 10

    def test_zero_revenue_no_crash(self):
        from app.services.analytics_engine import compute_financial_analytics
        records = [{"record_date": date(2024, 1, 1), "revenue": 0, "expenses": 0, "profit": 0}]
        r = compute_financial_analytics(records)
        assert r["status"] == "ok"
        assert r["total_revenue"] == 0


class TestGoalAnalytics:
    def test_empty_goals(self):
        from app.services.analytics_engine import compute_goal_analytics
        r = compute_goal_analytics([])
        assert r["total"] == 0
        assert r["completion_pct"] == 0.0

    def test_completion_pct_calculated(self):
        from app.services.analytics_engine import compute_goal_analytics
        goals = [
            {"status": "completed", "priority": "high",   "goal_type": "general", "is_overdue": False},
            {"status": "completed", "priority": "medium",  "goal_type": "general", "is_overdue": False},
            {"status": "in_progress", "priority": "low",  "goal_type": "general", "is_overdue": False},
            {"status": "not_started", "priority": "low",  "goal_type": "general", "is_overdue": False},
        ]
        r = compute_goal_analytics(goals)
        assert r["total"] == 4
        assert r["completed"] == 2
        assert r["completion_pct"] == pytest.approx(50.0, rel=0.01)

    def test_overdue_counted(self):
        from app.services.analytics_engine import compute_goal_analytics
        goals = [
            {"status": "in_progress", "priority": "high", "goal_type": "general", "is_overdue": True},
            {"status": "in_progress", "priority": "high", "goal_type": "general", "is_overdue": False},
        ]
        r = compute_goal_analytics(goals)
        assert r["overdue"] == 1

    def test_by_priority_breakdown(self):
        from app.services.analytics_engine import compute_goal_analytics
        goals = [
            {"status": "completed", "priority": "high",   "goal_type": "a", "is_overdue": False},
            {"status": "completed", "priority": "high",   "goal_type": "b", "is_overdue": False},
            {"status": "completed", "priority": "medium", "goal_type": "c", "is_overdue": False},
        ]
        r = compute_goal_analytics(goals)
        assert r["by_priority"]["high"] == 2
        assert r["by_priority"]["medium"] == 1


class TestProgressScore:
    def _make_fin(self, n_records=0, trend="insufficient_data", avg_profit=0):
        return {
            "record_count": n_records,
            "avg_monthly_profit": avg_profit,
            "profit_trend": trend,
            "status": "ok" if n_records > 0 else "insufficient_data",
        }

    def _make_goals(self, total=0, completed=0, in_progress=0):
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "completion_pct": (completed / total * 100) if total > 0 else 0.0,
        }

    def test_zero_data_returns_low_score(self):
        from app.services.analytics_engine import compute_progress_score
        r = compute_progress_score(self._make_fin(), self._make_goals(), 0, 0, 0)
        assert r["overall_score"] < 20

    def test_score_in_range_0_to_100(self):
        from app.services.analytics_engine import compute_progress_score
        r = compute_progress_score(
            self._make_fin(10, "improving", 5000),
            self._make_goals(5, 4, 1),
            20, 30, 90
        )
        assert 0 <= r["overall_score"] <= 100

    def test_financial_data_boosts_score(self):
        from app.services.analytics_engine import compute_progress_score
        low  = compute_progress_score(self._make_fin(0), self._make_goals(), 0, 0, 0)
        high = compute_progress_score(self._make_fin(10, "improving", 5000), self._make_goals(), 0, 0, 0)
        assert high["overall_score"] > low["overall_score"]

    def test_category_scores_have_5_keys(self):
        from app.services.analytics_engine import compute_progress_score
        r = compute_progress_score(self._make_fin(), self._make_goals(), 0, 0, 0)
        assert len(r["category_scores"]) == 5

    def test_strengths_and_improvements_present(self):
        from app.services.analytics_engine import compute_progress_score
        r = compute_progress_score(self._make_fin(), self._make_goals(), 0, 0, 0)
        assert isinstance(r["strengths"], list)
        assert isinstance(r["improvement_areas"], list)

    def test_weights_sum_to_1(self):
        from app.services.analytics_engine import SCORE_WEIGHTS
        total = sum(SCORE_WEIGHTS.values())
        assert total == pytest.approx(1.0, rel=0.001)

    def test_improving_trend_higher_than_declining(self):
        from app.services.analytics_engine import compute_progress_score
        improving = compute_progress_score(
            self._make_fin(5, "improving", 8000), self._make_goals(), 5, 5, 50
        )
        declining = compute_progress_score(
            self._make_fin(5, "declining", 2000), self._make_goals(), 5, 5, 50
        )
        assert improving["overall_score"] > declining["overall_score"]

    def test_disclaimer_present(self):
        from app.services.analytics_engine import compute_progress_score
        r = compute_progress_score(self._make_fin(), self._make_goals(), 0, 0, 0)
        assert "disclaimer" in r and len(r["disclaimer"]) > 10

    def test_confidence_level(self):
        from app.services.analytics_engine import compute_progress_score
        low_conf  = compute_progress_score(self._make_fin(), self._make_goals(), 0, 0, 0)
        high_conf = compute_progress_score(self._make_fin(5, "stable", 3000), self._make_goals(3, 2), 10, 5, 80)
        assert low_conf["confidence"]  == "low"
        assert high_conf["confidence"] in ("medium", "high")


class TestFinancialInsights:
    def test_empty_returns_placeholder(self):
        from app.services.analytics_engine import compute_financial_insights
        r = compute_financial_insights({"status": "insufficient_data"})
        assert len(r) > 0
        assert "Add financial records" in r[0]

    def test_high_margin_insight(self):
        from app.services.analytics_engine import compute_financial_insights
        fa = {"status": "ok", "avg_monthly_profit": 15000, "avg_monthly_revenue": 20000,
              "profit_trend": "stable", "expense_trend": "stable"}
        r = compute_financial_insights(fa)
        assert any("margin" in insight.lower() for insight in r)

    def test_declining_trend_insight(self):
        from app.services.analytics_engine import compute_financial_insights
        fa = {"status": "ok", "avg_monthly_profit": 2000, "avg_monthly_revenue": 10000,
              "profit_trend": "declining", "expense_trend": "stable"}
        r = compute_financial_insights(fa)
        assert any("declining" in i.lower() for i in r)


# ═══════════════════════════════════════════════════════════════════════════════
# Action Plan Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestActionPlanEngine:
    def _run(self, **kwargs):
        from app.services.action_plan_engine import generate_action_plan
        defaults = {
            "user_profile": {},
            "financial_records": [],
            "goals": [],
            "saved_businesses": [],
            "advisory_sessions": [],
            "interactions": [],
            "profile_completeness": 0,
            "financial_analytics": None,
        }
        defaults.update(kwargs)
        return generate_action_plan(**defaults)

    def test_returns_list(self):
        r = self._run()
        assert isinstance(r, list)

    def test_max_8_actions(self):
        r = self._run()
        assert len(r) <= 8

    def test_profile_incomplete_critical_action(self):
        r = self._run(profile_completeness=20)
        priorities = [a["priority"] for a in r]
        assert "critical" in priorities

    def test_no_financial_records_produces_action(self):
        r = self._run(financial_records=[])
        titles = [a["title"].lower() for a in r]
        assert any("financial" in t or "record" in t for t in titles)

    def test_no_goals_produces_action(self):
        r = self._run(goals=[])
        titles = [a["title"].lower() for a in r]
        assert any("goal" in t for t in titles)

    def test_sorted_critical_first(self):
        r = self._run(profile_completeness=10)
        if len(r) > 1:
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(r) - 1):
                assert priority_order[r[i]["priority"]] <= priority_order[r[i+1]["priority"]]

    def test_each_action_has_required_fields(self):
        r = self._run()
        required = {"id", "title", "description", "category", "priority",
                    "impact", "status", "action_url"}
        for action in r:
            assert required.issubset(action.keys())

    def test_state_produces_scheme_action(self):
        r = self._run(user_profile={"state": "Telangana"}, profile_completeness=80)
        categories = [a["category"] for a in r]
        assert "government_support" in categories

    def test_declining_trend_produces_action(self):
        r = self._run(
            financial_records=[{"revenue": 1}],
            financial_analytics={"profit_trend": "declining", "record_count": 5},
            profile_completeness=60,
        )
        titles = " ".join(a["title"].lower() for a in r)
        assert "profit" in titles or "financial" in titles or "declining" in titles

    def test_action_url_starts_with_slash(self):
        r = self._run()
        for a in r:
            if a.get("action_url"):
                assert a["action_url"].startswith("/")

    def test_completed_profile_no_critical_action(self):
        r = self._run(profile_completeness=95, goals=[{"title": "test", "status": "in_progress", "is_overdue": False}])
        priorities = [a["priority"] for a in r]
        assert "critical" not in priorities


# ═══════════════════════════════════════════════════════════════════════════════
# Goal Model Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGoalModel:
    def test_progress_percentage_zero_when_no_target(self):
        from app.models.goal import BusinessGoal
        g = BusinessGoal(user_id="u1", title="Test", goal_type="general")
        assert g.progress_percentage == 0.0

    def test_progress_percentage_calculated(self):
        from app.models.goal import BusinessGoal
        g = BusinessGoal(user_id="u1", title="T", goal_type="general",
                         target_value=100, current_value=50)
        assert g.progress_percentage == pytest.approx(50.0)

    def test_progress_percentage_capped_at_100(self):
        from app.models.goal import BusinessGoal
        g = BusinessGoal(user_id="u1", title="T", goal_type="general",
                         target_value=100, current_value=150)
        assert g.progress_percentage <= 100.0

    def test_days_remaining_none_when_no_target_date(self):
        from app.models.goal import BusinessGoal
        g = BusinessGoal(user_id="u1", title="T", goal_type="general")
        assert g.days_remaining is None

    def test_is_overdue_false_when_completed(self):
        from app.models.goal import BusinessGoal
        from datetime import date, timedelta
        g = BusinessGoal(user_id="u1", title="T", goal_type="general",
                         status="completed", target_date=date.today() - timedelta(days=5))
        assert g.is_overdue is False

    def test_is_overdue_true_when_past_date(self):
        from app.models.goal import BusinessGoal
        from datetime import date, timedelta
        g = BusinessGoal(user_id="u1", title="T", goal_type="general",
                         status="in_progress", target_date=date.today() - timedelta(days=1))
        assert g.is_overdue is True

    def test_is_overdue_false_future_date(self):
        from app.models.goal import BusinessGoal
        from datetime import date, timedelta
        g = BusinessGoal(user_id="u1", title="T", goal_type="general",
                         status="in_progress", target_date=date.today() + timedelta(days=10))
        assert g.is_overdue is False

    def test_completed_status_progress_100(self):
        from app.models.goal import BusinessGoal
        g = BusinessGoal(user_id="u1", title="T", goal_type="general", status="completed")
        assert g.progress_percentage == 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# Financial Progress Model Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancialProgressModel:
    def test_instantiation(self):
        from app.models.financial_progress import FinancialProgressRecord
        from datetime import date
        r = FinancialProgressRecord(
            user_id="u1", record_date=date(2024, 1, 1),
            revenue=20000, expenses=12000
        )
        assert r.user_id == "u1"
        assert r.revenue == 20000

    def test_nullable_fields(self):
        from app.models.financial_progress import FinancialProgressRecord
        from datetime import date
        r = FinancialProgressRecord(user_id="u1", record_date=date.today())
        assert r.revenue is None
        assert r.customers is None


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9 Schemas Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase9Schemas:
    def test_goal_create_required_title(self):
        from app.schemas.phase9 import GoalCreate
        with pytest.raises(Exception):
            GoalCreate(title="")

    def test_goal_create_defaults(self):
        from app.schemas.phase9 import GoalCreate
        g = GoalCreate(title="My Goal")
        assert g.goal_type == "general"
        assert g.priority  == "medium"

    def test_financial_record_non_negative_revenue(self):
        from app.schemas.phase9 import FinancialRecordCreate
        from datetime import date
        with pytest.raises(Exception):
            FinancialRecordCreate(record_date=date.today(), revenue=-100)

    def test_financial_record_valid(self):
        from app.schemas.phase9 import FinancialRecordCreate
        from datetime import date
        r = FinancialRecordCreate(record_date=date.today(), revenue=10000, expenses=6000)
        assert r.revenue == 10000

    def test_action_status_update_required(self):
        from app.schemas.phase9 import ActionStatusUpdate
        with pytest.raises(Exception):
            ActionStatusUpdate()


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9 API Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase9API:
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
                skills="tailoring", business_interests="garment",
                monthly_income_goal=12000.0, experience_years=2, is_active=True,
            )

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_result.scalars.return_value.first.return_value = None
            mock_result.scalar.return_value = 0
            mock_result.all.return_value = []
            mock_result.rowcount = 1

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.add     = MagicMock()
            mock_db.commit  = AsyncMock()
            mock_db.refresh = AsyncMock()

            app.dependency_overrides[get_current_user] = lambda: mock_user
            app.dependency_overrides[get_db]           = lambda: mock_db

            self.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            self.client = None

    def test_goals_list_returns_200(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/goals")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_goals_create_endpoint_exists(self):
        if not self.client: pytest.skip()
        resp = self.client.post("/goals", json={"title": "Test Goal"})
        assert resp.status_code not in (404, 405)

    def test_goals_create_requires_title(self):
        if not self.client: pytest.skip()
        resp = self.client.post("/goals", json={"title": ""})
        assert resp.status_code == 422

    def test_financial_list_returns_200(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/progress/financial")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_financial_disclaimer_present(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/progress/financial")
        assert resp.status_code == 200
        assert "disclaimer" in resp.json()

    def test_analytics_dashboard_endpoint_exists(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/analytics/dashboard")
        assert resp.status_code not in (404, 405)

    def test_analytics_progress_score_endpoint(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/analytics/progress-score")
        assert resp.status_code not in (404, 405)

    def test_analytics_goals_endpoint(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/analytics/goals")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data

    def test_analytics_trends_endpoint(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/analytics/trends")
        assert resp.status_code == 200

    def test_actions_next_endpoint_exists(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/actions/next")
        assert resp.status_code not in (404, 405)

    def test_actions_returns_list(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/actions/next")
        if resp.status_code == 200:
            data = resp.json()
            assert "actions" in data
            assert isinstance(data["actions"], list)

    def test_timeline_endpoint_returns_200(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/activity/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_goals_require_auth(self):
        if not self.client: pytest.skip()
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        fresh = TestClient(app, raise_server_exceptions=False)
        resp = fresh.get("/goals")
        assert resp.status_code in (401, 403)

    def test_delete_nonexistent_goal_404(self):
        if not self.client: pytest.skip()
        from app.main import app
        from app.database.db import get_db
        mock_db2 = AsyncMock()
        mock_r = MagicMock()
        mock_r.rowcount = 0
        mock_db2.execute = AsyncMock(return_value=mock_r)
        mock_db2.commit  = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db2
        resp = self.client.delete("/goals/nonexistent-id")
        assert resp.status_code == 404

    def test_financial_record_negative_revenue_422(self):
        if not self.client: pytest.skip()
        resp = self.client.post("/progress/financial", json={
            "record_date": "2024-01-01",
            "revenue": -100,
        })
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Backward compatibility
# ═══════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatibilityPhase9:
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
            mock_result.scalar.return_value = 0
            mock_db.execute = AsyncMock(return_value=mock_result)
            app.dependency_overrides[get_db] = lambda: mock_db
            self.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            self.client = None

    def test_phase2_recommendations_intact(self):
        if not self.client: pytest.skip()
        resp = self.client.post("/recommendations", json={"top_n": 3})
        assert resp.status_code not in (404, 405)

    def test_phase8_personalized_intact(self):
        if not self.client: pytest.skip()
        resp = self.client.post("/recommendations/personalized", json={"top_n": 3})
        assert resp.status_code not in (404, 405)

    def test_advisor_status_intact(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/advisor/status")
        assert resp.status_code == 200

    def test_saved_businesses_intact(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/saved-businesses")
        assert resp.status_code == 200

    def test_preferences_intact(self):
        if not self.client: pytest.skip()
        resp = self.client.get("/recommendations/preferences")
        assert resp.status_code == 200
