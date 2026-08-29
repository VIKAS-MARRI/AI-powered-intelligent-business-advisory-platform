/**
 * Phase 10 — Language Selector Component
 * Dropdown to switch between English, Hindi, Telugu.
 * Works for both authenticated and unauthenticated users.
 * Persists to localStorage; syncs to backend when logged in.
 */
import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { LANGUAGE_OPTIONS } from '../types/language'
import type { LanguageCode } from '../types/language'
import { languageService } from '../services/languageService'
import { useAuth } from '../context/AuthContext'

interface Props {
  compact?: boolean   // show only flag in mobile nav
}

export default function LanguageSelector({ compact = false }: Props) {
  const { i18n, t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const [open, setOpen] = useState(false)
  const ref  = useRef<HTMLDivElement>(null)

  const current = LANGUAGE_OPTIONS.find(l => l.code === i18n.language)
    ?? LANGUAGE_OPTIONS[0]

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSelect = async (code: LanguageCode) => {
    setOpen(false)
    await languageService.changeLanguage(code, isAuthenticated)
  }

  return (
    <div ref={ref} className="relative">
      {/* Trigger button */}
      <button
        id="language-selector-btn"
        onClick={() => setOpen(v => !v)}
        aria-label={t('language.title')}
        className={`
          flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl
          bg-surface-700/40 border border-surface-600/30
          hover:border-surface-500/50 hover:bg-surface-700/60
          text-white text-xs font-medium transition-all duration-150
          ${open ? 'border-primary-500/50 bg-surface-700/70' : ''}
        `}
      >
        <span className="text-sm">{current.flag}</span>
        {!compact && (
          <span className="hidden sm:inline">{current.native_name}</span>
        )}
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div className="
          absolute right-0 mt-1.5 w-44 z-50
          bg-surface-800/95 backdrop-blur-md
          border border-surface-600/40 rounded-2xl shadow-2xl
          overflow-hidden animate-fade-in
        ">
          <div className="px-3 py-2 border-b border-surface-700/30">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">
              🌐 {t('language.title')}
            </p>
          </div>
          {LANGUAGE_OPTIONS.map(lang => (
            <button
              key={lang.code}
              id={`lang-option-${lang.code}`}
              onClick={() => handleSelect(lang.code as LanguageCode)}
              className={`
                w-full flex items-center gap-2.5 px-3 py-2.5
                text-sm text-left transition-colors duration-100
                ${lang.code === current.code
                  ? 'bg-primary-500/15 text-primary-300'
                  : 'text-gray-300 hover:bg-surface-700/50 hover:text-white'}
              `}
            >
              <span className="text-base">{lang.flag}</span>
              <div>
                <p className="font-medium">{lang.native_name}</p>
                {lang.native_name !== lang.name && (
                  <p className="text-[10px] text-gray-500">{lang.name}</p>
                )}
              </div>
              {lang.code === current.code && (
                <svg className="w-3 h-3 ml-auto text-primary-400 shrink-0"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
