// Phase 10 — Language TypeScript types

export type LanguageCode = 'en' | 'hi' | 'te'

export interface LanguageConfig {
  code:        LanguageCode
  name:        string
  native_name: string
  supported:   boolean
  speech_code: string
  flag:        string
}

export interface LanguageListResponse {
  languages: LanguageConfig[]
  default:   string
}

export interface LanguagePreference {
  language:           LanguageCode
  supported_languages: LanguageConfig[]
}

export interface AccessibilityPreference {
  simple_language_mode: boolean
  preferred_language:   LanguageCode
}

export interface TranslationRequest {
  text:            string
  target_language: LanguageCode
  source_language?: string
}

export interface TranslationResult {
  translated_text:  string
  source_language:  string
  target_language:  string
  provider:         string
  confidence:       number
  is_fallback:      boolean
  disclaimer:       string | null
}

// Language selector option for UI
export const LANGUAGE_OPTIONS: LanguageConfig[] = [
  { code: 'en', name: 'English',  native_name: 'English',  supported: true, speech_code: 'en-IN', flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi',    native_name: 'हिन्दी',   supported: true, speech_code: 'hi-IN', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu',   native_name: 'తెలుగు',   supported: true, speech_code: 'te-IN', flag: '🇮🇳' },
]

export function getSpeechCode(lang: LanguageCode): string {
  return LANGUAGE_OPTIONS.find(l => l.code === lang)?.speech_code ?? 'en-IN'
}

export function getLanguageConfig(lang: LanguageCode): LanguageConfig {
  return LANGUAGE_OPTIONS.find(l => l.code === lang) ?? LANGUAGE_OPTIONS[0]
}

export function isValidLanguage(code: string): code is LanguageCode {
  return ['en', 'hi', 'te'].includes(code)
}
