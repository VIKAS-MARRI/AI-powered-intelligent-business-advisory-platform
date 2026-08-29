/**
 * Phase 10 — Voice Input Component
 * Uses browser Web Speech API for speech recognition.
 * Gracefully degrades when unsupported or permission denied.
 * Never requests microphone until user clicks the button.
 */
import { useState, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { getSpeechCode } from '../types/language'
import type { LanguageCode } from '../types/language'
import { languageService } from '../services/languageService'

interface Props {
  onTranscript:    (text: string) => void   // called with final transcript
  onInterim?:      (text: string) => void   // called with interim results
  language?:       LanguageCode             // override; defaults to current i18n language
  disabled?:       boolean
  className?:      string
  buttonLabel?:    string
}

type State = 'idle' | 'listening' | 'error'

// SpeechRecognition type shim
type SpeechRecognitionAny = {
  lang:              string
  continuous:        boolean
  interimResults:    boolean
  maxAlternatives:   number
  start:             () => void
  stop:              () => void
  onresult:          (e: { results: SpeechRecognitionResultList }) => void
  onerror:           (e: { error: string }) => void
  onend:             () => void
}

function getSpeechRecognition(): (new () => SpeechRecognitionAny) | null {
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRecognitionAny
    webkitSpeechRecognition?: new () => SpeechRecognitionAny
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export default function VoiceInput({ onTranscript, onInterim, language, disabled, className = '', buttonLabel }: Props) {
  const { t } = useTranslation()
  const [state,    setState]    = useState<State>('idle')
  const [interim,  setInterim]  = useState('')
  const [errMsg,   setErrMsg]   = useState('')
  const recognitionRef = useRef<SpeechRecognitionAny | null>(null)

  const SpeechRec = getSpeechRecognition()
  const supported = !!SpeechRec

  const lang = language ?? (languageService.getLocalLanguage() as LanguageCode)
  const speechCode = getSpeechCode(lang)

  const start = useCallback(() => {
    if (!SpeechRec) return
    setErrMsg('')
    setInterim('')

    const rec = new SpeechRec()
    rec.lang            = speechCode
    rec.continuous      = false
    rec.interimResults  = true
    rec.maxAlternatives = 1

    rec.onresult = (e) => {
      let interimText = ''
      let finalText   = ''
      for (let i = 0; i < e.results.length; i++) {
        const t = e.results[i][0].transcript
        if (e.results[i].isFinal) finalText += t
        else interimText += t
      }
      setInterim(interimText)
      onInterim?.(interimText)
      if (finalText) {
        onTranscript(finalText.trim())
        setInterim('')
      }
    }

    rec.onerror = (e) => {
      switch (e.error) {
        case 'not-allowed':
        case 'permission-denied':
          setErrMsg(t('voice.permissionDenied'))
          break
        case 'no-speech':
          setErrMsg(t('voice.noSpeech'))
          break
        case 'network':
          setErrMsg(t('voice.networkError'))
          break
        default:
          setErrMsg(`${t('common.error')}: ${e.error}`)
      }
      setState('idle')
    }

    rec.onend = () => {
      setState('idle')
      setInterim('')
    }

    recognitionRef.current = rec
    try {
      rec.start()
      setState('listening')
    } catch {
      setErrMsg(t('voice.unsupported'))
      setState('error')
    }
  }, [SpeechRec, speechCode, onTranscript, onInterim, t])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setState('idle')
  }, [])

  if (!supported) {
    return (
      <div className={`flex items-center gap-2 text-xs text-gray-500 ${className}`}>
        <span>🎤</span>
        <span>{t('voice.unsupported')}</span>
      </div>
    )
  }

  const isListening = state === 'listening'

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <div className="flex items-center gap-2">
        {/* Mic button */}
        <button
          id="voice-input-btn"
          type="button"
          onClick={isListening ? stop : start}
          disabled={disabled}
          aria-label={isListening ? t('voice.stopListening') : t('voice.startListening')}
          className={`
            relative flex items-center gap-2 px-3 py-2 rounded-xl font-medium text-sm
            transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
            ${isListening
              ? 'bg-red-500/20 border border-red-500/40 text-red-400 hover:bg-red-500/30'
              : 'bg-primary-500/15 border border-primary-500/30 text-primary-300 hover:bg-primary-500/25'}
          `}
        >
          {/* Pulse ring when listening */}
          {isListening && (
            <span className="absolute inset-0 rounded-xl animate-ping bg-red-500/10 pointer-events-none" />
          )}
          <span className="text-base">{isListening ? '⏹' : '🎤'}</span>
          <span>{buttonLabel ?? (isListening ? t('voice.listening') : t('voice.speak'))}</span>
          {isListening && (
            <span className="flex gap-0.5 items-end h-4">
              {[1, 2, 3].map(i => (
                <span key={i} className={`w-0.5 bg-red-400 rounded-full animate-bounce`}
                  style={{ height: `${6 + i * 3}px`, animationDelay: `${i * 0.1}s` }} />
              ))}
            </span>
          )}
        </button>

        {/* Interim text badge */}
        {interim && (
          <span className="text-xs text-gray-400 italic truncate max-w-[150px]">
            {interim}
          </span>
        )}
      </div>

      {/* Error message */}
      {errMsg && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <span>⚠️</span> {errMsg}
        </p>
      )}
    </div>
  )
}
