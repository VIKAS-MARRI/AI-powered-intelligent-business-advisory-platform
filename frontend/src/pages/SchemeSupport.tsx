/**
 * SchemeSupport — Phase 6 Government Scheme & Financial Support Intelligence.
 *
 * Sections:
 *  1. Business + Financial Configurator
 *  2. Funding Gap Summary
 *  3. Ranked Scheme Matches (with score, eligibility, tags)
 *  4. Scheme Detail Modal (full eligibility, docs, steps, official link)
 *  5. Scheme Comparison (select 2–4, side-by-side table)
 *  6. Browse All Schemes (with category/sector filters)
 *  7. Disclaimer
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { businessService } from '../services/businessService'
import { schemeService } from '../services/schemeService'
import { inrShort } from '../utils/format'

import type { BusinessPublic } from '../types/business'
import type {
  SchemeMatchOut,
  MatchResultOut,
  SchemeOut,
  SchemeSummaryOut,
  FundingGapOut,
} from '../types/scheme'

// ── Constants ─────────────────────────────────────────────────────────────────

const DISCLAIMER = `Scheme recommendations are generated based on available profile, business, financial, and scheme
information. Eligibility, benefits, funding amounts, and application requirements may change.
Always verify the latest requirements through official government sources before applying.
RuralBiz AI does not guarantee eligibility, approval, loans, subsidies, or financial assistance.`

const ELIGIBILITY_CONFIG: Record<string, { cls: string; dot: string }> = {
  '🟢 Likely Eligible':                         { cls: 'text-emerald-300 bg-emerald-900/30 border-emerald-700/40', dot: 'bg-emerald-400' },
  '🟡 Possible Eligibility — Verify Requirements': { cls: 'text-amber-300  bg-amber-900/30  border-amber-700/40',   dot: 'bg-amber-400'   },
  '🔴 Likely Not Eligible':                      { cls: 'text-red-300    bg-red-900/30    border-red-700/40',     dot: 'bg-red-400'     },
  '⚪ More Information Required':                { cls: 'text-slate-300  bg-slate-800/50  border-slate-600/40',   dot: 'bg-slate-400'   },
}

// ── Small shared components ────────────────────────────────────────────────────

function EligibilityBadge({ status }: { status: string }) {
  const cfg = ELIGIBILITY_CONFIG[status] ?? ELIGIBILITY_CONFIG['⚪ More Information Required']
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-semibold ${cfg.cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {status.replace(/^[^\s]+\s/, '')}
    </span>
  )
}

function DataStatusBadge({ status }: { status: string }) {
  return status === 'verified' ? (
    <span className="text-[10px] px-1.5 py-0.5 rounded border border-emerald-700/40 bg-emerald-900/30 text-emerald-400 font-semibold">
      ✓ Verified
    </span>
  ) : (
    <span className="text-[10px] px-1.5 py-0.5 rounded border border-amber-700/30 bg-amber-900/20 text-amber-500 font-semibold">
      Demo Data
    </span>
  )
}

function FundingTag({ type }: { type: string }) {
  const cfg: Record<string, string> = {
    Loan:    'border-blue-700/40 bg-blue-900/30 text-blue-300',
    Subsidy: 'border-violet-700/40 bg-violet-900/30 text-violet-300',
    Both:    'border-teal-700/40 bg-teal-900/30 text-teal-300',
    Support: 'border-slate-700/40 bg-slate-800/30 text-slate-400',
  }
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${cfg[type] ?? cfg.Support}`}>
      {type}
    </span>
  )
}

// ScoreBar is exported for potential re-use in future phases
export function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="text-xs text-gray-500 w-40 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-surface-700/50 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(100, value / 0.35 * 100)}%`, background: color }} />
      </div>
      <span className="text-xs text-white font-semibold w-8 text-right shrink-0">{value.toFixed(1)}</span>
    </div>
  )
}

// ── Funding Gap Card ──────────────────────────────────────────────────────────

function FundingGapCard({ gap }: { gap: FundingGapOut }) {
  return (
    <div className="card p-5 bg-gradient-to-br from-slate-800/60 to-transparent">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">💰 Funding Gap Analysis</h3>
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Estimated Investment</p>
          <p className="text-lg font-bold text-white">{inrShort(gap.estimated_investment)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Available Capital</p>
          <p className="text-lg font-bold text-emerald-400">{inrShort(gap.available_capital)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Funding Gap</p>
          <p className={`text-lg font-bold ${gap.has_gap ? 'text-amber-400' : 'text-emerald-400'}`}>
            {gap.has_gap ? inrShort(gap.funding_gap) : '—'}
          </p>
        </div>
      </div>
      {gap.has_gap && (
        <div className="bg-surface-700/40 rounded-lg px-3 py-2">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-gray-500">Gap coverage needed</span>
            <span className="text-xs font-bold text-amber-300">{gap.gap_percentage}%</span>
          </div>
          <div className="h-1.5 bg-surface-600/50 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full transition-all duration-700"
              style={{ width: `${Math.min(100, gap.gap_percentage)}%` }} />
          </div>
        </div>
      )}
      <p className="text-xs text-gray-500 mt-3 italic">{gap.gap_label}</p>
    </div>
  )
}

// ── Scheme Match Card ─────────────────────────────────────────────────────────

function SchemeCard({
  match, rank, isBest, isSelected, onSelect, onViewDetails,
}: {
  match:          SchemeMatchOut
  rank:           number
  isBest:         boolean
  isSelected:     boolean
  onSelect:       (id: string) => void
  onViewDetails:  (id: string) => void
}) {
  const rankIcon = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`
  return (
    <div className={`card p-5 transition-all duration-200 ${isSelected ? 'ring-2 ring-primary-500/50' : ''} ${isBest ? 'border-primary-700/50' : ''}`}>
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <span className="text-lg shrink-0">{rankIcon}</span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-white leading-snug">{match.scheme_name}</h3>
            <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
              <EligibilityBadge status={match.eligibility.status} />
              <FundingTag type={match.funding_relevance} />
              <DataStatusBadge status={match.data_status} />
              {match.tags.map(t => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded border border-slate-600/40 text-slate-400">{t}</span>
              ))}
            </div>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold text-white leading-none">{Math.round(match.score_breakdown.total)}</div>
          <div className="text-[10px] text-gray-600">/ 100</div>
        </div>
      </div>

      {/* Key benefit */}
      <p className="text-xs text-gray-400 mb-3 line-clamp-2">{match.key_benefit}</p>

      {/* Score bar (total) */}
      <div className="h-1 bg-surface-700/60 rounded-full mb-3">
        <div className="h-full rounded-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-700"
          style={{ width: `${match.score_breakdown.total}%` }} />
      </div>

      {/* Match reasons */}
      {match.match_reasons.length > 0 && (
        <ul className="space-y-0.5 mb-3">
          {match.match_reasons.slice(0, 3).map((r, i) => (
            <li key={i} className="text-xs text-gray-400">{r}</li>
          ))}
        </ul>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-3 pt-3 border-t border-surface-700/20">
        <button
          id={`scheme-detail-${match.scheme_id}`}
          onClick={() => onViewDetails(match.scheme_id)}
          className="flex-1 text-xs py-1.5 rounded-lg border border-surface-600/50 text-gray-300 hover:text-white hover:border-primary-500/50 transition-all"
        >
          View Details
        </button>
        <button
          id={`scheme-compare-${match.scheme_id}`}
          onClick={() => onSelect(match.scheme_id)}
          className={`flex-1 text-xs py-1.5 rounded-lg border transition-all ${
            isSelected
              ? 'border-primary-500/70 bg-primary-900/30 text-primary-300'
              : 'border-surface-600/50 text-gray-500 hover:text-gray-300'
          }`}
        >
          {isSelected ? '✓ In Compare' : '+ Compare'}
        </button>
      </div>
    </div>
  )
}

// ── Scheme Detail Modal ───────────────────────────────────────────────────────

function SchemeDetailModal({ schemeId, onClose }: { schemeId: string; onClose: () => void }) {
  const [scheme, setScheme] = useState<SchemeOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    schemeService.get(schemeId)
      .then(setScheme)
      .catch(() => setScheme(null))
      .finally(() => setLoading(false))
  }, [schemeId])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative bg-surface-900 border border-surface-700/50 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-6 h-6 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
          </div>
        ) : !scheme ? (
          <div className="p-8 text-center text-gray-500">Failed to load scheme details.</div>
        ) : (
          <div className="p-6 space-y-5">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white leading-snug">{scheme.name}</h2>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <DataStatusBadge status={scheme.data_status} />
                  <span className="text-xs px-2 py-0.5 rounded border border-surface-600/40 text-gray-400">{scheme.category}</span>
                  <span className="text-xs px-2 py-0.5 rounded border border-surface-600/40 text-gray-400">{scheme.sector}</span>
                  <span className="text-xs px-2 py-0.5 rounded border border-surface-600/40 text-gray-400">{scheme.location_scope}</span>
                </div>
              </div>
              <button aria-label="Close details" onClick={onClose} className="text-gray-500 hover:text-white text-xl shrink-0">✕</button>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-300">{scheme.full_description || scheme.short_description}</p>

            {/* Financial support */}
            {(scheme.maximum_loan_amount || scheme.maximum_subsidy_amount || scheme.subsidy_percentage) && (
              <div className="bg-surface-800/50 rounded-xl p-4">
                <h4 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wide">💰 Financial Support</h4>
                <div className="grid grid-cols-3 gap-3 text-center">
                  {scheme.maximum_loan_amount && (
                    <div>
                      <p className="text-xs text-gray-500">Max Loan</p>
                      <p className="text-sm font-bold text-blue-300">{inrShort(scheme.maximum_loan_amount)}</p>
                    </div>
                  )}
                  {scheme.maximum_subsidy_amount && (
                    <div>
                      <p className="text-xs text-gray-500">Max Subsidy</p>
                      <p className="text-sm font-bold text-violet-300">{inrShort(scheme.maximum_subsidy_amount)}</p>
                    </div>
                  )}
                  {scheme.subsidy_percentage && (
                    <div>
                      <p className="text-xs text-gray-500">Subsidy %</p>
                      <p className="text-sm font-bold text-teal-300">{scheme.subsidy_percentage}%</p>
                    </div>
                  )}
                </div>
                {scheme.key_benefit && <p className="text-xs text-gray-400 mt-2 italic">{scheme.key_benefit}</p>}
              </div>
            )}

            {/* Who it helps */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">👥 Who It May Help</h4>
              <p className="text-sm text-gray-300">{scheme.target_beneficiaries}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {scheme.is_women_specific && <span className="text-xs px-2 py-0.5 rounded bg-pink-900/30 border border-pink-700/30 text-pink-300">👩 Women</span>}
                {scheme.is_sc_st_specific  && <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/30 border border-indigo-700/30 text-indigo-300">SC/ST</span>}
                {scheme.is_rural_specific  && <span className="text-xs px-2 py-0.5 rounded bg-green-900/30 border border-green-700/30 text-green-300">🌾 Rural</span>}
                {scheme.is_youth_specific  && <span className="text-xs px-2 py-0.5 rounded bg-amber-900/30 border border-amber-700/30 text-amber-300">Youth</span>}
              </div>
            </div>

            {/* Eligibility */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">📋 Eligibility Requirements</h4>
              <ul className="space-y-1.5">
                {scheme.eligibility_requirements.map((r, i) => (
                  <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-primary-500 mt-0.5 shrink-0">•</span>{r}
                  </li>
                ))}
              </ul>
            </div>

            {/* Documents */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">📄 Documents You May Need</h4>
              <ul className="space-y-1.5">
                {scheme.required_documents.map((d, i) => (
                  <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5 shrink-0">→</span>{d}
                  </li>
                ))}
              </ul>
            </div>

            {/* Application steps */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">📝 Application Steps</h4>
              <ol className="space-y-2">
                {scheme.application_steps.map((s, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs text-gray-300">
                    <span className="w-5 h-5 rounded-full bg-primary-900/50 border border-primary-700/40 text-primary-400 flex items-center justify-center shrink-0 text-[10px] font-bold">
                      {i + 1}
                    </span>
                    {s}
                  </li>
                ))}
              </ol>
            </div>

            {/* Official info */}
            <div className="bg-surface-800/40 rounded-xl p-4">
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">🔗 Official Source</h4>
              <p className="text-xs text-gray-400 mb-1">{scheme.official_source}</p>
              <p className="text-xs text-gray-600">Last reviewed: {scheme.last_reviewed}</p>
              <a
                href={scheme.official_url}
                target="_blank"
                rel="noopener noreferrer"
                id={`official-link-${scheme.id}`}
                className="mt-3 inline-flex items-center gap-1.5 text-xs text-primary-400 hover:text-primary-300 border border-primary-700/40 bg-primary-900/20 px-3 py-1.5 rounded-lg transition-colors"
              >
                View Official Information ↗
              </a>
            </div>

            {/* Disclaimer */}
            <div className="text-xs text-amber-700/80 bg-amber-900/10 border border-amber-800/20 rounded-lg px-4 py-3">
              ⚠️ <strong>Important:</strong> {DISCLAIMER.split('\n')[0]}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Compare Table ─────────────────────────────────────────────────────────────

function CompareTable({ matches, onRemove }: { matches: SchemeMatchOut[]; onRemove: (id: string) => void }) {
  if (matches.length === 0) return null

  const rows: { label: string; render: (m: SchemeMatchOut) => React.ReactNode }[] = [
    { label: 'Match Score',    render: m => <span className="text-xl font-bold text-white">{Math.round(m.score_breakdown.total)}<span className="text-xs text-gray-600">/100</span></span> },
    { label: 'Category',       render: m => m.category },
    { label: 'Sector',         render: m => m.sector },
    { label: 'Funding Type',   render: m => <FundingTag type={m.funding_relevance} /> },
    { label: 'Eligibility',    render: m => <EligibilityBadge status={m.eligibility.status} /> },
    { label: 'Data Status',    render: m => <DataStatusBadge status={m.data_status} /> },
    { label: 'Key Benefit',    render: m => <span className="text-xs text-gray-400">{m.key_benefit}</span> },
    { label: 'Business Rel.', render: m => `${m.score_breakdown.business_relevance.toFixed(1)}` },
    { label: 'Location',       render: m => `${m.score_breakdown.location_eligibility.toFixed(1)}` },
    { label: 'Official Info',  render: m => (
        <a href={m.official_url} target="_blank" rel="noopener noreferrer"
          className="text-xs text-primary-400 hover:text-primary-300">Visit ↗</a>
      )},
  ]

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-surface-700/30">
        <h3 className="text-sm font-semibold text-gray-300">⚖️ Scheme Comparison</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700/20">
              <th className="px-4 py-3 text-left text-xs text-gray-500 w-32">Feature</th>
              {matches.map(m => (
                <th key={m.scheme_id} className="px-4 py-3 text-left">
                  <div className="text-xs font-semibold text-white line-clamp-2 pr-2">{m.scheme_name}</div>
                  <button
                    onClick={() => onRemove(m.scheme_id)}
                    className="text-[10px] text-red-500 hover:text-red-400 mt-0.5"
                  >✕ Remove</button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr key={row.label} className="border-b border-surface-700/10 hover:bg-surface-700/10">
                <td className="px-4 py-2.5 text-xs text-gray-500 font-medium">{row.label}</td>
                {matches.map(m => (
                  <td key={m.scheme_id} className="px-4 py-2.5 text-xs text-gray-300">
                    {row.render(m)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function SchemeSupport() {
  const { user } = useAuth()
  const loc = useLocation()
  const params = new URLSearchParams(loc.search)
  const autoplay = params.get('autoplay') === '1'
  const { demoProfile } = useDemo()

  // ── State ─────────────────────────────────────────────────────────────────
  const [businesses, setBusinesses]       = useState<BusinessPublic[]>([])
  const [bizLoading, setBizLoading]       = useState(true)
  const [selectedBizId, setSelectedBizId] = useState('')

  const [estimatedInvestment, setEstimatedInvestment] = useState<string>('200000')
  const [availableCapital, setAvailableCapital]       = useState<string>('')
  const [state, setState]                             = useState<string>('')
  const [userAge, setUserAge]                         = useState<string>('')
  const [isWoman, setIsWoman]                         = useState<string>('unknown')
  const [isScSt, setIsScSt]                           = useState<string>('unknown')
  const [isRural, setIsRural]                         = useState<string>('unknown')

  const [matchResult, setMatchResult] = useState<MatchResultOut | null>(null)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState<string | null>(null)

  const [detailSchemeId, setDetailSchemeId]     = useState<string | null>(null)
  const [compareIds, setCompareIds]             = useState<string[]>([])
  const [compareMatches, setCompareMatches]     = useState<SchemeMatchOut[]>([])

  const [allSchemes, setAllSchemes]   = useState<SchemeSummaryOut[]>([])
  const [catFilter, setCatFilter]     = useState('All')
  const [browseLoading, setBrowseLoading] = useState(true)

  // ── Load businesses ────────────────────────────────────────────────────────
  useEffect(() => {
    businessService.recommend({ top_n: 10 })
      .then(r => {
        const list = r.recommendations.map(rec => rec.business)
        setBusinesses(list)
        if (list.length) {
          setSelectedBizId(prev => prev || list[0].id)
          const biz = list[0]
          const mid = ((biz.min_investment ?? 0) + (biz.max_investment ?? 0)) / 2
          if (mid) setEstimatedInvestment(Math.round(mid).toString())
        }
      })
      .catch(() =>
        businessService.list({ rural_only: false }).then(r => {
          const list = r.items.slice(0, 10)
          setBusinesses(list)
          if (list.length) setSelectedBizId(list[0].id)
        }).catch(() => {})
      )
      .finally(() => setBizLoading(false))
  }, [])

  // Prefill demo profile if active
  useEffect(() => {
    if (!demoProfile) return
    if (demoProfile.available_capital) setAvailableCapital(String(Math.round(demoProfile.available_capital)))
    if (!state && demoProfile.state) setState(demoProfile.state)
    if (demoProfile.available_capital && !estimatedInvestment) setEstimatedInvestment(String(Math.round(demoProfile.available_capital)))
    // ensure a business is selected
    if (businesses.length > 0) setSelectedBizId(prev => prev || businesses[0].id)
  }, [demoProfile, businesses])

  // Auto-run findSupport when autoplay requested
  useEffect(() => {
    if (!autoplay || !demoProfile) return
    const t = setTimeout(() => {
      if (selectedBizId && !matchResult && !loading) {
        void findSupport()
      }
    }, 700)
    return () => clearTimeout(t)
  }, [autoplay, demoProfile, selectedBizId, matchResult, loading])

  // Pre-fill state from profile
  useEffect(() => {
    if (user?.state && !state) setState(user.state)
    if (user?.available_capital && !availableCapital) setAvailableCapital(Math.round(user.available_capital).toString())
  }, [user])

  // ── Load all schemes for browse section ────────────────────────────────────
  useEffect(() => {
    schemeService.list()
      .then(r => setAllSchemes(r.items))
      .catch(() => {})
      .finally(() => setBrowseLoading(false))
  }, [])

  // ── Find support ───────────────────────────────────────────────────────────
  const findSupport = useCallback(async () => {
    if (!selectedBizId) { setError('Select a business.'); return }
    const inv = parseFloat(estimatedInvestment)
    const cap = parseFloat(availableCapital || '0')
    if (!inv || inv <= 0) { setError('Enter a valid estimated investment amount.'); return }
    setError(null)
    setLoading(true)
    try {
      const res = await schemeService.match({
        business_id:          selectedBizId,
        estimated_investment: inv,
        available_capital:    cap,
        state:                state || undefined,
        user_age:             userAge ? parseInt(userAge) : undefined,
        is_woman:             isWoman === 'yes' ? true : isWoman === 'no' ? false : undefined,
        is_sc_st:             isScSt  === 'yes' ? true : isScSt  === 'no' ? false : undefined,
        is_rural:             isRural === 'yes' ? true : isRural === 'no' ? false : undefined,
      })
      setMatchResult(res)
      setCompareIds([])
      setCompareMatches([])
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Failed to find matching schemes. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [selectedBizId, estimatedInvestment, availableCapital, state, userAge, isWoman, isScSt, isRural])

  // ── Compare ────────────────────────────────────────────────────────────────
  const toggleCompare = useCallback((id: string) => {
    setCompareIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev)
  }, [])

  const runCompare = useCallback(async () => {
    if (compareIds.length < 2) return
    let _loading = true
    try {
      const inv = parseFloat(estimatedInvestment) || undefined
      const cap = parseFloat(availableCapital || '0') || undefined
      const res = await schemeService.compare({
        scheme_ids:            compareIds,
        business_id:           selectedBizId || undefined,
        estimated_investment:  inv,
        available_capital:     cap,
        state:                 state || undefined,
      })
      setCompareMatches(res)
    } catch {
      setCompareMatches([])
    } finally {
      _loading = false
      void _loading // suppress lint
    }
  }, [compareIds, selectedBizId, estimatedInvestment, availableCapital, state])

  useEffect(() => {
    if (compareIds.length >= 2) runCompare()
    else setCompareMatches([])
  }, [compareIds])

  // ── Derived ────────────────────────────────────────────────────────────────
  const categories = useMemo(() => ['All', ...Array.from(new Set(allSchemes.map(s => s.category))).sort()], [allSchemes])
  const filteredBrowse = useMemo(() =>
    catFilter === 'All' ? allSchemes : allSchemes.filter(s => s.category === catFilter),
    [allSchemes, catFilter]
  )

  // selectedBiz available for future use (e.g. displaying min/max investment)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            🏛️ <span className="text-gradient">Government Scheme Support</span>
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Discover government schemes, subsidies, and loans that may support your business journey.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {demoProfile && <div className="text-xs text-amber-300 font-semibold">Demo Data</div>}
          <DemoProgress />
          <Link to="/market-intelligence" className="btn-outline text-sm px-4 py-2">🗺️ Market Intelligence</Link>
        </div>
      </div>

      {/* ── Configurator ── */}
      <div className="card p-6 space-y-5">
        <h2 className="text-lg font-display font-bold text-white">Configure Your Profile</h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Business */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Business</label>
            {bizLoading ? (
              <div className="flex items-center gap-2 h-10 text-xs text-gray-600">
                <div className="w-3.5 h-3.5 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" /> Loading…
              </div>
            ) : (
              <select id="scheme-biz-select" value={selectedBizId} onChange={e => setSelectedBizId(e.target.value)}
                className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none">
                <option value="">— Select —</option>
                {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            )}
          </div>

          {/* Estimated investment */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Estimated Investment (₹)</label>
            <input id="scheme-investment" type="number" value={estimatedInvestment}
              onChange={e => setEstimatedInvestment(e.target.value)} placeholder="e.g. 200000"
              className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600" />
          </div>

          {/* Available capital */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Available Capital (₹)</label>
            <input id="scheme-capital" type="number" value={availableCapital}
              onChange={e => setAvailableCapital(e.target.value)} placeholder="e.g. 120000"
              className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600" />
          </div>

          {/* State */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">State</label>
            <input id="scheme-state" type="text" value={state}
              onChange={e => setState(e.target.value)} placeholder="e.g. Telangana"
              className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600" />
          </div>

          {/* Age */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Age <span className="text-gray-600">(optional)</span></label>
            <input id="scheme-age" type="number" value={userAge}
              onChange={e => setUserAge(e.target.value)} placeholder="e.g. 28"
              className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600" />
          </div>

          {/* Profile flags */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-400">Profile <span className="text-gray-600">(optional — improves matching)</span></label>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Woman', state: isWoman, setter: setIsWoman },
                { label: 'SC/ST', state: isScSt,  setter: setIsScSt  },
                { label: 'Rural', state: isRural, setter: setIsRural },
              ].map(({ label, state: s, setter }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <span className="text-xs text-gray-500">{label}:</span>
                  {(['yes', 'no', 'unknown'] as const).map(v => (
                    <button key={v} onClick={() => setter(v)}
                      className={`text-xs px-2 py-0.5 rounded border transition-all ${
                        s === v ? 'border-primary-500/70 bg-primary-900/30 text-white' : 'border-surface-700/40 text-gray-600 hover:text-gray-400'
                      }`}>
                      {v === 'unknown' ? '?' : v === 'yes' ? '✓' : '✗'}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5">{error}</div>
        )}

        <button id="find-support-btn" onClick={findSupport}
          disabled={loading || !selectedBizId}
          className="btn-primary px-8 py-2.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? (
            <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Finding Schemes…</>
          ) : '🏛️ Find Support Schemes'}
        </button>
      </div>

      {/* ── Results ── */}
      {matchResult && (
        <>
          {/* Funding gap */}
          <FundingGapCard gap={matchResult.funding_gap} />

          {/* Best picks */}
          {(matchResult.best_overall || matchResult.best_loan || matchResult.best_subsidy) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: '🥇 Best Overall', id: matchResult.best_overall },
                { label: '🏦 Best Loan',    id: matchResult.best_loan    },
                { label: '💸 Best Subsidy', id: matchResult.best_subsidy },
                { label: '🌾 Best Rural',   id: matchResult.best_rural   },
              ].map(({ label, id }) => {
                const m = matchResult.matches.find(x => x.scheme_id === id)
                if (!m) return null
                return (
                  <div key={label} className="card p-3 text-center">
                    <p className="text-[10px] text-gray-500 mb-1">{label}</p>
                    <p className="text-xs text-white font-semibold line-clamp-2 leading-snug">{m.scheme_name}</p>
                    <p className="text-lg font-bold text-primary-400 mt-1">{Math.round(m.score_breakdown.total)}<span className="text-xs text-gray-600">/100</span></p>
                  </div>
                )
              })}
            </div>
          )}

          {/* Compare instructions */}
          {matchResult.matches.length >= 2 && (
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span>💡 Select 2–4 schemes to compare side-by-side.</span>
              {compareIds.length >= 2 && (
                <span className="text-primary-400 font-medium">{compareIds.length} selected → scroll down to compare</span>
              )}
            </div>
          )}

          {/* Scheme cards grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {matchResult.matches.map((m, i) => (
              <SchemeCard
                key={m.scheme_id}
                match={m}
                rank={i + 1}
                isBest={m.scheme_id === matchResult.best_overall}
                isSelected={compareIds.includes(m.scheme_id)}
                onSelect={toggleCompare}
                onViewDetails={setDetailSchemeId}
              />
            ))}
          </div>

          {/* Compare table */}
          {compareMatches.length >= 2 && (
            <CompareTable
              matches={compareMatches}
              onRemove={id => setCompareIds(prev => prev.filter(x => x !== id))}
            />
          )}

          {/* Disclaimer */}
          <div className="rounded-xl bg-amber-900/10 border border-amber-700/20 px-5 py-4">
            <p className="text-xs text-amber-600/80">
              ⚠️ <strong>Disclaimer:</strong> {DISCLAIMER.trim().replace(/\n/g, ' ')}
            </p>
          </div>
        </>
      )}

      {/* ── Empty state ── */}
      {!matchResult && !loading && (
        <div className="card p-10 text-center text-gray-500">
          <div className="text-5xl mb-4">🏛️</div>
          <p className="text-lg font-semibold text-gray-400 mb-2">Discover Government Support</p>
          <p className="text-sm max-w-md mx-auto">
            Select your business, enter investment details, and click <strong className="text-white">Find Support Schemes</strong> to see matched government programs.
          </p>
        </div>
      )}

      {/* ── Browse All Schemes ── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-bold text-white">📚 Browse All Schemes</h2>
          <div className="flex gap-1.5 flex-wrap">
            {categories.slice(0, 7).map(cat => (
              <button key={cat} onClick={() => setCatFilter(cat)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                  catFilter === cat
                    ? 'border-primary-500/70 bg-primary-900/30 text-primary-300'
                    : 'border-surface-700/40 text-gray-500 hover:text-white hover:border-surface-600'
                }`}>
                {cat}
              </button>
            ))}
          </div>
        </div>

        {browseLoading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1,2,3].map(i => (
              <div key={i} className="card p-5 animate-pulse">
                <div className="h-3 bg-surface-700/50 rounded w-3/4 mb-3" />
                <div className="h-2 bg-surface-700/30 rounded w-full mb-2" />
                <div className="h-2 bg-surface-700/30 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredBrowse.map(s => (
              <div key={s.id} className="card p-4 hover:border-surface-600/50 transition-colors">
                <div className="flex items-start justify-between mb-2 gap-2">
                  <h3 className="text-sm font-semibold text-white leading-snug line-clamp-2 flex-1">{s.name}</h3>
                  <DataStatusBadge status={s.data_status} />
                </div>
                <p className="text-xs text-gray-400 mb-3 line-clamp-2">{s.short_description}</p>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  <span className="text-[10px] px-2 py-0.5 rounded border border-surface-600/40 text-gray-500">{s.category}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded border border-surface-600/40 text-gray-500">{s.sector}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded border border-surface-600/40 text-gray-500">{s.location_scope}</span>
                </div>
                {s.key_benefit && <p className="text-xs text-primary-400 mb-3 line-clamp-1">{s.key_benefit}</p>}
                <button
                  id={`browse-detail-${s.id}`}
                  onClick={() => setDetailSchemeId(s.id)}
                  className="text-xs text-gray-500 hover:text-white border border-surface-700/30 hover:border-surface-600 px-3 py-1 rounded-lg transition-colors"
                >
                  View Details →
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Scheme Detail Modal ── */}
      {detailSchemeId && (
        <SchemeDetailModal schemeId={detailSchemeId} onClose={() => setDetailSchemeId(null)} />
      )}
    </div>
  )
}
