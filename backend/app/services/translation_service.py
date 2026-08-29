"""
Phase 10 — Translation Service.
Provider-abstracted translation with Gemini (when available) and safe fallback.

Architecture:
  TranslationProvider (abstract)
    ├── GeminiTranslationProvider  — used when GEMINI_API_KEY is present
    └── FallbackTranslationProvider — deterministic, no API required

IMPORTANT rules:
  1. English is the canonical internal language.
  2. Numbers, ₹ values, URLs, scheme names are NEVER altered.
  3. Translation metadata is always returned.
  4. The system works 100% without any API key.
  5. Fallback translation is honest about its limitations.
"""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.languages import DEFAULT_LANGUAGE, LANGUAGES, is_supported

logger = logging.getLogger(__name__)

# ── Protected token patterns ──────────────────────────────────────────────────
# These patterns are preserved as-is across all translations.
_PROTECTED_RE = re.compile(
    r"("
    r"₹[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore|lakhs|crores|L|Cr|k|K))?"  # ₹ amounts
    r"|\d+(?:,\d+)*(?:\.\d+)?(?:\s*%)"                                   # percentages
    r"|https?://\S+"                                                       # URLs
    r"|www\.\S+"                                                           # www links
    r"|\b\d{4}-\d{2}-\d{2}\b"                                            # ISO dates
    r"|\bPMEGP\b|\bMUDRA\b|\bPMFME\b|\bPMKVY\b|\bDIC\b|\bNSIC\b"      # scheme names
    r"|\bStand-Up India\b|\bStart-Up India\b"
    r")",
    re.IGNORECASE,
)


def _tokenise(text: str) -> tuple[str, list[str]]:
    """Replace protected tokens with placeholders. Returns (template, tokens)."""
    tokens: list[str] = []

    def _replace(m: re.Match) -> str:
        tokens.append(m.group(0))
        return f"__TOK{len(tokens)-1}__"

    template = _PROTECTED_RE.sub(_replace, text)
    return template, tokens


def _restore(template: str, tokens: list[str]) -> str:
    """Restore protected tokens from placeholders."""
    result = template
    for i, tok in enumerate(tokens):
        result = result.replace(f"__TOK{i}__", tok)
    return result


# ── Translation result ────────────────────────────────────────────────────────

class TranslationResult:
    def __init__(
        self,
        translated_text:  str,
        source_language:  str,
        target_language:  str,
        provider:         str,
        confidence:       float,
        is_fallback:      bool = False,
    ):
        self.translated_text  = translated_text
        self.source_language  = source_language
        self.target_language  = target_language
        self.provider         = provider
        self.confidence       = confidence
        self.is_fallback      = is_fallback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "translated_text": self.translated_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "provider":        self.provider,
            "confidence":      self.confidence,
            "is_fallback":     self.is_fallback,
            "disclaimer": (
                "⚠️ Translation is AI-generated. "
                "Official scheme names, financial figures, and URLs are preserved as-is."
            ) if self.target_language != "en" else None,
        }


# ── Abstract provider ─────────────────────────────────────────────────────────

class TranslationProvider(ABC):
    @abstractmethod
    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        ...

    def name(self) -> str:
        return self.__class__.__name__


# ── Fallback provider ─────────────────────────────────────────────────────────
# Provides minimal, honest dictionary-based translation for common UI phrases.
# For full sentences, it returns the original text with a disclaimer.

_COMMON_PHRASES: Dict[str, Dict[str, str]] = {
    "hi": {
        # Common UI labels
        "Dashboard":              "डैशबोर्ड",
        "Profile":                "प्रोफ़ाइल",
        "Logout":                 "लॉग आउट",
        "Login":                  "लॉगिन",
        "Register":               "पंजीकरण",
        "Loading":                "लोड हो रहा है",
        "Error":                  "त्रुटि",
        "Success":                "सफलता",
        "Save":                   "सहेजें",
        "Cancel":                 "रद्द करें",
        "Delete":                 "हटाएं",
        "Edit":                   "संपादित करें",
        "Submit":                 "जमा करें",
        "Back":                   "वापस",
        "Next":                   "अगला",
        "Revenue":                "राजस्व",
        "Expenses":               "खर्च",
        "Profit":                 "लाभ",
        "Investment":             "निवेश",
        "Business":               "व्यापार",
        "Goals":                  "लक्ष्य",
        "Analytics":              "विश्लेषण",
        "Recommendations":        "सिफारिशें",
        "Market":                 "बाज़ार",
        "Government Schemes":     "सरकारी योजनाएं",
        "AI Advisor":             "AI सलाहकार",
        "Financial Analysis":     "वित्तीय विश्लेषण",
        "Ask your question":      "अपना प्रश्न पूछें",
        "Insufficient data":      "अपर्याप्त डेटा",
        "No data available":      "कोई डेटा उपलब्ध नहीं",
        "Voice input":            "वॉयस इनपुट",
        "Speak now":              "अभी बोलें",
        "Listening":              "सुन रहा है",
        "Processing":             "प्रसंस्करण",
    },
    "te": {
        # Common UI labels
        "Dashboard":              "డ్యాష్‌బోర్డ్",
        "Profile":                "ప్రొఫైల్",
        "Logout":                 "లాగ్ అవుట్",
        "Login":                  "లాగిన్",
        "Register":               "నమోదు",
        "Loading":                "లోడ్ అవుతోంది",
        "Error":                  "లోపం",
        "Success":                "విజయం",
        "Save":                   "సేవ్ చేయి",
        "Cancel":                 "రద్దు చేయి",
        "Delete":                 "తొలగించు",
        "Edit":                   "సవరించు",
        "Submit":                 "సమర్పించు",
        "Back":                   "వెనుకకు",
        "Next":                   "తదుపరి",
        "Revenue":                "ఆదాయం",
        "Expenses":               "ఖర్చులు",
        "Profit":                 "లాభం",
        "Investment":             "పెట్టుబడి",
        "Business":               "వ్యాపారం",
        "Goals":                  "లక్ష్యాలు",
        "Analytics":              "విశ్లేషణలు",
        "Recommendations":        "సిఫార్సులు",
        "Market":                 "మార్కెట్",
        "Government Schemes":     "ప్రభుత్వ పథకాలు",
        "AI Advisor":             "AI సలహాదారు",
        "Financial Analysis":     "ఆర్థిక విశ్లేషణ",
        "Ask your question":      "మీ ప్రశ్న అడగండి",
        "Insufficient data":      "తగినంత డేటా లేదు",
        "No data available":      "డేటా అందుబాటులో లేదు",
        "Voice input":            "వాయిస్ ఇన్‌పుట్",
        "Speak now":              "ఇప్పుడు మాట్లాడండి",
        "Listening":              "వింటున్నాను",
        "Processing":             "ప్రాసెస్ అవుతోంది",
    },
}


class FallbackTranslationProvider(TranslationProvider):
    """
    Deterministic translation provider.
    Uses a phrase dictionary for known terms.
    For full sentences/paragraphs, returns original with disclaimer.
    Always preserves numbers, ₹ values, URLs.
    """

    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        if source == target or target == "en":
            return TranslationResult(
                translated_text=text, source_language=source,
                target_language=target, provider="passthrough",
                confidence=1.0, is_fallback=False,
            )

        template, tokens = _tokenise(text)
        phrases = _COMMON_PHRASES.get(target, {})

        translated = template
        # Check for exact single-phrase match
        stripped = text.strip()
        if stripped in phrases:
            translated = phrases[stripped]
            confidence = 0.85
        else:
            # Partial word replacement
            replaced_any = False
            for en_phrase, native in sorted(phrases.items(), key=lambda x: -len(x[0])):
                if en_phrase in translated:
                    translated = translated.replace(en_phrase, native, 1)
                    replaced_any = True
            confidence = 0.5 if replaced_any else 0.1

        result_text = _restore(translated, tokens)

        return TranslationResult(
            translated_text=result_text,
            source_language=source,
            target_language=target,
            provider="fallback_dictionary",
            confidence=confidence,
            is_fallback=True,
        )

    def name(self) -> str:
        return "fallback_dictionary"


# ── Gemini provider ───────────────────────────────────────────────────────────

class GeminiTranslationProvider(TranslationProvider):
    """
    Uses Gemini for high-quality contextual translation.
    Only instantiated when GEMINI_API_KEY is available.
    Falls back gracefully on any error.
    """

    def __init__(self, gemini_client: Any):
        self._client = gemini_client
        self._fallback = FallbackTranslationProvider()

    def translate(self, text: str, source: str, target: str) -> TranslationResult:
        if source == target or target == "en":
            return TranslationResult(
                translated_text=text, source_language=source,
                target_language=target, provider="passthrough",
                confidence=1.0, is_fallback=False,
            )

        # Protect tokens before sending to Gemini
        template, tokens = _tokenise(text)

        target_lang_name = LANGUAGES.get(target, LANGUAGES["en"]).name
        source_lang_name = LANGUAGES.get(source, LANGUAGES["en"]).name

        prompt = (
            f"Translate the following text from {source_lang_name} to {target_lang_name}.\n"
            f"CRITICAL RULES:\n"
            f"1. Preserve ALL placeholder tokens exactly: __TOK0__, __TOK1__, etc.\n"
            f"2. Never alter numbers, percentages, currency values.\n"
            f"3. Preserve official scheme names (MUDRA, PMEGP, etc.).\n"
            f"4. Use simple, clear language suitable for rural entrepreneurs.\n"
            f"5. Return ONLY the translated text, nothing else.\n\n"
            f"TEXT TO TRANSLATE:\n{template}"
        )

        try:
            response = self._client.generate_content(prompt)
            translated_template = response.text.strip() if response and response.text else template
            result_text = _restore(translated_template, tokens)
            return TranslationResult(
                translated_text=result_text,
                source_language=source,
                target_language=target,
                provider="gemini",
                confidence=0.90,
                is_fallback=False,
            )
        except Exception as e:
            logger.warning(f"Gemini translation failed, using fallback: {e}")
            fb = self._fallback.translate(text, source, target)
            fb.provider = "fallback_after_gemini_error"
            return fb

    def name(self) -> str:
        return "gemini"


# ── Translation Service ───────────────────────────────────────────────────────

class TranslationService:
    """
    Main translation service. Auto-selects best available provider.
    Always works without any API key using the fallback provider.
    """

    def __init__(self):
        self._provider: TranslationProvider = FallbackTranslationProvider()
        self._gemini_available = False
        self._try_init_gemini()

    def _try_init_gemini(self) -> None:
        """Attempt to initialise Gemini translation. Silent on failure."""
        try:
            from app.core.config import settings
            import google.generativeai as genai

            api_key = getattr(settings, "GEMINI_API_KEY", None)
            if not api_key or api_key == "your-gemini-api-key-here":
                return

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            self._provider = GeminiTranslationProvider(model)
            self._gemini_available = True
            logger.info("Phase 10: Gemini translation provider initialised.")
        except Exception as e:
            logger.info(f"Phase 10: Gemini unavailable, using fallback translation. ({e})")

    def translate(
        self,
        text:            str,
        target_language: str,
        source_language: str = "en",
    ) -> TranslationResult:
        """
        Translate text to target_language.
        Returns TranslationResult with metadata.
        Numbers, ₹ values, URLs are always preserved.
        """
        if not text or not text.strip():
            return TranslationResult(
                translated_text=text, source_language=source_language,
                target_language=target_language, provider="passthrough",
                confidence=1.0,
            )

        if not is_supported(target_language):
            target_language = "en"

        if source_language == target_language:
            return TranslationResult(
                translated_text=text, source_language=source_language,
                target_language=target_language, provider="passthrough",
                confidence=1.0,
            )

        return self._provider.translate(text, source_language, target_language)

    def translate_to_english(self, text: str, source_language: str) -> TranslationResult:
        """Translate user input to English for internal processing."""
        if source_language == "en":
            return TranslationResult(
                translated_text=text, source_language="en",
                target_language="en", provider="passthrough", confidence=1.0,
            )
        return self.translate(text, target_language="en", source_language=source_language)

    @property
    def provider_name(self) -> str:
        return self._provider.name()

    @property
    def gemini_available(self) -> bool:
        return self._gemini_available


# Singleton instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


def translate_text(
    text: str,
    target_language: str,
    source_language: str = "en",
) -> TranslationResult:
    """Convenience function for one-off translations."""
    return get_translation_service().translate(text, target_language, source_language)
