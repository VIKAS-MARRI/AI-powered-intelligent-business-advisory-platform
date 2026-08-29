"""
Gemini AI service layer for Phase 7 — uses google-genai SDK.

Reads API key from GEMINI_API_KEY env variable.
Never hardcodes secrets. Degrades gracefully when key is missing.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── SDK availability guard ────────────────────────────────────────────────────
try:
    from google import genai as _genai_module          # type: ignore
    from google.genai import types as _genai_types      # type: ignore
    _SDK_AVAILABLE = True
except ImportError:
    _genai_module = None        # type: ignore
    _genai_types  = None        # type: ignore
    _SDK_AVAILABLE = False
    logger.warning("google-genai SDK not available — AI features in fallback mode")


class AIService:
    """
    Gemini AI service with automatic graceful fallback.

    - Returns None on any failure; callers must handle.
    - Never raises to callers.
    - Never logs or exposes the API key.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None
        self._available = False
        self._reason = "Not initialized"
        self._init()

    def _init(self) -> None:
        if not _SDK_AVAILABLE:
            self._reason = "google-genai SDK not installed"
            return
        api_key = (settings.GEMINI_API_KEY or "").strip()
        if not api_key:
            self._reason = "GEMINI_API_KEY not configured"
            logger.info("AI service fallback mode: %s", self._reason)
            return
        try:
            self._client = _genai_module.Client(api_key=api_key)
            self._available = True
            self._reason = "available"
            logger.info("google-genai client initialized (model=%s)", settings.GEMINI_MODEL)
        except Exception as exc:
            self._reason = f"Init error: {exc}"
            logger.warning("google-genai init failed: %s", exc)

    def is_available(self) -> bool:
        return self._available

    @property
    def status(self) -> str:
        if self._available:
            return "available"
        return "limited" if (settings.GEMINI_API_KEY or "").strip() else "unavailable"

    @property
    def reason(self) -> str:
        return self._reason

    async def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Generate text. Returns None on any error."""
        if not self._available or self._client is None:
            return None
        for attempt in range(settings.AI_MAX_RETRIES + 1):
            try:
                config = _genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=1024,
                )
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=config,
                )
                text = response.text
                return text.strip() if text else None
            except Exception as exc:
                logger.warning("Gemini attempt %d/%d failed: %s", attempt + 1, settings.AI_MAX_RETRIES + 1, exc)
                if attempt == settings.AI_MAX_RETRIES:
                    return None
        return None

    async def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate and parse JSON. Returns None on any error."""
        text = await self.generate(prompt, temperature=0.1)
        if not text:
            return None
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Could not parse JSON from AI response: %.200s", text)
            return None


# Module-level singleton
ai_service = AIService()
