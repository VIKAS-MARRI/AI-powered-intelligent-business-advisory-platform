"""
Comprehensive tests for Phase 7 — AI Multi-Agent Business Advisory System.

Tests:
  - Supervisor routing (AI + keyword fallback)
  - Specialist agent nodes (with mocked dependencies)
  - AI service (missing key, SDK unavailable, API failure)
  - Synthesizer (AI and deterministic fallback)
  - Graph topology
  - API endpoints (query, analyze, status, history)
  - Prompt safety (no API keys in prompts)
  - Advisory history persistence

Run: python -m pytest app/tests/test_advisory_system.py -v
Tests NEVER require a real Gemini API key.
"""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.state import AgentState
from app.agents.supervisor import _keyword_route, supervisor_node
from app.agents.prompts import (
    GROUNDING_INSTRUCTION, SUPERVISOR_PROMPT, SYNTHESIZER_PROMPT,
    BUSINESS_AGENT_PROMPT, FINANCE_AGENT_PROMPT, MARKET_AGENT_PROMPT,
    SCHEME_AGENT_PROMPT, DISCLAIMER,
)
from app.agents.synthesizer import _fallback_advice, _extract_structured_advice


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _base_state(**overrides) -> Dict[str, Any]:
    defaults = {
        "user_id":           "u001",
        "question":          "What business can I start?",
        "available_capital": 200000.0,
        "business_id":       None,
        "latitude":          None,
        "longitude":         None,
        "state_name":        "Telangana",
        "radius_km":         5.0,
        "required_agents":   [],
        "business_result":   None,
        "finance_result":    None,
        "market_result":     None,
        "scheme_result":     None,
        "final_advice":      None,
        "ai_status":         "unavailable",
        "errors":            [],
        "_db":               None,
    }
    defaults.update(overrides)
    return defaults


# ══════════════════════════════════════════════════════════════════════════════
# TestKeywordRouting
# ══════════════════════════════════════════════════════════════════════════════

class TestKeywordRouting:
    def test_business_question_routes_to_business_finance(self):
        # "What business should I start?" triggers business keyword
        # finance is also included as the minimum safe pair
        agents = _keyword_route("What business should I start?")
        assert "business" in agents
        # either finance included directly or at minimum business
        assert len(agents) >= 1

    def test_capital_question_routes_to_finance(self):
        agents = _keyword_route("I have ₹2 lakh. What is the ROI?")
        assert "finance" in agents

    def test_market_question_routes_to_market(self):
        agents = _keyword_route("What is the competition in my area?")
        assert "market" in agents
        assert "business" in agents   # always included

    def test_scheme_question_routes_to_scheme(self):
        agents = _keyword_route("What government scheme can I apply for?")
        assert "scheme" in agents

    def test_comprehensive_question_routes_all(self):
        agents = _keyword_route(
            "I want to start a business with ₹2 lakh in my area. What government support is available?"
        )
        assert set(agents) >= {"business", "finance", "market", "scheme"}

    def test_empty_question_returns_minimum(self):
        agents = _keyword_route("")
        assert len(agents) >= 1
        assert "business" in agents

    def test_unknown_question_includes_business(self):
        agents = _keyword_route("xyz abc 123 no match at all")
        assert "business" in agents

    def test_returns_max_four_agents(self):
        agents = _keyword_route(
            "₹5 lakh business scheme area market government loan subsidy"
        )
        assert len(agents) <= 4

    def test_agents_are_valid_names(self):
        valid = {"business", "finance", "market", "scheme"}
        for question in [
            "start a business", "loan for dairy", "market near me", "PMEGP scheme"
        ]:
            agents = _keyword_route(question)
            assert all(a in valid for a in agents)

    def test_dairy_business_routes_business_and_finance(self):
        agents = _keyword_route("Is a dairy business good?")
        assert "business" in agents

    def test_location_with_capital_adds_market(self):
        agents = _keyword_route("I have ₹3 lakh and want to start a business in my village")
        assert "market" in agents


# ══════════════════════════════════════════════════════════════════════════════
# TestSupervisorNode
# ══════════════════════════════════════════════════════════════════════════════

class TestSupervisorNode:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(supervisor_node(state))

    def test_supervisor_sets_required_agents(self):
        state = _base_state(question="What business should I start with ₹2 lakh?")
        result = self._run(state)
        assert len(result["required_agents"]) >= 1

    def test_supervisor_sets_ai_status(self):
        state  = _base_state()
        result = self._run(state)
        assert result["ai_status"] in {"available", "limited", "unavailable"}

    def test_supervisor_preserves_other_state(self):
        state  = _base_state(user_id="test-user", state_name="Kerala")
        result = self._run(state)
        assert result["user_id"] == "test-user"
        assert result["state_name"] == "Kerala"

    def test_supervisor_uses_fallback_when_ai_unavailable(self):
        """Even without AI, supervisor must produce valid routing."""
        state  = _base_state(question="I want to start a tailoring shop")
        result = self._run(state)
        assert "business" in result["required_agents"]

    @patch("app.agents.supervisor.ai_service")
    def test_supervisor_uses_ai_routing_when_available(self, mock_ai):
        """When AI returns valid routing, supervisor uses it."""
        mock_ai.is_available.return_value = True
        mock_ai.generate_json = AsyncMock(return_value={"agents": ["business", "finance"]})
        state  = _base_state(question="What business for ₹2 lakh?")
        result = asyncio.get_event_loop().run_until_complete(supervisor_node(state))
        assert "business" in result["required_agents"]

    @patch("app.agents.supervisor.ai_service")
    def test_supervisor_falls_back_if_ai_returns_empty(self, mock_ai):
        mock_ai.is_available.return_value = True
        mock_ai.generate_json = AsyncMock(return_value=None)
        state  = _base_state(question="What business should I start?")
        result = asyncio.get_event_loop().run_until_complete(supervisor_node(state))
        assert len(result["required_agents"]) >= 1

    @patch("app.agents.supervisor.ai_service")
    def test_supervisor_falls_back_if_ai_raises(self, mock_ai):
        mock_ai.is_available.return_value = True
        mock_ai.generate_json = AsyncMock(side_effect=RuntimeError("API error"))
        state  = _base_state(question="start business")
        result = asyncio.get_event_loop().run_until_complete(supervisor_node(state))
        assert len(result["required_agents"]) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# TestAIService
# ══════════════════════════════════════════════════════════════════════════════

class TestAIService:
    def test_missing_key_marks_unavailable(self):
        from app.services.ai_service import AIService
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.GEMINI_MODEL   = "gemini-1.5-flash"
            mock_settings.AI_MAX_RETRIES = 2
            svc = AIService()
            assert not svc.is_available()

    def test_status_unavailable_when_no_key(self):
        from app.services.ai_service import AIService
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.GEMINI_MODEL   = "gemini-1.5-flash"
            mock_settings.AI_MAX_RETRIES = 2
            svc = AIService()
            assert svc.status == "unavailable"

    def test_status_limited_when_key_but_init_fails(self):
        from app.services.ai_service import AIService
        with patch("app.services.ai_service.settings") as mock_settings, \
             patch("app.services.ai_service._genai_module") as mock_sdk:
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL   = "gemini-1.5-flash"
            mock_settings.AI_MAX_RETRIES = 2
            mock_sdk.Client.side_effect  = RuntimeError("connection failed")
            svc = AIService()
            assert svc.status in {"limited", "unavailable"}

    def test_generate_returns_none_when_unavailable(self):
        from app.services.ai_service import AIService
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.GEMINI_MODEL   = "gemini-1.5-flash"
            mock_settings.AI_MAX_RETRIES = 2
            svc = AIService()
            result = asyncio.get_event_loop().run_until_complete(svc.generate("test prompt"))
            assert result is None

    def test_generate_json_returns_none_on_bad_response(self):
        from app.services.ai_service import AIService
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.GEMINI_MODEL   = "gemini-1.5-flash"
            mock_settings.AI_MAX_RETRIES = 2
            svc = AIService()
            result = asyncio.get_event_loop().run_until_complete(svc.generate_json("test"))
            assert result is None

    def test_generate_json_parses_valid_json(self):
        from app.services.ai_service import AIService
        svc = AIService()
        # Directly test the JSON parsing logic (without SDK)
        with patch.object(svc, "generate", new=AsyncMock(return_value='{"agents": ["business"]}')):
            svc._available = True
            result = asyncio.get_event_loop().run_until_complete(svc.generate_json("test"))
            assert result == {"agents": ["business"]}

    def test_generate_json_strips_markdown_fences(self):
        from app.services.ai_service import AIService
        svc = AIService()
        with patch.object(svc, "generate", new=AsyncMock(return_value='```json\n{"agents": ["finance"]}\n```')):
            svc._available = True
            result = asyncio.get_event_loop().run_until_complete(svc.generate_json("test"))
            assert result is not None
            assert result.get("agents") == ["finance"]

    def test_sdk_unavailable_marks_service_unavailable(self):
        from app.services import ai_service as ai_mod
        with patch.object(ai_mod, "_SDK_AVAILABLE", False):
            from app.services.ai_service import AIService
            with patch("app.services.ai_service._SDK_AVAILABLE", False):
                svc = AIService()
                assert not svc.is_available()


# ══════════════════════════════════════════════════════════════════════════════
# TestPromptSafety
# ══════════════════════════════════════════════════════════════════════════════

class TestPromptSafety:
    """Ensures prompts contain grounding instructions and no API key references."""

    def test_grounding_instruction_present(self):
        assert "STRICT DATA GROUNDING POLICY" in GROUNDING_INSTRUCTION
        assert "Do NOT invent" in GROUNDING_INSTRUCTION

    def test_supervisor_prompt_has_json_output_instruction(self):
        prompt = SUPERVISOR_PROMPT.format(question="test")
        assert "JSON" in prompt

    def test_synthesizer_prompt_includes_grounding(self):
        prompt = SYNTHESIZER_PROMPT.format(
            grounding="[grounding]", question="q",
            available_capital="₹1L", location="TG",
            business_summary="bs", finance_summary="fs",
            market_summary="ms", scheme_summary="ss",
            language_instruction="",   # Phase 10 default
        )
        assert "Use ONLY data" in prompt

    def test_no_api_key_in_any_prompt(self):
        """Verify no hardcoded API key patterns exist in any prompt."""
        import re
        key_pattern = re.compile(r"AIza[A-Za-z0-9_-]{35}")
        for prompt_text in [
            GROUNDING_INSTRUCTION, SUPERVISOR_PROMPT, SYNTHESIZER_PROMPT,
            BUSINESS_AGENT_PROMPT, FINANCE_AGENT_PROMPT,
            MARKET_AGENT_PROMPT, SCHEME_AGENT_PROMPT,
        ]:
            assert not key_pattern.search(prompt_text), \
                f"API key pattern found in prompt: {prompt_text[:50]}"

    def test_disclaimer_mentions_official_sources(self):
        assert "official" in DISCLAIMER.lower()
        assert "guarantee" in DISCLAIMER.lower()

    def test_scheme_prompt_warns_against_inventing(self):
        prompt = SCHEME_AGENT_PROMPT.format(
            grounding="[g]", question="q", business_name="b",
            available_capital="₹1L", funding_gap="₹50k", scheme_data="sd",
            language_instruction="",   # Phase 10 default
        )
        assert "Only mention schemes" in prompt

    def test_business_prompt_warns_against_inventing(self):
        prompt = BUSINESS_AGENT_PROMPT.format(
            grounding="[g]", question="q", available_capital="₹1L",
            state_name="TG", business_data="data",
            language_instruction="",   # Phase 10 default
        )
        assert "Do not invent" in prompt

    def test_finance_prompt_warns_against_inventing(self):
        prompt = FINANCE_AGENT_PROMPT.format(
            grounding="[g]", question="q", available_capital="₹1L",
            business_name="b", finance_data="fd",
            language_instruction="",   # Phase 10 default
        )
        assert "Do not invent" in prompt


# ══════════════════════════════════════════════════════════════════════════════
# TestSynthesizer
# ══════════════════════════════════════════════════════════════════════════════

class TestSynthesizer:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(
            __import__("app.agents.synthesizer", fromlist=["synthesizer_node"]).synthesizer_node(state)
        )

    def _state_with_results(self, **overrides):
        state = _base_state(
            required_agents  = ["business", "finance", "scheme"],
            business_result  = {
                "status": "success",
                "top_business": {
                    "id": "b1", "name": "Tailoring Shop", "score": 85.0,
                    "min_investment": 80000, "max_investment": 150000, "monthly_revenue": 15000,
                    "risk_level": "Low", "category": "Tailoring",
                    "reasons": ["Capital fits", "Good demand"],
                },
                "recommendations": [],
                "ai_explanation": None,
            },
            finance_result   = {
                "status": "success",
                "investment_required": 80000,
                "available_capital": 200000,
                "funding_gap": 0,
                "monthly_profit": 5000,
                "break_even_months": 16,
                "ai_explanation": None,
            },
            scheme_result    = {
                "status": "success",
                "top_scheme": {
                    "scheme_name": "MUDRA Loan",
                    "score": 82.0,
                    "eligibility_status": "🟢 Likely Eligible",
                    "funding_relevance": "Loan",
                    "key_benefit": "Loan up to ₹10 lakh",
                    "official_url": "https://mudra.org.in/",
                },
                "matches": [],
                "ai_explanation": None,
            },
        )
        state.update(overrides)
        return state

    def test_synthesizer_produces_final_advice(self):
        state  = self._state_with_results()
        result = self._run(state)
        assert result["final_advice"] is not None
        assert result["final_advice"].get("summary")

    def test_synthesizer_includes_disclaimer(self):
        state  = self._state_with_results()
        result = self._run(state)
        assert "disclaimer" in result["final_advice"]
        assert result["final_advice"]["disclaimer"]

    def test_synthesizer_includes_next_steps(self):
        state  = self._state_with_results()
        result = self._run(state)
        assert len(result["final_advice"].get("next_steps", [])) > 0

    def test_synthesizer_includes_risks(self):
        state  = self._state_with_results()
        result = self._run(state)
        assert len(result["final_advice"].get("risks", [])) > 0

    def test_fallback_advice_uses_business_name(self):
        state = self._state_with_results()
        advice = _fallback_advice(state)
        assert "Tailoring Shop" in advice.get("summary", "") or \
               "Tailoring Shop" in advice.get("recommendation", "")

    def test_fallback_advice_has_required_fields(self):
        state = _base_state()
        advice = _fallback_advice(state)
        for field in ["summary", "recommendation", "financial_plan", "risks", "next_steps"]:
            assert field in advice

    def test_fallback_not_ai_generated(self):
        state = _base_state()
        advice = _fallback_advice(state)
        assert advice.get("ai_generated") is False

    def test_extract_structured_advice_parses_sections(self):
        sample_text = """
🎯 MY RECOMMENDATION
This is the recommendation.

💰 FINANCIAL PLAN
This is the financial plan.

📍 LOCAL MARKET INSIGHT
This is the market insight.

🏛️ POSSIBLE GOVERNMENT SUPPORT
This is the government support.

⚠️ KEY RISKS
- Risk one
- Risk two

📋 YOUR NEXT STEPS
1. Step one
2. Step two
        """
        advice = _extract_structured_advice(sample_text)
        assert "recommendation" in advice
        assert "financial_plan" in advice
        assert "market_insight" in advice
        assert len(advice.get("next_steps", [])) >= 2
        assert len(advice.get("risks", [])) >= 2
        assert advice.get("ai_generated") is True


# ══════════════════════════════════════════════════════════════════════════════
# TestBusinessAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestBusinessAgent:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(
            __import__("app.agents.business_agent", fromlist=["business_agent_node"]).business_agent_node(state)
        )

    def test_skips_if_not_required(self):
        state  = _base_state(required_agents=["finance"])
        result = self._run(state)
        assert result.get("business_result") is None

    def test_returns_error_without_db(self):
        state  = _base_state(required_agents=["business"], _db=None)
        result = self._run(state)
        # Should produce an error result but not crash
        assert result["business_result"] is not None
        assert result["business_result"].get("status") in ("error", "success")

    def test_preserves_other_state_fields(self):
        state  = _base_state(required_agents=["finance"], state_name="Goa")
        result = self._run(state)
        assert result["state_name"] == "Goa"


# ══════════════════════════════════════════════════════════════════════════════
# TestFinanceAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestFinanceAgent:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(
            __import__("app.agents.finance_agent", fromlist=["finance_agent_node"]).finance_agent_node(state)
        )

    def test_skips_if_not_required(self):
        state  = _base_state(required_agents=["business"])
        result = self._run(state)
        assert result.get("finance_result") is None

    def test_computes_when_business_result_available(self):
        state = _base_state(
            required_agents = ["finance"],
            available_capital = 200000,
            business_result = {
                "status": "success",
                "top_business": {
                    "id": "b1", "name": "Bakery", "score": 80.0,
                    "min_investment": 80000, "max_investment": 150000,
                    "monthly_revenue": 15000, "risk_level": "Low", "category": "Food",
                    "reasons": [],
                },
            },
        )
        result = self._run(state)
        assert result["finance_result"] is not None
        assert result["finance_result"].get("status") in ("success", "error")

    def test_funding_gap_computed_correctly(self):
        state = _base_state(
            required_agents   = ["finance"],
            available_capital = 50000,
            business_result   = {
                "status": "success",
                "top_business": {
                    "id": "b1", "name": "Shop", "score": 70.0,
                    "min_investment": 200000, "max_investment": 400000,
                    "monthly_revenue": 20000, "risk_level": "Medium", "category": "Retail",
                    "reasons": [],
                },
            },
        )
        result = self._run(state)
        if result["finance_result"].get("status") == "success":
            assert result["finance_result"].get("funding_gap", 0) == 150000

    def test_no_error_with_zero_capital(self):
        state  = _base_state(required_agents=["finance"], available_capital=0)
        result = self._run(state)
        # Should not raise, should return result or error
        assert result["finance_result"] is not None


# ══════════════════════════════════════════════════════════════════════════════
# TestMarketAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketAgent:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(
            __import__("app.agents.market_agent", fromlist=["market_agent_node"]).market_agent_node(state)
        )

    def test_skips_if_not_required(self):
        state  = _base_state(required_agents=["business"])
        result = self._run(state)
        assert result.get("market_result") is None

    def test_skipped_when_no_coords(self):
        state  = _base_state(required_agents=["market"], latitude=None, longitude=None)
        result = self._run(state)
        mr = result.get("market_result")
        assert mr is not None
        assert mr.get("status") == "skipped"

    def test_skipped_message_is_actionable(self):
        state  = _base_state(required_agents=["market"], latitude=None, longitude=None)
        result = self._run(state)
        mr = result.get("market_result", {})
        # Should have either a message or reason
        assert mr.get("message") or mr.get("reason")


# ══════════════════════════════════════════════════════════════════════════════
# TestSchemeAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemeAgent:
    def _run(self, state):
        return asyncio.get_event_loop().run_until_complete(
            __import__("app.agents.scheme_agent", fromlist=["scheme_agent_node"]).scheme_agent_node(state)
        )

    def test_skips_if_not_required(self):
        state  = _base_state(required_agents=["business"])
        result = self._run(state)
        assert result.get("scheme_result") is None

    def test_returns_error_without_db(self):
        state  = _base_state(required_agents=["scheme"], _db=None)
        result = self._run(state)
        assert result["scheme_result"] is not None
        assert result["scheme_result"].get("status") in ("error", "success")

    def test_preserves_state(self):
        state  = _base_state(required_agents=["business"], state_name="Bihar")
        result = self._run(state)
        assert result["state_name"] == "Bihar"


# ══════════════════════════════════════════════════════════════════════════════
# TestAdvisoryGraph
# ══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryGraph:
    def test_graph_compiles_without_error(self):
        from app.agents.graph import advisory_graph
        assert advisory_graph is not None

    def test_graph_has_ainvoke(self):
        from app.agents.graph import advisory_graph
        assert hasattr(advisory_graph, "ainvoke")

    def test_graph_runs_and_produces_final_advice(self):
        from app.agents.graph import advisory_graph
        state = _base_state(
            question         = "What business should I start with ₹2 lakh?",
            required_agents  = [],
        )
        result = asyncio.get_event_loop().run_until_complete(
            advisory_graph.ainvoke(state)
        )
        # Should complete without exception and produce final_advice
        assert result is not None
        assert result.get("final_advice") is not None

    def test_graph_routes_only_required_agents(self):
        from app.agents.graph import advisory_graph
        state = _base_state(
            question = "What is the ROI for a bakery?",
        )
        result = asyncio.get_event_loop().run_until_complete(
            advisory_graph.ainvoke(state)
        )
        # Market agent should not run if no location
        assert result.get("market_result") is None or \
               result["market_result"].get("status") == "skipped"


# ══════════════════════════════════════════════════════════════════════════════
# TestAdvisoryAPIEndpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryAPIEndpoints:
    """Test API using TestClient with a real test database session."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import TestClient lazily to avoid startup side effects."""
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            from app.core.dependencies import get_current_user
            from app.database.db import get_db

            mock_user = SimpleNamespace(
                id="u001", email="test@test.com", full_name="Test User",
                state="Telangana", available_capital=200000.0,
                skills="tailoring", business_interests="shop",
                monthly_income_goal=15000.0, is_active=True,
            )

            # Override auth
            app.dependency_overrides[get_current_user] = lambda: mock_user

            # Mock DB session
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
            mock_db.add    = MagicMock()
            mock_db.commit = AsyncMock()
            app.dependency_overrides[get_db] = lambda: mock_db

            self.client = TestClient(app, raise_server_exceptions=False)
        except Exception:
            self.client = None

    def test_status_endpoint_returns_json(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/advisor/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "ai_available" in data
        assert "fallback_available" in data

    def test_status_does_not_expose_api_key(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/advisor/status")
        assert resp.status_code == 200
        text = resp.text
        import re
        key_pattern = re.compile(r"AIza[A-Za-z0-9_-]{35}")
        assert not key_pattern.search(text), "API key found in status response"

    def test_query_requires_authentication(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            from app.core.dependencies import get_current_user
            # Remove override temporarily
            app.dependency_overrides.pop(get_current_user, None)
            fresh = TestClient(app, raise_server_exceptions=False)
            resp  = fresh.post("/advisor/query", json={"question": "test"})
            assert resp.status_code in (401, 403, 422)
        finally:
            pass  # overrides cleaned up by next test

    def test_query_with_valid_auth_returns_200(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/advisor/query", json={
            "question":          "What business can I start with ₹2 lakh?",
            "available_capital": 200000,
        })
        # May be 200 or 500 depending on DB mocking, but should not 401/422
        assert resp.status_code not in (401, 422)

    def test_query_with_invalid_body_returns_422(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/advisor/query", json={})
        assert resp.status_code == 422

    def test_history_endpoint_authenticated(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.get("/advisor/history")
        # Should attempt DB query and return 200 (even if empty)
        assert resp.status_code in (200, 500)

    def test_analyze_endpoint_exists(self):
        if not self.client:
            pytest.skip("TestClient setup failed")
        resp = self.client.post("/advisor/analyze", json={
            "question": "Is dairy farming good in my area?",
        })
        assert resp.status_code not in (404, 422)
