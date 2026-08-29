/**
 * Phase 8 — Personalized Recommendations Page.
 *
 * Replaces the Phase 2 basic recommendations page with:
 *  - Profile Intelligence Summary
 *  - Natural Language Search
 *  - Semantic skill match display
 *  - 10-factor score breakdown
 *  - Explainable AI reasons
 *  - Save/Explore/Analyze actions
 *  - Interaction tracking
 *  - Data Mode / AI Mode badge
 */
import { useState, useEffect, useCallback } from 'react'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { phase8Service } from '../services/phase8Service'
import type {
  PersonalizedRecommendationItem,
  PersonalizedRecommendationResponse,
  NaturalQueryResponse,
} from '../types/phase8'

// ── Constants ─────────────────────────────────────────────────────────────────

const RISK_COLORS: Record<string, string> = {
  Low:    'text-emerald-400 bg-emerald-900/20 border-emerald-700/30',
  Medium: 'text-amber-400   bg-amber-900/20   border-amber-700/30',
  High:   'text-red-400    bg-red-900/20     border-red-700/30',
}

const BREAKDOWN_LABELS: Record<string, { label: string; color: string }> = {
  semantic_skill:       { label: 'Skill Match',        color: 'bg-violet-500' },
  budget:               { label: 'Budget Fit',          color: 'bg-emerald-500' },
  market_opportunity:   { label: 'Market Opportunity',  color: 'bg-teal-500' },
  financial_potential:  { label: 'Financial Potential', color: 'bg-cyan-500' },
  experience:           { label: 'Experience',          color: 'bg-blue-500' },
  gov_support:          { label: 'Gov. Support',        color: 'bg-indigo-500' },
  risk:                 { label: 'Risk Compatibility',  color: 'bg-amber-500' },
  interest:             { label: 'Interest Match',      color: 'bg-orange-500' },
  income_goal:          { label: 'Income Goal',         color: 'bg-pink-500' },
  location:             { label: 'Location Fit',        color: 'bg-rose-500' },
}

const WEIGHT_LABELS: Record<string, string> = {
  semantic_skill:       '20%',
  budget:               '15%',
  market_opportunity:   '15%',
  financial_potential:  '10%',
  experience:           '10%',
  gov_support:          '10%',
  risk:                 '8%',
  interest:             '5%',
  income_goal:          '4%',
  location:             '3%',
}

// ── Small utility components ──────────────────────────────────────────────────

function ScoreRing({ score, size = 56 }: { score: number; size?: number }) {
  const r     = size * 0.35
  const c     = 2 * Math.PI * r
  const off   = c - (score / 100) * c
  const color = score >= 75 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444'
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={4} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={4}
          strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-bold text-white">{Math.round(score)}</span>
      </div>
    </div>
  )
}


// ── Recommendation Card ───────────────────────────────────────────────────────

function RecommendationCard({
  item, onSave, onUnsave, onInteraction,
}: {
  item:          PersonalizedRecommendationItem
  onSave:        (id: string) => void
  onUnsave:      (id: string) => void
  onInteraction: (id: string, type: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [saving,   setSaving]   = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      if (item.is_saved) onUnsave(item.business_id)
      else onSave(item.business_id)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      id={`rec-card-${item.rank}`}
      className="card overflow-hidden border hover:border-surface-600/50 transition-all duration-200"
      onClick={() => onInteraction(item.business_id, 'viewed')}
    >
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Score ring */}
          <ScoreRing score={item.final_score} size={60} />

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] text-gray-500 font-medium">#{item.rank}</span>
                  <h3 className="text-base font-display font-bold text-white">{item.business_name}</h3>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 mt-1">
                  <span className="text-[10px] text-gray-500">{item.category}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${RISK_COLORS[item.risk_level] ?? ''}`}>
                    {item.risk_level} Risk
                  </span>
                  {item.suitable_for_rural && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded border border-emerald-700/30 bg-emerald-900/10 text-emerald-500">
                      Rural ✓
                    </span>
                  )}
                </div>
              </div>
              <button
                id={`save-btn-${item.business_id}`}
                onClick={e => { e.stopPropagation(); handleSave() }}
                disabled={saving}
                className={`shrink-0 text-xs px-2.5 py-1.5 rounded-lg border transition-all ${
                  item.is_saved
                    ? 'border-amber-600/40 bg-amber-900/20 text-amber-400'
                    : 'border-surface-600/40 text-gray-500 hover:border-amber-600/40 hover:text-amber-400'
                }`}
              >
                {item.is_saved ? '★ Saved' : '☆ Save'}
              </button>
            </div>

            {/* Semantic match highlight */}
            {item.semantic_detail.semantic_score > 0 && (
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1 bg-surface-700/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-violet-500 rounded-full"
                    style={{ width: `${item.semantic_detail.semantic_score}%` }}
                  />
                </div>
                <span className="text-[10px] text-violet-400">
                  🧠 {Math.round(item.semantic_detail.semantic_score)}% Skill Match
                </span>
              </div>
            )}

            {/* Concept tags */}
            {item.semantic_detail.matched_concepts.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {item.semantic_detail.matched_concepts.slice(0, 4).map(c => (
                  <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-violet-900/20 text-violet-400 border border-violet-700/20">
                    {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-3 gap-2 mt-4">
          <div className="bg-surface-700/30 rounded-lg p-2 text-center">
            <p className="text-[10px] text-gray-500">Investment</p>
            <p className="text-xs font-bold text-white">
              ₹{(item.min_investment / 1000).toFixed(0)}k–₹{(item.max_investment / 1000).toFixed(0)}k
            </p>
          </div>
          <div className="bg-surface-700/30 rounded-lg p-2 text-center">
            <p className="text-[10px] text-gray-500">Monthly Profit</p>
            <p className="text-xs font-bold text-emerald-400">
              ₹{(item.monthly_profit_min / 1000).toFixed(0)}k–₹{(item.monthly_profit_max / 1000).toFixed(0)}k
            </p>
          </div>
          <div className="bg-surface-700/30 rounded-lg p-2 text-center">
            <p className="text-[10px] text-gray-500">Setup</p>
            <p className="text-xs font-bold text-white">
              {item.setup_time_weeks_min}–{item.setup_time_weeks_max}w
            </p>
          </div>
        </div>

        {/* Why recommended — top 3 */}
        <div className="mt-3 space-y-1">
          {item.explanation.why_recommended.slice(0, 3).map((r, i) => (
            <p key={i} className="text-[11px] text-gray-400 flex items-start gap-1.5">
              <span className="shrink-0 mt-0.5">
                {r.startsWith('✓') ? '✓' : r.startsWith('⚠') ? '⚠' : '•'}
              </span>
              {r.replace(/^[✓⚠•]\s*/, '')}
            </p>
          ))}
        </div>

        {/* Toggle buttons */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            onClick={e => { e.stopPropagation(); setExpanded(o => !o) }}
            className="text-xs text-gray-500 hover:text-white border border-surface-700/40 px-3 py-1.5 rounded-lg hover:border-surface-600 transition-colors"
          >
            {expanded ? '▲ Less' : '▾ Score Breakdown'}
          </button>
          <Link
            to={`/financial-analysis?business_id=${item.business_id}`}
            onClick={() => onInteraction(item.business_id, 'explored')}
            className="text-xs text-emerald-500 hover:text-emerald-400 border border-emerald-700/30 px-3 py-1.5 rounded-lg hover:border-emerald-600 transition-colors"
          >
            💰 Analyze Finance
          </Link>
          <Link
            to={`/advisor?q=${encodeURIComponent(item.business_name)}`}
            onClick={() => onInteraction(item.business_id, 'explored')}
            className="text-xs text-primary-400 hover:text-primary-300 border border-primary-700/30 px-3 py-1.5 rounded-lg hover:border-primary-600 transition-colors"
          >
            🤖 Ask AI Advisor
          </Link>
          <Link
            to="/scheme-support"
            className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-700/30 px-3 py-1.5 rounded-lg hover:border-indigo-600 transition-colors"
          >
            🏛️ Find Schemes
          </Link>
        </div>
      </div>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="px-5 pb-5 border-t border-surface-700/20 pt-4 space-y-4">
          {/* Score breakdown bars */}
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Score Breakdown (weighted contributions)
            </p>
            <div className="space-y-2">
              {Object.entries(item.breakdown).filter(([k]) => k !== 'preference_modifier').map(([key, val]) => {
                const cfg = BREAKDOWN_LABELS[key]
                if (!cfg) return null
                const rawVal = (item.raw_scores as unknown as Record<string, number>)[key] ?? 0
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-500 w-[140px] shrink-0">{cfg.label} ({WEIGHT_LABELS[key]})</span>
                    <div className="flex-1 h-1.5 bg-surface-700/50 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${cfg.color}`}
                        style={{ width: `${rawVal}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 w-8 text-right">{rawVal.toFixed(0)}</span>
                    <span className="text-[10px] text-gray-600 w-10 text-right">(+{(val as number).toFixed(1)})</span>
                  </div>
                )
              })}
              {item.breakdown.preference_modifier !== 0 && (
                <p className="text-[10px] text-amber-500 mt-1">
                  📈 Preference adjustment: {item.breakdown.preference_modifier > 0 ? '+' : ''}{item.breakdown.preference_modifier.toFixed(1)} pts
                </p>
              )}
            </div>
          </div>

          {/* Semantic explanation */}
          <div>
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Skill Match Analysis</p>
            <p className="text-[11px] text-gray-400">{item.semantic_detail.explanation}</p>
            {item.semantic_detail.method && (
              <p className="text-[10px] text-gray-600 mt-1">Method: {item.semantic_detail.method}</p>
            )}
          </div>

          {/* Challenges */}
          {item.explanation.challenges.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-amber-500/80 uppercase tracking-wider mb-2">⚠ Challenges</p>
              <ul className="space-y-1">
                {item.explanation.challenges.map((c, i) => (
                  <li key={i} className="text-[11px] text-gray-400 flex items-start gap-1.5">
                    <span className="text-amber-500 shrink-0">•</span>{c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Next steps */}
          {item.explanation.next_steps.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-primary-400/80 uppercase tracking-wider mb-2">📋 Next Steps</p>
              <ol className="space-y-1">
                {item.explanation.next_steps.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-[11px] text-gray-300">
                    <span className="w-4 h-4 rounded-full bg-primary-900/50 text-primary-400 flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    {s}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-[10px] text-gray-600 italic">{item.disclaimer}</p>
        </div>
      )}
    </div>
  )
}

// ── Profile Summary Panel ────────────────────────────────────────────────────

function ProfileSummary({ user }: { user: { full_name?: string; skills?: string; available_capital?: number; monthly_income_goal?: number; state?: string; business_interests?: string; experience_years?: number } }) {
  return (
    <div className="card p-4">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
        👤 Your Profile Intelligence
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {[
          { label: 'Capital', value: user.available_capital ? `₹${(user.available_capital / 1000).toFixed(0)}k` : '—' },
          { label: 'State',  value: user.state || '—' },
          { label: 'Experience', value: user.experience_years ? `${user.experience_years} yrs` : '—' },
          { label: 'Income Goal', value: user.monthly_income_goal ? `₹${(user.monthly_income_goal / 1000).toFixed(0)}k/mo` : '—' },
          { label: 'Skills',     value: user.skills ? user.skills.split(',').slice(0, 2).join(', ') + (user.skills.split(',').length > 2 ? '…' : '') : 'Not set' },
          { label: 'Interests',  value: user.business_interests ? user.business_interests.slice(0, 30) + (user.business_interests.length > 30 ? '…' : '') : 'Not set' },
        ].map(item => (
          <div key={item.label} className="bg-surface-700/30 rounded-lg px-3 py-2">
            <p className="text-[10px] text-gray-500">{item.label}</p>
            <p className="text-xs font-semibold text-white truncate">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Recommendations() {
  const { user } = useAuth()

  const [results,    setResults]    = useState<PersonalizedRecommendationItem[]>([])
  const [response,   setResponse]   = useState<PersonalizedRecommendationResponse | null>(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState<string | null>(null)

  const [query,      setQuery]      = useState('')
  const [nlLoading,  setNlLoading]  = useState(false)
  const [nlResult,   setNlResult]   = useState<NaturalQueryResponse | null>(null)
  const [activeMode, setActiveMode] = useState<'personalized' | 'natural'>('personalized')

  const [savedIds,   setSavedIds]   = useState<Set<string>>(new Set())
  const [topN,       setTopN]       = useState(8)

  // Load personalized recommendations
  const loadPersonalized = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // If demo profile is present, pass overrides to the backend (does not persist user data)
      const demoOverrides = demoProfile ? {
        top_n: topN,
        available_capital: demoProfile.available_capital,
        skills: demoProfile.skills,
        business_interests: demoProfile.business_interests,
        monthly_income_goal: demoProfile.monthly_income_goal,
      } : { top_n: topN }
      const res = await phase8Service.getPersonalized(demoOverrides)
      setResults(res.recommendations)
      setResponse(res)
      setSavedIds(new Set(res.recommendations.filter(r => r.is_saved).map(r => r.business_id)))
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Failed to load recommendations.')
    } finally {
      setLoading(false)
    }
  }, [topN])
  const { demoProfile } = useDemo()
  useEffect(() => { loadPersonalized() }, [loadPersonalized, demoProfile])

  // Natural query
  const handleNaturalQuery = async () => {
    if (!query.trim()) return
    setNlLoading(true)
    setError(null)
    try {
      const res = await phase8Service.naturalQuery(query, topN)
      setNlResult(res)
      setActiveMode('natural')
      setSavedIds(prev => {
        const next = new Set(prev)
        res.recommendations.filter(r => r.is_saved).forEach(r => next.add(r.business_id))
        return next
      })
    } catch {
      setError('Natural query failed. Try again.')
    } finally {
      setNlLoading(false)
    }
  }

  // Save / unsave
  const handleSave = async (id: string) => {
    try {
      await phase8Service.saveBusiness(id)
      setSavedIds(prev => new Set([...prev, id]))
      setResults(r => r.map(item => item.business_id === id ? { ...item, is_saved: true } : item))
      if (nlResult) {
        setNlResult(prev => prev ? {
          ...prev,
          recommendations: prev.recommendations.map(item =>
            item.business_id === id ? { ...item, is_saved: true } : item
          ),
        } : prev)
      }
    } catch { /* already saved */ }
  }

  const handleUnsave = async (id: string) => {
    try {
      await phase8Service.deleteSaved(id)
      setSavedIds(prev => { const s = new Set(prev); s.delete(id); return s })
      setResults(r => r.map(item => item.business_id === id ? { ...item, is_saved: false } : item))
    } catch {}
  }

  const handleInteraction = (id: string, type: string) => {
    phase8Service.recordInteraction(id, type).catch(() => {})
  }

  const displayItems = activeMode === 'natural' && nlResult
    ? nlResult.recommendations
    : results

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            🎯 <span className="text-gradient">Personalized Recommendations</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            AI-powered semantic matching across {response?.total_businesses_scored ?? '—'} rural businesses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] px-2 py-1 rounded border border-slate-700/40 bg-slate-800/30 text-slate-400">
            📊 Data Mode
          </span>
          <DemoProgress />
          <Link to="/saved-businesses" className="btn-outline text-xs px-3 py-1.5">
            ★ Saved
          </Link>
        </div>
      </div>

      {/* ── Profile Summary ── */}
      {user && <ProfileSummary user={user as unknown as Parameters<typeof ProfileSummary>[0]['user']} />}

      {/* ── Natural Language Search ── */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <input
              id="natural-query-input"
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleNaturalQuery()}
              placeholder='Try: "I know tailoring and have ₹2 lakh" or "Low risk food business in village"'
              className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
            />
          </div>
          <button
            id="natural-query-btn"
            onClick={handleNaturalQuery}
            disabled={nlLoading || !query.trim()}
            className="btn-primary px-5 py-3 flex items-center gap-2 disabled:opacity-50 shrink-0"
          >
            {nlLoading ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Searching…</>
            ) : '🔍 Search'}
          </button>
          {activeMode === 'natural' && (
            <button
              onClick={() => { setActiveMode('personalized'); setNlResult(null); setQuery('') }}
              className="text-sm text-gray-500 hover:text-white border border-surface-700/40 px-3 py-2 rounded-xl"
            >
              ✕ Clear
            </button>
          )}
        </div>

        {/* Extracted intent */}
        {activeMode === 'natural' && nlResult && (
          <div className="mt-3 text-xs text-gray-500 flex flex-wrap gap-2">
            <span className="font-semibold text-gray-400">Understood:</span>
            {nlResult.extracted_intent.budget && (
              <span className="px-2 py-0.5 rounded bg-surface-700/50 border border-surface-600/30">
                💰 ₹{(nlResult.extracted_intent.budget / 1000).toFixed(0)}k budget
              </span>
            )}
            {nlResult.extracted_intent.skills && (
              <span className="px-2 py-0.5 rounded bg-surface-700/50 border border-surface-600/30">
                🛠 {nlResult.extracted_intent.skills}
              </span>
            )}
            {nlResult.extracted_intent.risk_preference && (
              <span className="px-2 py-0.5 rounded bg-surface-700/50 border border-surface-600/30">
                ⚡ {nlResult.extracted_intent.risk_preference} risk
              </span>
            )}
            {nlResult.extracted_intent.location_type && (
              <span className="px-2 py-0.5 rounded bg-surface-700/50 border border-surface-600/30">
                📍 {nlResult.extracted_intent.location_type}
              </span>
            )}
            <span className="text-gray-600">via {nlResult.parse_method}</span>
          </div>
        )}
      </div>

      {/* ── Mode tabs ── */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 p-1 bg-surface-800/50 rounded-xl">
          {(['personalized', 'natural'] as const).map(mode => (
            <button
              key={mode}
              id={`tab-${mode}`}
              onClick={() => setActiveMode(mode)}
              className={`px-4 py-1.5 text-xs rounded-lg transition-all ${
                activeMode === mode
                  ? 'bg-surface-700 text-white font-semibold'
                  : 'text-gray-500 hover:text-white'
              }`}
            >
              {mode === 'personalized' ? '🎯 Personalized' : '🔍 Search Results'}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Show</label>
          <select
            value={topN}
            onChange={e => setTopN(Number(e.target.value))}
            className="bg-surface-700/50 border border-surface-600/40 text-white text-xs rounded-lg px-2 py-1"
          >
            {[5, 8, 10, 15].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Error state ── */}
      {error && (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* ── Loading ── */}
      {loading && (
        <div className="card p-10 text-center">
          <div className="w-10 h-10 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-400">Running semantic analysis across {response?.total_businesses_scored ?? '30+'} businesses…</p>
        </div>
      )}

      {/* ── Results ── */}
      {!loading && displayItems.length > 0 && (
        <div className="space-y-4">
          {displayItems.map(item => (
            <RecommendationCard
              key={item.business_id}
              item={{ ...item, is_saved: savedIds.has(item.business_id) }}
              onSave={handleSave}
              onUnsave={handleUnsave}
              onInteraction={handleInteraction}
            />
          ))}
          <p className="text-center text-xs text-gray-600 pb-4">
            ⚠️ Scores and financial figures are estimates for advisory purposes only.
          </p>
        </div>
      )}

      {/* ── Empty state ── */}
      {!loading && displayItems.length === 0 && !error && (
        <div className="card p-10 text-center text-gray-500">
          <div className="text-4xl mb-3">🎯</div>
          <p className="text-sm">
            {activeMode === 'natural'
              ? 'No results found. Try a different search query.'
              : 'Complete your profile to get personalized recommendations.'}
          </p>
          {activeMode === 'personalized' && (
            <Link to="/profile" className="mt-4 inline-block btn-primary text-sm px-4 py-2">
              Complete Profile →
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
