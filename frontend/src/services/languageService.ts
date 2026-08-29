/**
 * Phase 10 — Language & Accessibility API service
 */
import api from './api'
import i18n from '../i18n/i18n'
import type {
  LanguageCode,
  LanguageListResponse,
  LanguagePreference,
  AccessibilityPreference,
  TranslationRequest,
  TranslationResult,
} from '../types/language'

const LS_KEY = 'ruralbiz_language'

// ── Language preference ───────────────────────────────────────────────────────

export const languageService = {
  /** Read language from localStorage (works unauthenticated) */
  getLocalLanguage(): LanguageCode {
    const stored = localStorage.getItem(LS_KEY)
    if (stored && ['en', 'hi', 'te'].includes(stored)) return stored as LanguageCode
    return 'en'
  },

  /** Persist language in localStorage and update i18n */
  setLocalLanguage(lang: LanguageCode): void {
    localStorage.setItem(LS_KEY, lang)
    i18n.changeLanguage(lang)
  },

  /** GET /users/language — returns user's backend preference */
  async getPreference(): Promise<LanguagePreference> {
    const r = await api.get<LanguagePreference>('/users/language')
    return r.data
  },

  /** PATCH /users/language — sync language to backend */
  async updatePreference(language: LanguageCode): Promise<void> {
    await api.patch('/users/language', { language })
  },

  /** GET /languages — public list of supported languages */
  async listLanguages(): Promise<LanguageListResponse> {
    const r = await api.get<LanguageListResponse>('/languages')
    return r.data
  },

  /**
   * Change language: update localStorage, i18n, and backend (if authenticated).
   * Silently ignores backend errors for unauthenticated users.
   */
  async changeLanguage(lang: LanguageCode, isAuthenticated = false): Promise<void> {
    this.setLocalLanguage(lang)
    if (isAuthenticated) {
      try { await this.updatePreference(lang) } catch { /* ok if not logged in */ }
    }
  },

  /**
   * On login: sync backend preference to local state.
   * Prioritises backend preference over localStorage.
   */
  async syncOnLogin(): Promise<LanguageCode> {
    try {
      const pref = await this.getPreference()
      this.setLocalLanguage(pref.language as LanguageCode)
      return pref.language as LanguageCode
    } catch {
      return this.getLocalLanguage()
    }
  },
}

// ── Accessibility ─────────────────────────────────────────────────────────────

export const accessibilityService = {
  async get(): Promise<AccessibilityPreference> {
    const r = await api.get<AccessibilityPreference>('/users/accessibility')
    return r.data
  },

  async setSimpleLanguage(enabled: boolean): Promise<void> {
    await api.patch('/users/accessibility', { simple_language_mode: enabled })
  },
}

// ── Translation ───────────────────────────────────────────────────────────────

export const translationService = {
  async translate(req: TranslationRequest): Promise<TranslationResult> {
    const r = await api.post<TranslationResult>('/language/translate', req)
    return r.data
  },

  async translateToCurrentLanguage(text: string): Promise<string> {
    const lang = languageService.getLocalLanguage()
    if (lang === 'en') return text
    try {
      const r = await this.translate({ text, target_language: lang, source_language: 'en' })
      return r.translated_text
    } catch {
      return text // always return original on failure
    }
  },
}
