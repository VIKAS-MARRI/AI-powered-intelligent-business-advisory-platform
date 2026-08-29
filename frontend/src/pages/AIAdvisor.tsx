/**
 * AIAdvisor — Phase 7 + Phase 10 (Multilingual & Voice).
 *
 * Sections:
 *  1. Question input + voice input + suggested prompts
 *  2. Context panel (capital, business, location, state)
 *  3. Agent activity progress display
 *  4. Final advice — structured action plan + voice output
 *  5. Expandable specialist sections (business, finance, market, schemes)
 *  6. Advisory history
 *  7. AI status badge + disclaimer
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useAuth } from '../context/AuthContext'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { useLocation } from 'react-router-dom'
import { advisoryService } from '../services/advisoryService'
import VoiceInput from '../components/VoiceInput'
import VoiceOutput from '../components/VoiceOutput'
import { languageService } from '../services/languageService'
import type { LanguageCode } from '../types/language'

import type { AdvisoryResultOut, AdvisoryHistoryItem, FinalAdviceOut } from '../types/advisory'

// ── Constants ─────────────────────────────────────────────────────────────────

const SUGGESTED_QUESTIONS = [
  { icon: '💡', text: 'What business can I start with ₹2 lakh in my area?' },
  { icon: '📍', text: 'Is a dairy business good for my location and capital?' },
  { icon: '💰', text: 'How should I invest my available capital for best returns?' },
  { icon: '🏛️', text: 'What government support and schemes may be available to me?' },
  { icon: '📊', text: 'What is the financial feasibility of a tailoring shop?' },
  { icon: '🌾', text: 'What rural business can I start with limited skills?' },
]

const AGENT_LABELS: Record<string, { icon: string; label: string; color: string }> = {
  business: { icon: '💼', label: 'Analyzing business options',       color: 'text-primary-400'  },
  finance:  { icon: '📊', label: 'Reviewing financial feasibility',  color: 'text-emerald-400'  },
  market:   { icon: '🗺️', label: 'Checking local market',            color: 'text-teal-400'     },
  scheme:   { icon: '🏛️', label: 'Finding relevant government support', color: 'text-indigo-400' },
}

const PROCESSING_STEPS = [
  { icon: '🎯', label: 'Understanding your question…'    },
  { icon: '💼', label: 'Analyzing business options…'     },
  { icon: '📊', label: 'Reviewing financial feasibility…'},
  { icon: '🗺️', label: 'Checking local market…'          },
  { icon: '🏛️', label: 'Finding government support…'     },
  { icon: '🧠', label: 'Preparing your action plan…'     },
]

const ADVISORY_DISCLAIMER = `RuralBiz AI provides AI-assisted business guidance based on available system data. Recommendations, financial estimates, market information, and scheme matches are intended for planning and decision support only. They do not guarantee business success, profits, funding approval, or eligibility. Always verify important financial, legal, and government information through appropriate official or professional sources.`

// ── Small components ──────────────────────────────────────────────────────────

function AIStatusBadge({ status }: { status: string }) {
  const cfg = {
    available:   { cls: 'border-emerald-700/40 bg-emerald-900/20 text-emerald-400', label: '🤖 AI Active',     dot: 'bg-emerald-400' },
    limited:     { cls: 'border-amber-700/40  bg-amber-900/20  text-amber-400',    label: '⚡ AI Limited',    dot: 'bg-amber-400'   },
    unavailable: { cls: 'border-slate-700/40  bg-slate-800/30  text-slate-400',    label: '📊 Data Mode',     dot: 'bg-slate-400'   },
  }[status] ?? { cls: 'border-slate-700/40 bg-slate-800/30 text-slate-400', label: '📊 Data Mode', dot: 'bg-slate-400' }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${cfg.cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

function AgentBadge({ agent }: { agent: string }) {
  const cfg = AGENT_LABELS[agent] ?? { icon: '🔍', label: agent, color: 'text-gray-400' }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-700/40 border border-surface-600/30 text-xs ${cfg.color}`}>
      {cfg.icon} {agent}
    </span>
  )
}

function SectionCard({
  icon, title, children, defaultOpen = false,
  badge, badgeColor,
}: {
  icon: string; title: string; children: React.ReactNode
  defaultOpen?: boolean; badge?: string; badgeColor?: string
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-surface-700/10 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className="text-sm font-semibold text-white">{title}</span>
          {badge && (
            <span className={`text-[10px] px-2 py-0.5 rounded border ${badgeColor ?? 'border-primary-700/40 bg-primary-900/20 text-primary-400'}`}>
              {badge}
            </span>
          )}
        </div>
        <span className={`text-gray-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {open && <div className="px-5 pb-5 border-t border-surface-700/20">{children}</div>}
    </div>
  )
}

// ── Processing Spinner ────────────────────────────────────────────────────────

function ProcessingDisplay({ step }: { step: number }) {
  return (
    <div className="card p-8 text-center space-y-5">
      <div className="w-12 h-12 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto" />
      <div className="space-y-2">
        {PROCESSING_STEPS.map((s, i) => (
          <div
            key={i}
            className={`flex items-center gap-2 justify-center text-sm transition-all duration-300 ${
              i < step  ? 'text-emerald-400 opacity-60' :
              i === step ? 'text-white font-semibold' :
              'text-gray-600 opacity-40'
            }`}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
            {i < step && <span className="text-emerald-500 text-xs">✓</span>}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Final Advice Display ──────────────────────────────────────────────────────

function FinalAdviceCard({
  advice, agents, aiStatus,
}: {
  advice:   FinalAdviceOut
  agents:   string[]
  aiStatus: string
}) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card p-5 bg-gradient-to-br from-primary-900/20 to-transparent border-primary-700/30">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            <h2 className="text-lg font-display font-bold text-white">Your Personalized Action Plan</h2>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <AIStatusBadge status={aiStatus} />
            {advice.ai_generated ? (
              <span className="text-[10px] px-2 py-0.5 rounded border border-primary-700/40 bg-primary-900/20 text-primary-400">AI Generated</span>
            ) : (
              <span className="text-[10px] px-2 py-0.5 rounded border border-slate-700/40 bg-slate-800/30 text-slate-400">System Analysis</span>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {agents.map(a => <AgentBadge key={a} agent={a} />)}
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">{advice.summary}</p>
      </div>

      {/* Recommendation */}
      {advice.recommendation && (
        <div className="card p-5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
            <span>🎯</span> My Recommendation
          </h3>
          <p className="text-sm text-gray-300 leading-relaxed">{advice.recommendation}</p>
        </div>
      )}

      {/* 2-column grid: Financial Plan + Market Insight */}
      {(advice.financial_plan || advice.market_insight) && (
        <div className="grid md:grid-cols-2 gap-4">
          {advice.financial_plan && (
            <div className="card p-5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
                <span>💰</span> Financial Plan
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">{advice.financial_plan}</p>
            </div>
          )}
          {advice.market_insight && (
            <div className="card p-5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
                <span>📍</span> Local Market Insight
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">{advice.market_insight}</p>
            </div>
          )}
        </div>
      )}

      {/* Government Support */}
      {advice.government_support && (
        <div className="card p-5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
            <span>🏛️</span> Possible Government Support
          </h3>
          <p className="text-xs text-gray-400 leading-relaxed">{advice.government_support}</p>
        </div>
      )}

      {/* 2-column grid: Risks + Next Steps */}
      <div className="grid md:grid-cols-2 gap-4">
        {advice.risks.length > 0 && (
          <div className="card p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-3">
              <span>⚠️</span> Key Risks
            </h3>
            <ul className="space-y-2">
              {advice.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                  <span className="text-amber-500 mt-0.5 shrink-0">•</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}
        {advice.next_steps.length > 0 && (
          <div className="card p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-3">
              <span>📋</span> Your Next Steps
            </h3>
            <ol className="space-y-2">
              {advice.next_steps.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-gray-300">
                  <span className="w-5 h-5 rounded-full bg-primary-900/50 border border-primary-700/40 text-primary-400 flex items-center justify-center shrink-0 font-bold text-[10px]">
                    {i + 1}
                  </span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="rounded-xl bg-amber-900/10 border border-amber-700/20 px-4 py-3 text-xs text-amber-700/80">
        ⚠️ <strong>Disclaimer:</strong> {ADVISORY_DISCLAIMER}
      </div>
    </div>
  )
}

// ── Specialist Detail Sections ────────────────────────────────────────────────

function BusinessSection({ data }: { data: Record<string, unknown> }) {
  const recs = (data.recommendations as unknown[]) ?? []
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs text-gray-500">Source: {String(data.data_source ?? 'Phase 2 Recommendation Engine')}</p>
      {recs.slice(0, 3).map((r: unknown, i) => {
        const rec = r as Record<string, unknown>
        return (
          <div key={i} className="bg-surface-700/30 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-white">{String(rec.name ?? '—')}</p>
              <span className="text-xs text-primary-400 font-bold">{Number(rec.score ?? 0).toFixed(0)}/100</span>
            </div>
            <p className="text-xs text-gray-500">
              Investment: ₹{Number(rec.min_investment ?? 0).toLocaleString('en-IN')}–₹{Number(rec.max_investment ?? 0).toLocaleString('en-IN')} | Risk: {String(rec.risk_level ?? '?')}
            </p>
          </div>
        )
      })}
    </div>
  )
}

function FinanceSection({ data }: { data: Record<string, unknown> }) {
  const rows = [
    { label: 'Investment Required', value: data.investment_required !== undefined ? `₹${Number(data.investment_required).toLocaleString('en-IN')}` : null },
    { label: 'Available Capital',   value: data.available_capital   !== undefined ? `₹${Number(data.available_capital).toLocaleString('en-IN')}` : null },
    { label: 'Funding Gap',         value: data.funding_gap         !== undefined ? `₹${Number(data.funding_gap).toLocaleString('en-IN')}` : null },
    { label: 'Est. Monthly Profit', value: data.monthly_profit      !== undefined ? `₹${Number(data.monthly_profit).toLocaleString('en-IN')}` : null },
    { label: 'Break-Even',          value: data.break_even_months   !== undefined ? `${Number(data.break_even_months).toFixed(1)} months` : null },
    { label: 'Annual ROI',          value: data.annual_roi_pct      !== undefined ? `${Number(data.annual_roi_pct).toFixed(1)}%` : null },
  ].filter(r => r.value !== null && r.value !== '₹0')
  return (
    <div className="mt-4">
      <p className="text-xs text-gray-500 mb-3">Source: Phase 3 Financial Calculator (deterministic)</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {rows.map(row => (
          <div key={row.label} className="bg-surface-700/30 rounded-lg p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">{row.label}</p>
            <p className="text-sm font-bold text-white">{row.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function MarketSection({ data }: { data: Record<string, unknown> }) {
  if (data.status === 'skipped') {
    return <p className="mt-3 text-sm text-gray-500 italic">{String(data.message ?? 'Location coordinates required for market analysis.')}</p>
  }
  const insights = (data.insights as Array<Record<string, string>>) ?? []
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs text-gray-500">Source: Phase 5 OpenStreetMap / Overpass API (real data)</p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {data.competition_level !== undefined && data.competition_level !== null && (
          <div className="bg-surface-700/30 rounded-lg p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">Competition</p>
            <p className="text-sm font-bold text-white">{String(data.competition_level)}</p>
          </div>
        )}
        {data.direct_competitors !== undefined && (
          <div className="bg-surface-700/30 rounded-lg p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">Direct Competitors</p>
            <p className="text-sm font-bold text-white">{String(data.direct_competitors)}</p>
          </div>
        )}
        {data.market_opportunity_score !== undefined && data.market_opportunity_score !== null && (
          <div className="bg-surface-700/30 rounded-lg p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">Opportunity Score</p>
            <p className="text-sm font-bold text-emerald-400">{Number(data.market_opportunity_score).toFixed(0)}/100</p>
          </div>
        )}
        {data.location_suitability_score !== undefined && data.location_suitability_score !== null && (
          <div className="bg-surface-700/30 rounded-lg p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">Location Suitability</p>
            <p className="text-sm font-bold text-primary-400">{Number(data.location_suitability_score).toFixed(0)}/100</p>
          </div>
        )}
      </div>
      {insights.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-1.5">Key Insights:</p>
          <ul className="space-y-1">
            {insights.slice(0, 3).map((ins, i) => (
              <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                <span className="text-teal-500 mt-0.5 shrink-0">•</span>
                {ins.message ?? String(ins)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function SchemeSection({ data }: { data: Record<string, unknown> }) {
  const matches = (data.matches as unknown[]) ?? []
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs text-gray-500">Source: Phase 6 Scheme Matcher (verified scheme data)</p>
      {matches.slice(0, 3).map((m: unknown, i) => {
        const match = m as Record<string, unknown>
        return (
          <div key={i} className="bg-surface-700/30 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-white line-clamp-1">{String(match.scheme_name ?? '—')}</p>
              <span className="text-xs text-indigo-400 font-bold shrink-0 ml-2">{Number(match.score ?? 0).toFixed(0)}/100</span>
            </div>
            <p className="text-xs text-gray-500 mb-1.5">{String(match.eligibility_status ?? '—')} | {String(match.funding_relevance ?? '—')}</p>
            <a href={String(match.official_url ?? '#')} target="_blank" rel="noopener noreferrer"
              className="text-[10px] text-primary-400 hover:text-primary-300">
              Official Information ↗
            </a>
          </div>
        )
      })}
    </div>
  )
}

// ── History Tab ───────────────────────────────────────────────────────────────

function HistoryPanel({
  items, onReask,
}: {
  items: AdvisoryHistoryItem[]
  onReask: (q: string) => void
}) {
  if (items.length === 0) {
    return (
      <div className="card p-10 text-center text-gray-500">
        <div className="text-4xl mb-3">📖</div>
        <p className="text-sm">No advisory history yet. Ask your first question above!</p>
      </div>
    )
  }
  return (
    <div className="space-y-3">
      {items.map(item => (
        <div key={item.id} className="card p-4 hover:border-surface-600/50 transition-colors">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium line-clamp-2 mb-1.5">{item.question}</p>
              {item.summary && (
                <p className="text-xs text-gray-500 line-clamp-2">{item.summary}</p>
              )}
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                {item.required_agents.map(a => <AgentBadge key={a} agent={a} />)}
                <AIStatusBadge status={item.ai_status} />
                <span className="text-[10px] text-gray-600">{new Date(item.created_at).toLocaleDateString('en-IN')}</span>
              </div>
            </div>
            <button
              onClick={() => onReask(item.question)}
              className="text-xs text-gray-500 hover:text-white border border-surface-700/40 hover:border-surface-600 px-2.5 py-1.5 rounded-lg transition-colors shrink-0"
            >
              Ask again
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AIAdvisor() {
  const { user } = useAuth()
  const { t } = useTranslation()

  // Current UI language for voice features
  const currentLang = languageService.getLocalLanguage() as LanguageCode

  const [question, setQuestion]           = useState('')
  const [capital, setCapital]             = useState('')
  const [stateName, setStateName]         = useState('')
  const [showContext, setShowContext]      = useState(false)

  const [loading, setLoading]             = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [result, setResult]               = useState<AdvisoryResultOut | null>(null)
  const [error, setError]                 = useState<string | null>(null)

  const [aiStatus, setAiStatus]           = useState<string>('unavailable')
  const [history, setHistory]             = useState<AdvisoryHistoryItem[]>([])
  const [activeTab, setActiveTab]         = useState<'advisor' | 'history'>('advisor')

  const stepTimerRef = useRef<number | null>(null)
  const textareaRef  = useRef<HTMLTextAreaElement>(null)

  // Phase 10: build full response text for TTS
  const responseText = result?.final_advice
    ? [
        result.final_advice.summary,
        result.final_advice.recommendation,
        result.final_advice.financial_plan,
        result.final_advice.market_insight,
      ]
        .filter(Boolean)
        .join('. ')
    : ''

  // Load AI status and history on mount
  useEffect(() => {
    advisoryService.status().then(s => setAiStatus(s.status)).catch(() => {})
    advisoryService.history().then(h => setHistory(h.items)).catch(() => {})
    if (user?.state && !stateName) setStateName(user.state)
    if (user?.available_capital && !capital) setCapital(Math.round(user.available_capital).toString())
  }, [user])

  const loc = useLocation()
  const params = new URLSearchParams(loc.search)
  const autoplay = params.get('autoplay') === '1'
  const { demoProfile } = useDemo()

  // Prefill demo question and context
  useEffect(() => {
    if (!demoProfile) return
    if (demoProfile.scenario && !question) setQuestion(demoProfile.scenario)
    if (demoProfile.available_capital && !capital) setCapital(String(demoProfile.available_capital))
    if (demoProfile.state && !stateName) setStateName(demoProfile.state)
  }, [demoProfile])

  // Auto-run advisory when autoplay=1
  useEffect(() => {
    if (!autoplay || !demoProfile) return
    const t = setTimeout(() => {
      if (question && !loading && !result) {
        void handleAsk()
      }
    }, 800)
    return () => clearTimeout(t)
  }, [autoplay, demoProfile, question, loading, result])

  // Advance processing step indicator
  const startProcessingSteps = () => {
    setProcessingStep(0)
    let step = 0
    const advance = () => {
      step = Math.min(step + 1, PROCESSING_STEPS.length - 1)
      setProcessingStep(step)
      if (step < PROCESSING_STEPS.length - 1) {
        stepTimerRef.current = window.setTimeout(advance, 1200)
      }
    }
    stepTimerRef.current = window.setTimeout(advance, 800)
  }

  const stopProcessingSteps = () => {
    if (stepTimerRef.current) clearTimeout(stepTimerRef.current)
    setProcessingStep(PROCESSING_STEPS.length - 1)
  }

  const handleAsk = useCallback(async () => {
    const q = question.trim()
    if (!q) { setError('Please enter a question.'); return }
    setError(null)
    setResult(null)
    setLoading(true)
    startProcessingSteps()

    try {
      const res = await advisoryService.query({
        question:           q,
        available_capital:  capital   ? parseFloat(capital)   : undefined,
        state_name:         stateName || undefined,
      })
      stopProcessingSteps()
      setResult(res)
      setAiStatus(res.ai_status)
      // Refresh history
      advisoryService.history().then(h => setHistory(h.items)).catch(() => {})
    } catch (e: unknown) {
      stopProcessingSteps()
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Advisory system encountered an error. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [question, capital, stateName])

  const handleSuggestedQuestion = (text: string) => {
    setQuestion(text)
    textareaRef.current?.focus()
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            🤖 <span className="text-gradient">RuralBiz AI Advisor</span>
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Ask anything about starting, financing, or growing your rural business.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {demoProfile && <div className="text-xs text-amber-300 font-semibold">Demo Data</div>}
          <DemoProgress />
          <AIStatusBadge status={aiStatus} />
          <Link to="/scheme-support" className="btn-outline text-xs px-3 py-1.5">🏛️ Schemes</Link>
        </div>
      </div>

      {/* ── Tab bar ── */}
      <div className="flex gap-1 p-1 bg-surface-800/50 rounded-xl w-fit">
        {([['advisor', '🤖 AI Advisor'], ['history', '📖 History']] as const).map(([tab, label]) => (
          <button
            key={tab}
            id={`tab-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm rounded-lg transition-all ${
              activeTab === tab
                ? 'bg-surface-700 text-white font-semibold'
                : 'text-gray-500 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Advisor Tab ── */}
      {activeTab === 'advisor' && (
        <div className="space-y-5">
          {/* Question input */}
          <div className="card p-5">
            <label className="text-xs font-medium text-gray-400 mb-2 block">
              {t('advisor.title')} — {t('voice.speak')} or Type
            </label>
            <textarea
              id="advisor-question"
              ref={textareaRef}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAsk() }}
              rows={3}
              placeholder={t('advisor.askPlaceholder')}
              className="w-full bg-surface-700/30 border border-surface-600/50 text-white text-sm rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600 resize-none"
            />
            <p className="text-[10px] text-gray-600 mt-1">Tip: Press Ctrl+Enter to submit</p>

            {/* Phase 10 — Voice Input row */}
            <div className="mt-3 flex items-center gap-3">
              <VoiceInput
                onTranscript={text => {
                  setQuestion(text)
                  // Auto-submit after voice input for fluid UX
                  setTimeout(() => textareaRef.current?.focus(), 100)
                }}
                language={currentLang}
                disabled={loading}
                buttonLabel={t('voice.speak')}
              />
              {result && responseText && (
                <VoiceOutput
                  text={responseText}
                  language={currentLang}
                />
              )}
            </div>

            {/* Suggested questions */}
            <div className="mt-3">
              <p className="text-[10px] text-gray-500 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTED_QUESTIONS.map((sq, i) => (
                  <button
                    key={i}
                    id={`suggested-q-${i}`}
                    onClick={() => handleSuggestedQuestion(sq.text)}
                    className="text-[11px] px-2.5 py-1 rounded-full border border-surface-600/40 text-gray-500 hover:text-white hover:border-primary-500/40 transition-all"
                  >
                    {sq.icon} {sq.text.slice(0, 40)}{sq.text.length > 40 ? '…' : ''}
                  </button>
                ))}
              </div>
            </div>

            {/* Context panel toggle */}
            <button
              onClick={() => setShowContext(o => !o)}
              className="mt-3 text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors"
            >
              <span className={`transition-transform duration-200 ${showContext ? 'rotate-90' : ''}`}>▶</span>
              {showContext ? 'Hide' : 'Add'} context ({t('advisor.capital')}, state)
            </button>

            {/* Context fields */}
            {showContext && (
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] text-gray-500">{t('advisor.capital')} (₹)</label>
                  <input
                    id="advisor-capital"
                    type="number" value={capital} onChange={e => setCapital(e.target.value)}
                    placeholder="e.g. 200000"
                    className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-gray-500">State</label>
                  <input
                    id="advisor-state"
                    type="text" value={stateName} onChange={e => setStateName(e.target.value)}
                    placeholder="e.g. Telangana"
                    className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
                  />
                </div>
              </div>
            )}

            {error && (
              <div className="mt-3 text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5">{error}</div>
            )}

            <button
              id="ask-advisor-btn"
              onClick={handleAsk}
              disabled={loading || !question.trim()}
              className="mt-4 btn-primary px-6 py-2.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />{t('advisor.processing')}</>
              ) : `🤖 ${t('advisor.askBtn')}`}
            </button>
          </div>

          {/* Processing indicator */}
          {loading && <ProcessingDisplay step={processingStep} />}

          {/* Results */}
          {!loading && result && (
            <div className="space-y-4">
              {/* Final advice */}
              <FinalAdviceCard
                advice={result.final_advice}
                agents={result.required_agents}
                aiStatus={result.ai_status}
              />

              {/* Expandable specialist sections */}
              {Object.keys(result.results).length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                    Detailed Specialist Analysis
                  </h3>

                  {Boolean(result.results.business) && (
                    <SectionCard icon="💼" title="Business Analysis"
                      badge="Phase 2" badgeColor="border-primary-700/40 bg-primary-900/20 text-primary-400">
                      <BusinessSection data={result.results.business as Record<string, unknown>} />
                    </SectionCard>
                  )}
                  {Boolean(result.results.finance) && (
                    <SectionCard icon="📊" title="Financial Analysis"
                      badge="Phase 3" badgeColor="border-emerald-700/40 bg-emerald-900/20 text-emerald-400">
                      <FinanceSection data={result.results.finance as Record<string, unknown>} />
                    </SectionCard>
                  )}
                  {Boolean(result.results.market) && (
                    <SectionCard icon="🗺️" title="Market Intelligence"
                      badge="Phase 5" badgeColor="border-teal-700/40 bg-teal-900/20 text-teal-400">
                      <MarketSection data={result.results.market as Record<string, unknown>} />
                    </SectionCard>
                  )}
                  {Boolean(result.results.scheme) && (
                    <SectionCard icon="🏛️" title="Government Support"
                      badge="Phase 6" badgeColor="border-indigo-700/40 bg-indigo-900/20 text-indigo-400">
                      <SchemeSection data={result.results.scheme as Record<string, unknown>} />
                    </SectionCard>
                  )}
                </div>
              )}

              {/* Errors (if any) */}
              {result.errors.length > 0 && (
                <div className="text-xs text-amber-600/70 bg-amber-900/10 border border-amber-700/20 rounded-lg px-4 py-3">
                  <p className="font-semibold mb-1">ℹ️ Some analyses had partial results:</p>
                  <ul className="space-y-0.5">
                    {result.errors.slice(0, 3).map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {!loading && !result && !error && (
            <div className="card p-10 text-center text-gray-500">
              <div className="text-5xl mb-4">🤖</div>
              <p className="text-lg font-semibold text-gray-400 mb-2">Ask RuralBiz AI</p>
              <p className="text-sm max-w-md mx-auto">
                Type your question above or click a suggested question to get a personalized
                business, financial, market, and government support advisory.
              </p>
              {aiStatus === 'unavailable' && (
                <div className="mt-4 text-xs text-amber-600/70 bg-amber-900/10 border border-amber-700/20 rounded-lg px-4 py-3 max-w-sm mx-auto">
                  <strong>AI Status:</strong> No API key configured. System will provide structured data analysis without AI narrative.
                  To enable AI: add your GEMINI_API_KEY to the backend .env file.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── History Tab ── */}
      {activeTab === 'history' && (
        <HistoryPanel
          items={history}
          onReask={q => { setQuestion(q); setActiveTab('advisor') }}
        />
      )}
    </div>
  )
}
