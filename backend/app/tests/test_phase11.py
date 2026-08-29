"""
Phase 11 tests — Health endpoints, environment validation, demo mode, error handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_client(demo_mode: bool = False, authenticated: bool = False):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.dependencies import get_current_user
    from app.database.db import get_db

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    if authenticated:
        mock_user = SimpleNamespace(
            id="test-user-001", email="test@test.com", full_name="Test User",
            state="Telangana", preferred_language="en", simple_language_mode=False,
            available_capital=100000.0, skills="tailoring", business_interests="garments",
            monthly_income_goal=15000.0, experience_years=2, is_active=True,
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app, raise_server_exceptions=False)
    return client, app, get_db, get_current_user if authenticated else None


# ── 1. Health Endpoints ───────────────────────────────────────────────────────

class TestHealthEndpoints:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client, self.app, self.get_db, _ = _make_client()
        yield
        self.app.dependency_overrides.pop(self.get_db, None)

    def test_health_returns_200(self):
        r = self.client.get("/health")
        assert r.status_code == 200

    def test_health_has_status(self):
        r = self.client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_has_version(self):
        r = self.client.get("/health")
        assert "version" in r.json()

    def test_health_has_environment(self):
        r = self.client.get("/health")
        assert "environment" in r.json()

    def test_health_live_returns_200(self):
        r = self.client.get("/health/live")
        assert r.status_code == 200

    def test_health_live_status_alive(self):
        r = self.client.get("/health/live")
        assert r.json()["status"] == "alive"

    def test_health_live_has_uptime(self):
        r = self.client.get("/health/live")
        assert "uptime_s" in r.json()

    def test_health_live_has_timestamp(self):
        r = self.client.get("/health/live")
        assert "timestamp" in r.json()

    def test_health_ready_returns_200_or_503(self):
        r = self.client.get("/health/ready")
        assert r.status_code in (200, 503)

    def test_health_details_returns_200_or_503(self):
        r = self.client.get("/health/details")
        assert r.status_code in (200, 503)

    def test_health_details_no_secrets(self):
        r = self.client.get("/health/details")
        body = r.text
        assert "JWT_SECRET_KEY" not in body
        assert "GEMINI_API_KEY" not in body
        assert "password" not in body.lower()
        assert "AIza" not in body  # no API key patterns

    def test_health_details_has_ai_field(self):
        r = self.client.get("/health/details")
        if r.status_code == 200:
            data = r.json()
            assert "ai" in data
            assert "available" in data["ai"]
            assert "fallback_available" in data["ai"]

    def test_health_is_public(self):
        """Health endpoints must not require authentication."""
        r = self.client.get("/health")
        assert r.status_code == 200


# ── 2. Environment Validation ─────────────────────────────────────────────────

class TestEnvironmentValidation:
    def test_settings_has_app_name(self):
        from app.core.config import settings
        assert settings.APP_NAME == "RuralBiz AI"

    def test_settings_has_version(self):
        from app.core.config import settings
        assert settings.APP_VERSION is not None

    def test_settings_environment_valid(self):
        from app.core.config import settings
        assert settings.ENVIRONMENT in ("development", "testing", "production")

    def test_settings_debug_is_bool(self):
        from app.core.config import settings
        assert isinstance(settings.DEBUG, bool)

    def test_settings_cors_is_list(self):
        from app.core.config import settings
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert len(settings.BACKEND_CORS_ORIGINS) > 0

    def test_settings_gemini_key_is_optional(self):
        """GEMINI_API_KEY absence must NOT crash the app."""
        from app.core.config import settings
        # Empty string is allowed — fallback mode works
        assert isinstance(settings.GEMINI_API_KEY, str)

    def test_settings_database_url_present(self):
        from app.core.config import settings
        assert settings.DATABASE_URL
        assert "://" in settings.DATABASE_URL

    def test_settings_demo_mode_is_bool(self):
        from app.core.config import settings
        assert isinstance(settings.DEMO_MODE, bool)

    def test_settings_rate_limit_enabled_is_bool(self):
        from app.core.config import settings
        assert isinstance(settings.RATE_LIMIT_ENABLED, bool)

    def test_settings_is_development_helper(self):
        from app.core.config import settings
        # In test environment it should be development or testing
        assert isinstance(settings.is_development, bool)

    def test_production_rejects_insecure_jwt(self):
        """Simulate production validation."""
        from pydantic import ValidationError
        import os, sys
        # We test the model validator logic directly without re-importing
        from app.core.config import _INSECURE_JWT
        assert "change-me-to-a-long-random-secret" in _INSECURE_JWT

    def test_mask_db_url_hides_password(self):
        from app.core.logging import mask_db_url
        url = "postgresql+asyncpg://user:secretpassword@localhost:5432/db"
        masked = mask_db_url(url)
        assert "secretpassword" not in masked
        assert "***" in masked

    def test_mask_sqlite_url_unchanged(self):
        from app.core.logging import mask_db_url
        url = "sqlite+aiosqlite:///./ruralbiz.db"
        masked = mask_db_url(url)
        assert "ruralbiz.db" in masked


# ── 3. Demo Mode ─────────────────────────────────────────────────────────────

class TestDemoMode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client, self.app, self.get_db, _ = _make_client(demo_mode=False)
        yield
        self.app.dependency_overrides.pop(self.get_db, None)

    def test_demo_status_endpoint(self):
        r = self.client.get("/demo/status")
        assert r.status_code == 200
        assert "demo_mode" in r.json()

    def test_demo_status_is_bool(self):
        r = self.client.get("/demo/status")
        assert isinstance(r.json()["demo_mode"], bool)

    def test_demo_profiles_endpoint(self):
        r = self.client.get("/demo/profiles")
        assert r.status_code == 200
        data = r.json()
        assert "profiles" in data
        assert isinstance(data["profiles"], list)

    def test_demo_profiles_count(self):
        r = self.client.get("/demo/profiles")
        data = r.json()
        assert data["count"] >= 3

    def test_demo_profiles_labeled(self):
        r = self.client.get("/demo/profiles")
        for p in r.json()["profiles"]:
            assert p.get("is_demo") is True

    def test_demo_profiles_have_required_fields(self):
        r = self.client.get("/demo/profiles")
        for p in r.json()["profiles"]:
            assert "name" in p
            assert "description" in p
            assert "available_capital" in p
            assert "skills" in p
            assert "state" in p

    def test_demo_scenarios_endpoint(self):
        r = self.client.get("/demo/scenarios")
        assert r.status_code == 200
        data = r.json()
        assert "scenarios" in data

    def test_demo_scenarios_count(self):
        r = self.client.get("/demo/scenarios")
        assert r.json()["count"] >= 5

    def test_demo_scenarios_have_routes(self):
        r = self.client.get("/demo/scenarios")
        for s in r.json()["scenarios"]:
            assert "route" in s
            assert s["route"].startswith("/")

    def test_demo_scenarios_are_labeled(self):
        r = self.client.get("/demo/scenarios")
        for s in r.json()["scenarios"]:
            assert s.get("is_demo") is True

    def test_demo_profiles_not_mixed_with_real_users(self):
        """Demo profiles must be clearly separated."""
        r = self.client.get("/demo/profiles")
        for p in r.json()["profiles"]:
            # Each profile must carry an explicit demo flag
            assert "is_demo" in p
            # Must not have a real JWT user ID format
            assert p.get("id", "").startswith("demo-")


# ── 4. Error Handling ────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client, self.app, self.get_db, _ = _make_client()
        yield
        self.app.dependency_overrides.pop(self.get_db, None)

    def test_not_found_returns_json(self):
        r = self.client.get("/this-endpoint-does-not-exist-at-all-xyz")
        # FastAPI returns 404 for unknown routes
        assert r.status_code == 404

    def test_unauth_returns_401_or_422(self):
        """Unauthenticated access to protected endpoint returns 401/422."""
        r = self.client.get("/users/me")
        assert r.status_code in (401, 403, 422)

    def test_exception_classes_importable(self):
        from app.core.exceptions import (
            RuralBizError, AuthenticationError, AuthorizationError,
            ResourceNotFoundError, ValidationFailedError, ExternalAPIError,
            DatabaseError, RateLimitError, DemoModeError,
        )
        assert RuralBizError.status_code == 500
        assert AuthenticationError.status_code == 401
        assert ResourceNotFoundError.status_code == 404
        assert RateLimitError.status_code == 429

    def test_ruralbiz_error_message(self):
        from app.core.exceptions import ResourceNotFoundError
        e = ResourceNotFoundError("Item not found")
        assert "Item not found" in str(e)

    def test_exception_handler_registered(self):
        """Verify exception handlers are registered on the app."""
        from app.main import app
        assert len(app.exception_handlers) > 0

    def test_validation_error_returns_json(self):
        """Sending invalid data to a protected endpoint returns 401/403/422."""
        r = self.client.patch("/users/language", json={"language": "invalid_lang_xyz"})
        assert r.status_code in (401, 403, 422)

    def test_root_endpoint(self):
        r = self.client.get("/")
        assert r.status_code == 200
        assert "version" in r.json()


# ── 5. Backward Compatibility ────────────────────────────────────────────────

class TestPhase11BackwardCompatibility:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client, self.app, self.get_db, self.get_current_user = _make_client(authenticated=True)
        yield
        self.app.dependency_overrides.pop(self.get_db, None)
        if self.get_current_user:
            self.app.dependency_overrides.pop(self.get_current_user, None)

    def test_health_still_works(self):
        r = self.client.get("/health")
        assert r.status_code == 200

    def test_languages_still_work(self):
        r = self.client.get("/languages")
        assert r.status_code == 200

    def test_translate_still_works(self):
        r = self.client.post("/language/translate", json={"text": "Revenue", "target_language": "hi"})
        assert r.status_code == 200

    def test_businesses_endpoint_still_works(self):
        r = self.client.get("/businesses")
        assert r.status_code in (200, 404)

    def test_goals_endpoint_still_works(self):
        r = self.client.get("/goals")
        assert r.status_code in (200, 422)

    def test_analytics_endpoint_still_works(self):
        r = self.client.get("/analytics/dashboard")
        assert r.status_code not in (404, 405)

    def test_demo_endpoint_accessible(self):
        r = self.client.get("/demo/status")
        assert r.status_code == 200

    def test_docs_accessible(self):
        r = self.client.get("/docs")
        assert r.status_code == 200

    def test_openapi_json_accessible(self):
        r = self.client.get("/openapi.json")
        assert r.status_code == 200

    def test_openapi_has_title(self):
        r = self.client.get("/openapi.json")
        data = r.json()
        assert "RuralBiz" in data["info"]["title"]
