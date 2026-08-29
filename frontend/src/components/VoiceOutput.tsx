/**
 * Phase 10 — Voice Output Component
 * Uses browser SpeechSynthesis API to read text aloud.
 * Requires explicit user click — never auto-plays.
 * Gracefully handles no voices available.
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { getSpeechCode } from '../types/language'
import type { LanguageCode } from '../types/language'
import { languageService } from '../services/languageService'

interface Props {
  text:       string
  language?:  LanguageCode      // override; defaults to current i18n language
  className?: string
  compact?:   boolean           // show only icon button
}

type PlayState = 'idle' | 'playing' | 'paused'

function getSynth(): SpeechSynthesis | null {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
    ? window.speechSynthesis : null
}

function getBestVoice(lang: string): SpeechSynthesisVoice | null {
  const voices = getSynth()?.getVoices() ?? []
  // Try exact match first, then prefix match
  return (
    voices.find(v => v.lang === lang) ??
    voices.find(v => v.lang.startsWith(lang.split('-')[0])) ??
    voices[0] ?? null
  )
}

export default function VoiceOutput({ text, language, className = '', compact = false }: Props) {
  const { t } = useTranslation()
  const [playState, setPlayState] = useState<PlayState>('idle')
  const [supported, setSupported] = useState(true)
  const uttRef = useRef<SpeechSynthesisUtterance | null>(null)
  const synth = getSynth()

  useEffect(() => {
    if (!synth) setSupported(false)
    // Voices load async in some browsers
    if (synth && synth.getVoices().length === 0) {
      synth.addEventListener('voiceschanged', () => { /* trigger re-render */ }, { once: true })
    }
    return () => { synth?.cancel() }
  }, [synth])

  const lang = language ?? (languageService.getLocalLanguage() as LanguageCode)
  const speechCode = getSpeechCode(lang)

  const play = useCallback(() => {
    if (!synth || !text.trim()) return
    synth.cancel()

    const utt = new SpeechSynthesisUtterance(text)
    utt.lang  = speechCode
    utt.rate  = 0.9
    utt.pitch = 1

    const voice = getBestVoice(speechCode)
    if (voice) utt.voice = voice

    utt.onstart  = () => setPlayState('playing')
    utt.onend    = () => setPlayState('idle')
    utt.onerror  = () => setPlayState('idle')
    utt.onpause  = () => setPlayState('paused')
    utt.onresume = () => setPlayState('playing')

    uttRef.current = utt
    synth.speak(utt)
  }, [synth, text, speechCode])

  const pause = useCallback(() => { synth?.pause(); setPlayState('paused') }, [synth])
  const resume = useCallback(() => { synth?.resume(); setPlayState('playing') }, [synth])
  const stop  = useCallback(() => { synth?.cancel(); setPlayState('idle') }, [synth])

  if (!supported || !text.trim()) return null

  if (compact) {
    return (
      <button
        id="voice-output-compact-btn"
        type="button"
        onClick={playState === 'idle' ? play : stop}
        title={playState === 'idle' ? t('voice.listenResponse') : t('voice.stop')}
        className={`
          p-1.5 rounded-lg transition-all text-sm
          ${playState !== 'idle'
            ? 'text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20'
            : 'text-gray-500 hover:text-gray-300 hover:bg-surface-700/50'}
          ${className}
        `}
      >
        {playState === 'playing' ? '⏸' : playState === 'paused' ? '▶' : '🔊'}
      </button>
    )
  }

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      {/* Play / Pause / Resume */}
      {playState === 'idle' && (
        <button
          id="voice-output-play-btn"
          type="button"
          onClick={play}
          title={t('voice.listenResponse')}
          className="
            flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium
            bg-emerald-500/10 border border-emerald-500/25 text-emerald-400
            hover:bg-emerald-500/20 transition-all
          "
        >
          🔊 {t('voice.listenResponse')}
        </button>
      )}

      {playState === 'playing' && (
        <>
          <button id="voice-output-pause-btn" type="button" onClick={pause}
            title={t('voice.pause')}
            className="px-2 py-1 rounded-lg text-xs bg-yellow-500/10 border border-yellow-500/25 text-yellow-400 hover:bg-yellow-500/20">
            ⏸ {t('voice.pause')}
          </button>
          <button id="voice-output-stop-btn" type="button" onClick={stop}
            title={t('voice.stop')}
            className="px-2 py-1 rounded-lg text-xs bg-red-500/10 border border-red-500/25 text-red-400 hover:bg-red-500/20">
            ⏹ {t('voice.stop')}
          </button>
          {/* Waveform animation */}
          <span className="flex items-end gap-0.5 h-4">
            {[1,2,3,2,1].map((h, i) => (
              <span key={i} className="w-0.5 bg-emerald-400 rounded-full animate-bounce"
                style={{ height: `${h*4}px`, animationDelay: `${i*0.1}s` }} />
            ))}
          </span>
        </>
      )}

      {playState === 'paused' && (
        <>
          <button id="voice-output-resume-btn" type="button" onClick={resume}
            title={t('voice.resume')}
            className="px-2 py-1 rounded-lg text-xs bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/20">
            ▶ {t('voice.resume')}
          </button>
          <button id="voice-output-stop2-btn" type="button" onClick={stop}
            title={t('voice.stop')}
            className="px-2 py-1 rounded-lg text-xs bg-red-500/10 border border-red-500/25 text-red-400 hover:bg-red-500/20">
            ⏹ {t('voice.stop')}
          </button>
        </>
      )}
    </div>
  )
}
