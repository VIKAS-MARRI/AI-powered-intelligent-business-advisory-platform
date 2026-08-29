/**
 * InvestmentOptimizer — Phase 4 Investment Optimization Engine page.
 *
 * Sections:
 *  1. Business Selector + Capital Input + Optional Constraints
 *  2. Insufficient Capital Warning (when applicable)
 *  3. Three-Strategy Comparison Table
 *  4. Capital Allocation Charts (per-strategy + side-by-side)
 *  5. Strategy Detail Cards (explanations + trade-offs)
 *  6. Financial Disclaimer
 *
 * Uses Google OR-Tools via the backend — no AI/LLM involved.
 */
import { useState, useEffect, useCallback } from 'react'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import { businessService } from '../services/businessService'
import { optimizerService } from '../services/optimizerService'
import type { BusinessPublic } from '../types/business'
import type { OptimizationResultOut, StrategyResultOut } from '../types/optimizer'
import { inr, inrShort, RISK_COLORS } from '../utils/format'

// ── Constants ─────────────────────────────────────────────────────────────────

const STRATEGY_META: Record<string, { icon: string; color: string; ring: string; badge: string; glow: string }> = {
  conservative: {
    icon: '🛡️',
    color: 'from-sky-900/30 to-sky-800/10 border-sky-700/40',
    ring: '#38bdf8',
    badge: 'bg-sky-900/40 text-sky-300 border-sky-700/40',
    glow: 'shadow-sky-900/20',
  },
  balanced: {
    icon: '⚖️',
    color: 'from-primary-900/30 to-primary-800/10 border-primary-700/40',
    ring: '#a78bfa',
    badge: 'bg-primary-900/40 text-primary-300 border-primary-700/40',
    glow: 'shadow-primary-900/20',
  },
  growth: {
    icon: '🚀',
    color: 'from-emerald-900/30 to-emerald-800/10 border-emerald-700/40',
    ring: '#34d399',
    badge: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/40',
    glow: 'shadow-emerald-900/20',
  },
}

const CATEGORY_COLORS: Record<string, string> = {
  'Equipment':          '#a78bfa',
  'Initial Inventory':  '#38bdf8',
  'Business Setup':     '#fb923c',
  'Licensing / Other':  '#facc15',
  'Marketing':          '#f472b6',
  'Working Capital':    '#4ade80',
  'Emergency Reserve':  '#f87171',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

// pct helper kept for potential future use
// function pct(v: number) { return `${v.toFixed(1)}%` }

function RiskBadge({ level }: { level: string }) {
  const dot = level === 'Low' ? 'bg-emerald-400' : level === 'Medium' ? 'bg-amber-400' : 'bg-red-400'
  const cls  = RISK_COLORS[level] ?? RISK_COLORS['Medium']
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {level}
    </span>
  )
}

// ── Score Arc ─────────────────────────────────────────────────────────────────

function ScoreArc({ score, color }: { score: number; color: string }) {
  const C = 2 * Math.PI * 28
  const offset = C - (score / 100) * C
  return (
    <div className="relative w-20 h-20">
      <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
        <circle cx="32" cy="32" r="28" fill="none" stroke="#1e293b" strokeWidth="5" />
        <circle
          cx="32" cy="32" r="28" fill="none"
          stroke={color} strokeWidth="5"
          strokeDasharray={C} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-white leading-none">{Math.round(score)}</span>
        <span className="text-[9px] text-gray-500">/ 100</span>
      </div>
    </div>
  )
}

// ── Allocation Bar Row ─────────────────────────────────────────────────────────

function AllocRow({ name, allocated, total }: { name: string; allocated: number; total: number }) {
  const pctVal = total > 0 ? (allocated / total) * 100 : 0
  const color  = CATEGORY_COLORS[name] ?? '#a78bfa'
  return (
    <div className="flex items-center gap-2 py-1.5">
      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: color }} />
      <span className="text-xs text-gray-400 w-32 shrink-0 truncate">{name}</span>
      <div className="flex-1 h-1.5 bg-surface-700/60 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pctVal}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold text-white w-16 text-right shrink-0">{inrShort(allocated)}</span>
      <span className="text-xs text-gray-600 w-8 text-right shrink-0">{pctVal.toFixed(0)}%</span>
    </div>
  )
}

// ── Strategy Card ──────────────────────────────────────────────────────────────

function StrategyCard({
  strategy, isRecommended, isSelected, onSelect,
}: {
  strategy: StrategyResultOut
  isRecommended: boolean
  isSelected: boolean
  onSelect: () => void
}) {
  const meta = STRATEGY_META[strategy.name]
  return (
    <div
      onClick={onSelect}
      className={`card p-5 bg-gradient-to-br ${meta.color} border cursor-pointer transition-all duration-200
        ${isSelected ? 'ring-2 ring-primary-500/70 scale-[1.01]' : 'hover:scale-[1.005]'}
      `}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">{meta.icon}</span>
          <span className="font-display font-bold text-white">{strategy.label}</span>
        </div>
        <div className="flex items-center gap-2">
          {isRecommended && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-900/40 text-amber-300 border border-amber-700/40">
              ★ Recommended
            </span>
          )}
          {isSelected && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-900/60 text-primary-300 border border-primary-700/40">
              Selected
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <ScoreArc score={strategy.optimization_score} color={meta.ring} />
        <div className="flex-1 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Total Allocated</span>
            <span className="font-semibold text-white">{inr(strategy.total_allocated)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Remaining</span>
            <span className="font-semibold text-emerald-400">{inr(strategy.remaining_capital)}</span>
          </div>
          <div className="flex justify-between text-xs items-center">
            <span className="text-gray-500">Risk Level</span>
            <RiskBadge level={strategy.risk_level} />
          </div>
        </div>
      </div>

      <div className="space-y-0.5">
        {strategy.allocations.map((a) => (
          <AllocRow key={a.name} name={a.name} allocated={a.allocated} total={strategy.total_allocated} />
        ))}
      </div>
    </div>
  )
}

// ── Comparison Table ───────────────────────────────────────────────────────────

function ComparisonTable({ strategies, recommended }: { strategies: StrategyResultOut[]; recommended: string }) {
  const cons = strategies.find(s => s.name === 'conservative')!
  const bal  = strategies.find(s => s.name === 'balanced')!
  const grow = strategies.find(s => s.name === 'growth')!

  const rows = [
    { label: 'Risk Level',         fmt: (s: StrategyResultOut) => s.risk_level },
    { label: 'Total Allocated',    fmt: (s: StrategyResultOut) => inr(s.total_allocated) },
    { label: 'Remaining Capital',  fmt: (s: StrategyResultOut) => inr(s.remaining_capital) },
    { label: 'Optimizer Score',    fmt: (s: StrategyResultOut) => `${s.optimization_score.toFixed(1)}/100` },
    { label: 'Emergency Reserve',  fmt: (s: StrategyResultOut) => inr(s.allocations[6]?.allocated ?? 0) },
    { label: 'Working Capital',    fmt: (s: StrategyResultOut) => inr(s.allocations[5]?.allocated ?? 0) },
    { label: 'Equipment',          fmt: (s: StrategyResultOut) => inr(s.allocations[0]?.allocated ?? 0) },
    { label: 'Marketing',          fmt: (s: StrategyResultOut) => inr(s.allocations[4]?.allocated ?? 0) },
  ]

  const hdrs = [cons, bal, grow]

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700/40">
            <th className="text-left py-3 px-4 text-gray-500 font-medium w-44">Feature</th>
            {hdrs.map(s => (
              <th key={s.name} className="py-3 px-4 text-center">
                <div className="flex flex-col items-center gap-1">
                  <span className="text-base">{STRATEGY_META[s.name].icon}</span>
                  <span className="font-semibold text-white">{s.name.charAt(0).toUpperCase() + s.name.slice(1)}</span>
                  {s.name === recommended && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-700/40">★ Recommended</span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.label} className={`border-b border-surface-700/20 ${i % 2 === 0 ? 'bg-surface-800/20' : ''}`}>
              <td className="py-2.5 px-4 text-gray-400">{row.label}</td>
              {hdrs.map(s => (
                <td key={s.name} className={`py-2.5 px-4 text-center font-medium ${s.name === recommended ? 'text-primary-300' : 'text-white'}`}>
                  {row.fmt(s)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Allocation Donut-ish BarChart ──────────────────────────────────────────────

function AllocationBarChart({ strategy }: { strategy: StrategyResultOut }) {
  const data = strategy.allocations.map(a => ({
    name: a.name.replace('/ Other', '').replace('Initial ', ''),
    value: Math.round(a.allocated),
    pct: a.pct_of_total,
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v: number) => inrShort(v)}
          tick={{ fill: '#64748b', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          dataKey="name"
          type="category"
          width={88}
          tick={{ fill: '#94a3b8', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0' }}
          formatter={(v: unknown, _n: unknown, props: { payload?: { name: string; pct: number } }) => [
            `${inr(Number(v))} (${props.payload?.pct.toFixed(1)}%)`,
            props.payload?.name,
          ] as [string, string | undefined]}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={CATEGORY_COLORS[strategy.allocations.find(a => a.name.startsWith(entry.name.split(' ')[0]))?.name ?? ''] ?? '#a78bfa'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Side-by-side Strategy Comparison Chart ────────────────────────────────────

function StrategyComparisonChart({ strategies }: { strategies: StrategyResultOut[] }) {
  const categories = ['Emergency Reserve', 'Working Capital', 'Equipment', 'Marketing', 'Initial Inventory']
  const data = categories.map(cat => {
    const row: Record<string, number | string> = { name: cat.replace('Initial ', '') }
    for (const s of strategies) {
      const alloc = s.allocations.find(a => a.name === cat)
      row[s.name] = alloc ? Math.round(alloc.allocated) : 0
    }
    return row
  })

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={(v: number) => inrShort(v)} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
          formatter={(v: unknown, name: unknown) => [inr(Number(v)), String(name).charAt(0).toUpperCase() + String(name).slice(1)] as [string, string]}
        />
        <Legend
          formatter={(value: string) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{value.charAt(0).toUpperCase() + value.slice(1)}</span>}
        />
        <Bar dataKey="conservative" fill="#38bdf8" radius={[3, 3, 0, 0]} />
        <Bar dataKey="balanced"     fill="#a78bfa" radius={[3, 3, 0, 0]} />
        <Bar dataKey="growth"       fill="#34d399" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function InvestmentOptimizer() {
  const { user } = useAuth()
  const { demoProfile } = useDemo()

  // ── State ─────────────────────────────────────────────────────────────────
  const [businesses, setBusinesses] = useState<BusinessPublic[]>([])
  const [bizLoading, setBizLoading] = useState(true)

  const [selectedBizId, setSelectedBizId] = useState<string>('')
  const [capital, setCapital] = useState<string>(
    user?.available_capital ? String(user.available_capital) : (demoProfile?.available_capital ? String(demoProfile.available_capital) : '')
  )
  const [riskPref, setRiskPref] = useState<'conservative' | 'balanced' | 'growth'>('balanced')

  // Optional constraints
  const [showConstraints, setShowConstraints] = useState(false)
  const [minReserve, setMinReserve] = useState<string>('')
  const [minWorking, setMinWorking] = useState<string>('')
  const [maxMarketing, setMaxMarketing] = useState<string>('')

  const [result, setResult] = useState<OptimizationResultOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selectedStrategy, setSelectedStrategy] = useState<'conservative' | 'balanced' | 'growth'>('balanced')

  // ── Load businesses ────────────────────────────────────────────────────────
  useEffect(() => {
    businessService.recommend({ top_n: 10 })
      .then(r => {
        const bizinesses = r.recommendations.map(rec => rec.business)
        setBusinesses(bizinesses)
        if (bizinesses.length > 0) setSelectedBizId(prev => prev || bizinesses[0].id)
      })
      .catch(() => {
        businessService.list({ rural_only: false }).then(r => {
          setBusinesses(r.items.slice(0, 10))
          if (r.items.length > 0) setSelectedBizId(r.items[0].id)
        }).catch(() => {})
      })
      .finally(() => setBizLoading(false))
  }, [])

  // When demo profile is active, prefill capital and ensure a business is selected
  useEffect(() => {
    if (!demoProfile) return
    if (demoProfile.available_capital) {
      setCapital(String(demoProfile.available_capital))
    }
    if (businesses.length > 0) {
      setSelectedBizId(prev => prev || businesses[0].id)
    }
  }, [demoProfile, businesses])

  // ── Run optimizer ──────────────────────────────────────────────────────────
  const runOptimizer = useCallback(async () => {
    const cap = parseFloat(capital)
    if (!selectedBizId) { setError('Please select a business.'); return }
    if (isNaN(cap) || cap <= 0) { setError('Please enter a valid positive capital amount.'); return }

    setError(null)
    setLoading(true)
    try {
      const res = await optimizerService.optimize({
        business_id:               selectedBizId,
        available_capital:         cap,
        risk_preference:           riskPref,
        minimum_emergency_reserve: minReserve  ? parseFloat(minReserve)  : undefined,
        minimum_working_capital:   minWorking  ? parseFloat(minWorking)  : undefined,
        maximum_marketing_budget:  maxMarketing ? parseFloat(maxMarketing) : undefined,
      })
      setResult(res)
      setSelectedStrategy(res.recommended_strategy)
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Optimization failed. Please check your inputs and try again.')
    } finally {
      setLoading(false)
    }
  }, [selectedBizId, capital, riskPref, minReserve, minWorking, maxMarketing])

  const selectedBiz = businesses.find(b => b.id === selectedBizId)
  const selectedStrategyData = result?.strategies.find(s => s.name === selectedStrategy)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            ⚡ <span className="text-gradient">Investment Optimizer</span>
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            OR-Tools powered capital allocation — Conservative, Balanced &amp; Growth strategies.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DemoProgress />
          <Link to="/financial-analysis" className="btn-outline text-sm px-4 py-2">
            💰 Financial Analysis
          </Link>
        </div>
      </div>

      {/* ── Setup Panel ── */}
      <div className="card p-6 space-y-5">
        <h2 className="text-lg font-display font-bold text-white">Configure Optimization</h2>

        <div className="grid md:grid-cols-2 gap-5">
          {/* Business Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Select Business</label>
            {bizLoading ? (
              <div className="flex items-center gap-2 h-10 text-sm text-gray-500">
                <div className="w-4 h-4 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                Loading businesses…
              </div>
            ) : (
              <select
                id="optimizer-business-select"
                value={selectedBizId}
                onChange={e => setSelectedBizId(e.target.value)}
                className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none"
              >
                <option value="">— Select a business —</option>
                {businesses.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            )}
            {selectedBiz && (
              <p className="text-xs text-gray-500">
                Investment: {inrShort(selectedBiz.min_investment)}–{inrShort(selectedBiz.max_investment)}
                {' · '}Risk: <span className={`font-medium ${selectedBiz.risk_level === 'Low' ? 'text-emerald-400' : selectedBiz.risk_level === 'High' ? 'text-red-400' : 'text-amber-400'}`}>{selectedBiz.risk_level}</span>
              </p>
            )}
          </div>

          {/* Capital Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Available Capital (₹)</label>
            <input
              id="optimizer-capital-input"
              type="number"
              min={1}
              value={capital}
              onChange={e => setCapital(e.target.value)}
              placeholder="e.g. 200000"
              className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
            />
            {user?.available_capital && (
              <button
                onClick={() => setCapital(String(user.available_capital))}
                className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
              >
                Use profile capital: {inrShort(user.available_capital)}
              </button>
            )}
          </div>
        </div>

        {/* Risk Preference */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">Risk Preference</label>
          <div className="grid grid-cols-3 gap-3">
            {(['conservative', 'balanced', 'growth'] as const).map(r => (
              <button
                key={r}
                id={`risk-pref-${r}`}
                onClick={() => setRiskPref(r)}
                className={`flex flex-col items-center gap-1 py-3 px-3 rounded-lg border text-sm font-medium transition-all duration-200
                  ${riskPref === r
                    ? 'border-primary-500/70 bg-primary-900/30 text-white'
                    : 'border-surface-700/40 bg-surface-800/40 text-gray-400 hover:text-white hover:border-surface-600/60'
                  }`}
              >
                <span className="text-xl">{STRATEGY_META[r].icon}</span>
                <span>{r.charAt(0).toUpperCase() + r.slice(1)}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Optional Constraints */}
        <div>
          <button
            onClick={() => setShowConstraints(v => !v)}
            className="text-xs text-primary-400 hover:text-primary-300 transition-colors flex items-center gap-1"
          >
            <span>{showConstraints ? '▾' : '▸'}</span>
            {showConstraints ? 'Hide' : 'Show'} Advanced Constraints
          </button>
          {showConstraints && (
            <div className="grid md:grid-cols-3 gap-4 mt-3">
              {[
                { id: 'min-reserve', label: 'Min Emergency Reserve (₹)', val: minReserve, set: setMinReserve },
                { id: 'min-working', label: 'Min Working Capital (₹)',   val: minWorking, set: setMinWorking },
                { id: 'max-mkt',    label: 'Max Marketing Budget (₹)',   val: maxMarketing, set: setMaxMarketing },
              ].map(f => (
                <div key={f.id} className="space-y-1">
                  <label className="text-xs font-medium text-gray-400">{f.label}</label>
                  <input
                    id={f.id}
                    type="number"
                    min={0}
                    value={f.val}
                    onChange={e => f.set(e.target.value)}
                    placeholder="Optional"
                    className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5">
            {error}
          </div>
        )}

        <button
          id="run-optimizer-btn"
          onClick={runOptimizer}
          disabled={loading || !selectedBizId}
          className="btn-primary px-8 py-2.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Optimizing…
            </>
          ) : (
            <>⚡ Run Optimization</>
          )}
        </button>
      </div>

      {/* ── Results ─────────────────────────────────────────────────────────── */}
      {result && (
        <>
          {/* ── Insufficient Capital ── */}
          {result.status === 'insufficient_capital' && result.insufficient_info && (
            <div id="insufficient-capital-panel" className="card p-6 border border-red-700/40 bg-red-900/10">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h2 className="text-lg font-display font-bold text-red-300">Insufficient Capital</h2>
                  <p className="text-xs text-gray-500 mt-0.5">You need more capital to start this business viably.</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mb-5">
                <div className="rounded-xl bg-surface-700/30 p-4 text-center">
                  <p className="text-xs text-gray-500 mb-1">Available Capital</p>
                  <p className="text-xl font-bold text-white">{inr(result.available_capital)}</p>
                </div>
                <div className="rounded-xl bg-surface-700/30 p-4 text-center">
                  <p className="text-xs text-gray-500 mb-1">Minimum Required</p>
                  <p className="text-xl font-bold text-red-400">{inr(result.minimum_required_capital)}</p>
                </div>
                <div className="rounded-xl bg-red-900/30 p-4 text-center border border-red-700/30">
                  <p className="text-xs text-gray-500 mb-1">Funding Gap</p>
                  <p className="text-xl font-bold text-red-400">{inr(result.insufficient_info.funding_gap)}</p>
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-400 mb-3">💡 Planning Suggestions</p>
                <ul className="space-y-2">
                  {result.insufficient_info.suggestions.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-primary-400 mt-0.5 shrink-0">→</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* ── Optimal Results ── */}
          {result.status === 'optimal' && result.strategies.length === 3 && (
            <>
              {/* Summary bar */}
              <div className="card p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-gradient-to-r from-primary-900/20 to-transparent">
                <div className="flex-1">
                  <p className="text-xs text-gray-500 mb-1">Recommended Strategy</p>
                  <p className="text-xl font-display font-bold text-white">
                    {STRATEGY_META[result.recommended_strategy].icon}{' '}
                    {result.recommended_strategy.charAt(0).toUpperCase() + result.recommended_strategy.slice(1)}
                  </p>
                </div>
                <div className="flex gap-6 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">Capital Available</p>
                    <p className="font-bold text-white">{inr(result.available_capital)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Min. Required</p>
                    <p className="font-bold text-emerald-400">{inr(result.minimum_required_capital)}</p>
                  </div>
                </div>
              </div>

              {/* Strategy Cards */}
              <div id="strategy-cards">
                <h2 className="text-lg font-display font-bold text-white mb-4">📊 Strategy Comparison</h2>
                <div className="grid lg:grid-cols-3 gap-4">
                  {result.strategies.map(s => (
                    <StrategyCard
                      key={s.name}
                      strategy={s}
                      isRecommended={s.name === result.recommended_strategy}
                      isSelected={s.name === selectedStrategy}
                      onSelect={() => setSelectedStrategy(s.name as 'conservative' | 'balanced' | 'growth')}
                    />
                  ))}
                </div>
              </div>

              {/* Comparison Table */}
              <div className="card overflow-hidden">
                <div className="px-5 py-4 border-b border-surface-700/30">
                  <h2 className="text-base font-display font-bold text-white">📋 Feature Comparison</h2>
                </div>
                <ComparisonTable strategies={result.strategies} recommended={result.recommended_strategy} />
              </div>

              {/* Charts */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Selected strategy allocation chart */}
                {selectedStrategyData && (
                  <div className="card p-5">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">
                      {STRATEGY_META[selectedStrategy].icon} {selectedStrategy.charAt(0).toUpperCase() + selectedStrategy.slice(1)} — Capital Allocation
                    </h3>
                    <AllocationBarChart strategy={selectedStrategyData} />
                  </div>
                )}

                {/* Side-by-side comparison chart */}
                <div className="card p-5">
                  <h3 className="text-sm font-semibold text-gray-300 mb-4">📊 Strategy vs. Strategy</h3>
                  <StrategyComparisonChart strategies={result.strategies} />
                </div>
              </div>

              {/* Strategy Detail — explanations & trade-offs */}
              {selectedStrategyData && (
                <div id="strategy-detail" className={`card p-6 bg-gradient-to-br ${STRATEGY_META[selectedStrategy].color}`}>
                  <div className="flex items-center gap-2 mb-5">
                    <span className="text-2xl">{STRATEGY_META[selectedStrategy].icon}</span>
                    <h2 className="text-lg font-display font-bold text-white">
                      {selectedStrategyData.label} — Strategy Details
                    </h2>
                    {selectedStrategyData.name === result.recommended_strategy && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-900/50 text-amber-300 border border-amber-700/40 ml-1">★ Recommended</span>
                    )}
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Why This Allocation?</h3>
                      <ul className="space-y-2.5">
                        {selectedStrategyData.explanations.map((e, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                            <span className="text-emerald-400 mt-0.5 shrink-0">✓</span>
                            <span>{e}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Trade-offs</h3>
                      <ul className="space-y-2.5">
                        {selectedStrategyData.tradeoffs.map((t, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                            <span className="text-amber-400 mt-0.5 shrink-0">⚠</span>
                            <span>{t}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="rounded-xl bg-amber-900/10 border border-amber-700/20 px-5 py-4">
                <p className="text-xs text-amber-600/80">
                  ⚠️ <strong>Disclaimer:</strong> {result.disclaimer}
                </p>
              </div>
            </>
          )}
        </>
      )}

      {/* Empty state */}
      {!result && !loading && (
        <div className="card p-10 text-center text-gray-500">
          <div className="text-5xl mb-4">⚡</div>
          <p className="text-lg font-semibold text-gray-400 mb-2">Ready to Optimize</p>
          <p className="text-sm">Select a business, enter your capital, and click <strong className="text-white">Run Optimization</strong> to generate your investment strategies.</p>
        </div>
      )}
    </div>
  )
}
