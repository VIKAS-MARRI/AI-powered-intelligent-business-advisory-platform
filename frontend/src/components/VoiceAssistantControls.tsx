/**
 * Phase 10 — Section 12: Voice Assistant Controls
 * Reusable panel combining VoiceInput + VoiceOutput + language indicator.
 * Large buttons, mobile-friendly, high contrast, accessible labels.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import VoiceInput from './VoiceInput'
import VoiceOutput from './VoiceOutput'
import LanguageSelector from './LanguageSelector'
import type { LanguageCode } from '../types/language'

interface Props {
  /** Called when the user finalises a voice transcript */
  onTranscript: (text: string) => void
  /** Text to be read aloud by TTS (optional) */
  responseText?: string
  /** Override current language (defaults to i18n language) */
  language?: LanguageCode
  /** Disable voice input (e.g. while loading) */
  disabled?: boolean
  /** Show a transcript panel below the buttons */
  showTranscript?: boolean
  className?: string
}

export default function VoiceAssistantControls({
  onTranscript,
  responseText,
  language,
  disabled = false,
  showTranscript = true,
  className = '',
}: Props) {
  const { t } = useTranslation()
  const [transcript, setTranscript] = useState('')

  const handleTranscript = (text: string) => {
    setTranscript(text)
    onTranscript(text)
  }

  return (
    <div
      className={`rounded-2xl bg-surface-800/60 border border-surface-700/30 p-4 space-y-4 ${className}`}
      role="region"
      aria-label="Voice Assistant Controls"
    >
      {/* ── Title row ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden="true">🎙️</span>
          <span className="text-sm font-semibold text-white">Voice Assistant</span>
        </div>
        {/* 🌐 Language selector */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider" aria-hidden="true">🌐</span>
          <LanguageSelector compact />
        </div>
      </div>

      {/* ── Buttons row ── */}
      <div className="flex flex-wrap gap-3">
        {/* 🎤 Speak — voice input */}
        <div className="flex-1 min-w-[120px]">
          <VoiceInput
            onTranscript={handleTranscript}
            onInterim={(t) => setTranscript(t)}
            language={language}
            disabled={disabled}
            className="w-full"
            buttonLabel={t('voice.speak')}
          />
        </div>

        {/* 🔊 Listen — voice output */}
        {responseText && responseText.trim() && (
          <div className="flex-1 min-w-[120px]">
            <VoiceOutput
              text={responseText}
              language={language}
            />
          </div>
        )}
      </div>

      {/* ── 📝 Transcript panel ── */}
      {showTranscript && transcript && (
        <div className="rounded-xl bg-surface-700/30 border border-surface-600/20 px-3 py-2.5">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">
            📝 {t('voice.transcript')}
          </p>
          <p className="text-sm text-gray-200 leading-relaxed">{transcript}</p>
        </div>
      )}
    </div>
  )
}
