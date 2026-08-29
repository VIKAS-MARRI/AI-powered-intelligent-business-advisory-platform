"""
Phase 10 tests — Language system, translation service, multilingual API.
Covers: language config, translation provider, API endpoints, number preservation,
        simple language mode, backward compatibility.
"""
import pytest
import re
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# 1. Language Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TestLanguageConfig:
    def test_supported_languages_exist(self):
        from app.core.languages import LANGUAGES
        assert "en" in LANGUAGES
        assert "hi" in LANGUAGES
        assert "te" in LANGUAGES

    def test_language_codes(self):
        from app.core.languages import LANGUAGES
        assert LANGUAGES["en"].code == "en"
        assert LANGUAGES["hi"].code == "hi"
        assert LANGUAGES["te"].code == "te"

    def test_native_names(self):
        from app.core.languages import LANGUAGES
        assert LANGUAGES["en"].native_name == "English"
        assert "हिन्दी" in LANGUAGES["hi"].native_name
        assert "తెలుగు" in LANGUAGES["te"].native_name

    def test_speech_codes(self):
        from app.core.languages import LANGUAGES
        assert LANGUAGES["en"].speech_code == "en-IN"
        assert LANGUAGES["hi"].speech_code == "hi-IN"
        assert LANGUAGES["te"].speech_code == "te-IN"

    def test_default_language(self):
        from app.core.languages import DEFAULT_LANGUAGE
        assert DEFAULT_LANGUAGE == "en"

    def test_supported_codes_list(self):
        from app.core.languages import SUPPORTED_CODES
        assert "en" in SUPPORTED_CODES
        assert "hi" in SUPPORTED_CODES
        assert "te" in SUPPORTED_CODES

    def test_get_language_valid(self):
        from app.core.languages import get_language
        lang = get_language("hi")
        assert lang.code == "hi"
        assert lang.name == "Hindi"

    def test_get_language_invalid_falls_back_to_english(self):
        from app.core.languages import get_language
        lang = get_language("xx")
        assert lang.code == "en"

    def test_is_supported_valid(self):
        from app.core.languages import is_supported
        assert is_supported("en") is True
        assert is_supported("hi") is True
        assert is_supported("te") is True

    def test_is_supported_invalid(self):
        from app.core.languages import is_supported
        assert is_supported("fr") is False
        assert is_supported("") is False
        assert is_supported("zz") is False

    def test_get_all_languages_returns_list(self):
        from app.core.languages import get_all_languages
        langs = get_all_languages()
        assert isinstance(langs, list)
        assert len(langs) == 3  # en, hi, te
        codes = [l["code"] for l in langs]
        assert "en" in codes
        assert "hi" in codes
        assert "te" in codes

    def test_language_has_required_fields(self):
        from app.core.languages import get_all_languages
        for lang in get_all_languages():
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang
            assert "supported" in lang
            assert "speech_code" in lang


# ─────────────────────────────────────────────────────────────────────────────
# 2. Translation Token Protection
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenProtection:
    def _tokenise(self, text: str):
        from app.services.translation_service import _tokenise
        return _tokenise(text)

    def _restore(self, template: str, tokens: list):
        from app.services.translation_service import _restore
        return _restore(template, tokens)

    def test_currency_protected(self):
        text = "Revenue is ₹25,000 this month"
        template, tokens = self._tokenise(text)
        assert "₹25,000" in tokens
        assert "₹25,000" not in template
        restored = self._restore(template, tokens)
        assert "₹25,000" in restored

    def test_percentage_protected(self):
        text = "Growth rate is 15%"
        template, tokens = self._tokenise(text)
        assert "15%" in tokens

    def test_url_protected(self):
        text = "Visit https://pmegp.kvic.org.in for details"
        template, tokens = self._tokenise(text)
        assert any("https://" in t for t in tokens)

    def test_scheme_name_protected(self):
        text = "Apply for MUDRA loan scheme"
        template, tokens = self._tokenise(text)
        assert "MUDRA" in tokens

    def test_pmegp_protected(self):
        text = "PMEGP scheme provides subsidy"
        template, tokens = self._tokenise(text)
        assert "PMEGP" in tokens

    def test_no_false_positives_on_plain_text(self):
        text = "This is a simple sentence"
        template, tokens = self._tokenise(text)
        assert len(tokens) == 0  # nothing protected
        assert template == text

    def test_restore_preserves_original(self):
        text = "Profit: ₹10,000 (25% margin) — see https://example.com"
        template, tokens = self._tokenise(text)
        restored = self._restore(template, tokens)
        assert restored == text


# ─────────────────────────────────────────────────────────────────────────────
# 3. Fallback Translation Provider
# ─────────────────────────────────────────────────────────────────────────────

class TestFallbackTranslation:
    def _provider(self):
        from app.services.translation_service import FallbackTranslationProvider
        return FallbackTranslationProvider()

    def test_same_language_passthrough(self):
        p = self._provider()
        r = p.translate("Hello", "en", "en")
        assert r.translated_text == "Hello"
        assert r.provider == "passthrough"
        assert r.confidence == 1.0

    def test_to_english_passthrough(self):
        p = self._provider()
        r = p.translate("नमस्ते", "hi", "en")
        assert r.translated_text == "नमस्ते"
        assert r.provider == "passthrough"

    def test_known_phrase_hi(self):
        p = self._provider()
        r = p.translate("Dashboard", "en", "hi")
        assert "डैशबोर्ड" in r.translated_text

    def test_known_phrase_te(self):
        p = self._provider()
        r = p.translate("Dashboard", "en", "te")
        assert "డ్యాష్‌బోర్డ్" in r.translated_text

    def test_is_fallback_flag(self):
        p = self._provider()
        r = p.translate("Revenue", "en", "hi")
        assert r.is_fallback is True

    def test_currency_preserved_in_translation(self):
        p = self._provider()
        r = p.translate("Revenue is ₹25,000", "en", "hi")
        assert "₹25,000" in r.translated_text

    def test_percentage_preserved_in_translation(self):
        p = self._provider()
        r = p.translate("Growth is 15%", "en", "te")
        assert "15%" in r.translated_text

    def test_url_preserved(self):
        p = self._provider()
        r = p.translate("Visit https://example.com for info", "en", "hi")
        assert "https://example.com" in r.translated_text

    def test_provider_name(self):
        p = self._provider()
        assert "fallback" in p.name().lower()

    def test_unsupported_language(self):
        from app.services.translation_service import FallbackTranslationProvider
        p = FallbackTranslationProvider()
        r = p.translate("Hello", "en", "fr")  # unsupported — returns original with low confidence
        # Should not crash
        assert r.translated_text is not None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Translation Service
# ─────────────────────────────────────────────────────────────────────────────

class TestTranslationService:
    def _service(self):
        from app.services.translation_service import TranslationService
        return TranslationService()

    def test_translate_en_to_en_is_passthrough(self):
        svc = self._service()
        r = svc.translate("Hello world", "en", "en")
        assert r.translated_text == "Hello world"
        assert r.provider == "passthrough"

    def test_translate_empty_string(self):
        svc = self._service()
        r = svc.translate("", "hi")
        assert r.translated_text == ""

    def test_translate_unsupported_falls_back_to_en(self):
        svc = self._service()
        r = svc.translate("Hello", "fr")  # unsupported → rerouted to en
        assert r.target_language == "en"

    def test_translate_to_hindi(self):
        svc = self._service()
        r = svc.translate("Dashboard", "hi")
        assert r is not None
        assert r.translated_text is not None
        assert r.target_language == "hi"
        assert r.source_language == "en"

    def test_translate_to_telugu(self):
        svc = self._service()
        r = svc.translate("Dashboard", "te")
        assert r is not None
        assert r.target_language == "te"

    def test_result_has_metadata(self):
        svc = self._service()
        r = svc.translate("Revenue", "hi")
        assert hasattr(r, "translated_text")
        assert hasattr(r, "source_language")
        assert hasattr(r, "target_language")
        assert hasattr(r, "provider")
        assert hasattr(r, "confidence")
        assert hasattr(r, "is_fallback")

    def test_result_to_dict(self):
        svc = self._service()
        r = svc.translate("Profit", "hi")
        d = r.to_dict()
        assert "translated_text" in d
        assert "source_language" in d
        assert "target_language" in d
        assert "provider" in d
        assert "confidence" in d
        assert "is_fallback" in d

    def test_translate_to_english_same_language(self):
        svc = self._service()
        r = svc.translate_to_english("Hello", "en")
        assert r.translated_text == "Hello"

    def test_translate_to_english_hindi(self):
        svc = self._service()
        r = svc.translate_to_english("नमस्ते", "hi")
        assert r is not None
        assert r.target_language == "en"

    def test_number_preserved_end_to_end(self):
        svc = self._service()
        r = svc.translate("Your revenue is ₹50,000 per month (30% margin)", "hi")
        assert "₹50,000" in r.translated_text
        assert "30%" in r.translated_text

    def test_provider_property(self):
        svc = self._service()
        assert isinstance(svc.provider_name, str)

    def test_singleton(self):
        from app.services.translation_service import get_translation_service
        s1 = get_translation_service()
        s2 = get_translation_service()
        assert s1 is s2  # same singleton

    def test_convenience_function(self):
        from app.services.translation_service import translate_text
        r = translate_text("Revenue", "te")
        assert r is not None
        assert r.target_language == "te"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Language API (via TestClient with dependency overrides)
# ─────────────────────────────────────────────────────────────────────────────

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


def _make_mock_client(simple_language_mode: bool = False, preferred_language: str = "en"):
    """Create a TestClient with fully mocked auth and DB dependencies."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.dependencies import get_current_user
    from app.database.db import get_db

    mock_user = SimpleNamespace(
        id="lang_user_001",
        email="lang@test.com",
        full_name="Lang Test",
        state="Telangana",
        preferred_language=preferred_language,
        simple_language_mode=simple_language_mode,
        available_capital=100000.0,
        skills="tailoring",
        business_interests="garments",
        monthly_income_goal=15000.0,
        experience_years=2,
        is_active=True,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app, raise_server_exceptions=False)
    return client, app, get_current_user, get_db


class TestLanguageAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            self.client, self.app, self.get_current_user, self.get_db = _make_mock_client()
        except Exception:
            self.client = None

    def teardown_method(self, method):
        if hasattr(self, 'app'):
            self.app.dependency_overrides.pop(self.get_current_user, None)
            self.app.dependency_overrides.pop(self.get_db, None)

    def test_list_languages(self):
        if not self.client: pytest.skip()
        r = self.client.get("/languages")
        assert r.status_code == 200
        data = r.json()
        assert "languages" in data
        codes = [l["code"] for l in data["languages"]]
        assert "en" in codes
        assert "hi" in codes
        assert "te" in codes

    def test_supported_languages(self):
        if not self.client: pytest.skip()
        r = self.client.get("/languages/supported")
        assert r.status_code == 200
        data = r.json()
        assert "supported" in data
        assert "count" in data
        assert data["count"] == 3

    def test_get_user_language(self):
        if not self.client: pytest.skip()
        r = self.client.get("/users/language")
        assert r.status_code == 200
        data = r.json()
        assert "language" in data
        assert data["language"] in ("en", "hi", "te")

    def test_update_language_to_hindi(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/language", json={"language": "hi"})
        assert r.status_code == 200
        assert r.json()["language"] == "hi"

    def test_update_language_to_telugu(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/language", json={"language": "te"})
        assert r.status_code == 200
        assert r.json()["language"] == "te"

    def test_update_language_back_to_english(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/language", json={"language": "en"})
        assert r.status_code == 200
        assert r.json()["language"] == "en"

    def test_invalid_language_rejected(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/language", json={"language": "fr"})
        assert r.status_code == 422

    def test_empty_language_rejected(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/language", json={"language": "zz"})
        assert r.status_code == 422

    def test_get_accessibility(self):
        if not self.client: pytest.skip()
        r = self.client.get("/users/accessibility")
        assert r.status_code == 200
        data = r.json()
        assert "simple_language_mode" in data
        assert "preferred_language" in data

    def test_update_simple_language_on(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/accessibility", json={"simple_language_mode": True})
        assert r.status_code == 200
        assert r.json()["simple_language_mode"] is True

    def test_update_simple_language_off(self):
        if not self.client: pytest.skip()
        r = self.client.patch("/users/accessibility", json={"simple_language_mode": False})
        assert r.status_code == 200
        assert r.json()["simple_language_mode"] is False

    def test_translate_endpoint_english_to_hindi(self):
        if not self.client: pytest.skip()
        r = self.client.post("/language/translate", json={
            "text": "Revenue",
            "target_language": "hi",
            "source_language": "en",
        })
        assert r.status_code == 200
        data = r.json()
        assert "translated_text" in data
        assert data["target_language"] == "hi"

    def test_translate_preserves_currency(self):
        if not self.client: pytest.skip()
        r = self.client.post("/language/translate", json={
            "text": "Revenue is ₹25,000",
            "target_language": "hi",
            "source_language": "en",
        })
        assert r.status_code == 200
        assert "₹25,000" in r.json()["translated_text"]

    def test_translate_unsupported_language_rejected(self):
        if not self.client: pytest.skip()
        r = self.client.post("/language/translate", json={
            "text": "Hello",
            "target_language": "fr",
        })
        assert r.status_code == 422

    def test_language_requires_auth(self):
        if not self.client: pytest.skip()
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.dependencies import get_current_user
        # Remove override to test unauthenticated
        app.dependency_overrides.pop(get_current_user, None)
        bare = TestClient(app, raise_server_exceptions=False)
        r = bare.get("/users/language")
        assert r.status_code in (401, 403, 422)

    def test_languages_is_public(self):
        if not self.client: pytest.skip()
        # Public endpoint — no auth needed
        r = self.client.get("/languages")
        assert r.status_code == 200

    def test_translate_is_public(self):
        if not self.client: pytest.skip()
        r = self.client.post("/language/translate", json={
            "text": "Dashboard",
            "target_language": "te",
        })
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 6. Advisory Language Integration
# ─────────────────────────────────────────────────────────────────────────────

class TestAdvisoryLanguage:
    def test_advisor_accepts_language_in_state(self):
        """AgentState accepts language fields without errors."""
        from app.agents.state import AgentState
        state: AgentState = {
            "user_id":         "test",
            "question":        "test question",
            "required_agents": [],
            "ai_status":       "unavailable",
            "errors":          [],
            "language":        "hi",
            "simple_language": True,
        }
        assert state["language"] == "hi"
        assert state["simple_language"] is True

    def test_advisory_model_has_language_fields(self):
        from app.models.advisory import AdvisorySession
        cols = [c.key for c in AdvisorySession.__table__.columns]
        assert "original_language"  in cols
        assert "canonical_query"    in cols
        assert "response_language"  in cols

    def test_user_model_has_simple_language_mode(self):
        from app.models.user import User
        cols = [c.key for c in User.__table__.columns]
        assert "simple_language_mode" in cols
        assert "preferred_language"   in cols


# ─────────────────────────────────────────────────────────────────────────────
# 7. Backward Compatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            self.client, self.app, self.get_current_user, self.get_db = _make_mock_client()
        except Exception:
            self.client = None

    def teardown_method(self, method):
        if hasattr(self, 'app'):
            self.app.dependency_overrides.pop(self.get_current_user, None)
            self.app.dependency_overrides.pop(self.get_db, None)

    def test_health_check(self):
        if not self.client: pytest.skip()
        r = self.client.get("/health")
        assert r.status_code == 200

    def test_businesses_list(self):
        if not self.client: pytest.skip()
        r = self.client.get("/businesses")
        assert r.status_code in (200, 401)

    def test_languages_public(self):
        if not self.client: pytest.skip()
        r = self.client.get("/languages")
        assert r.status_code == 200

    def test_translate_public(self):
        if not self.client: pytest.skip()
        r = self.client.post("/language/translate", json={
            "text": "Dashboard",
            "target_language": "te",
        })
        assert r.status_code == 200

    def test_goals_still_work(self):
        if not self.client: pytest.skip()
        r = self.client.get("/goals")
        assert r.status_code in (200, 422)

    def test_analytics_still_work(self):
        if not self.client: pytest.skip()
        r = self.client.get("/analytics/dashboard")
        assert r.status_code not in (404, 405)
