"""
Phase 10 — Language configuration.
Centralized multilingual architecture for RuralBiz AI.
Supports English, Hindi, Telugu with extensible design.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LanguageConfig:
    code:        str    # ISO 639-1/BCP-47
    name:        str    # English name
    native_name: str    # Name in the language itself
    supported:   bool   = True
    fallback:    str    = "en"   # fallback language code
    # BCP-47 tag for SpeechRecognition/SpeechSynthesis
    speech_code: str    = "en-IN"


# ── Supported Languages ───────────────────────────────────────────────────────

LANGUAGES: Dict[str, LanguageConfig] = {
    "en": LanguageConfig(
        code="en",
        name="English",
        native_name="English",
        supported=True,
        fallback="en",
        speech_code="en-IN",
    ),
    "hi": LanguageConfig(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        supported=True,
        fallback="en",
        speech_code="hi-IN",
    ),
    "te": LanguageConfig(
        code="te",
        name="Telugu",
        native_name="తెలుగు",
        supported=True,
        fallback="en",
        speech_code="te-IN",
    ),
}

DEFAULT_LANGUAGE = "en"
SUPPORTED_CODES: List[str] = [code for code, cfg in LANGUAGES.items() if cfg.supported]


def get_language(code: str) -> LanguageConfig:
    """Return config for a language code, falling back to English."""
    return LANGUAGES.get(code, LANGUAGES[DEFAULT_LANGUAGE])


def is_supported(code: str) -> bool:
    return code in SUPPORTED_CODES


def get_all_languages() -> List[Dict]:
    """Return list of supported language descriptors for API responses."""
    return [
        {
            "code":        cfg.code,
            "name":        cfg.name,
            "native_name": cfg.native_name,
            "supported":   cfg.supported,
            "speech_code": cfg.speech_code,
        }
        for cfg in LANGUAGES.values()
        if cfg.supported
    ]
