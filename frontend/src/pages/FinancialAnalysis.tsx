/**
 * FinancialAnalysis — Phase 3 Financial Intelligence & Planning page.
 *
 * Sections:
 *  1. Business Selector + Capital Input
 *  2. Startup Investment Plan
 *  3. Financial Scenarios (Conservative / Expected / Optimistic)
 *  4. Financial Performance KPIs
 *  5. Break-Even Analysis
 *  6. 12-Month Cash Flow Chart (Recharts)
 *  7. Financial Health Score
 *  8. Risk Indicators
 *
 * All calculations are deterministic Python — no AI/LLM used.
 */
import { useState, useEffect, useCallback } from 'react'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { Link } from 'react-router-dom'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, Area,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import { businessService } from '../services/businessService'
import { financeService } from '../services/financeService'
import type { BusinessPublic } from '../types/business'
import type { FullAnalysisOut, FinancialAssumptions } from '../types/finance'
import { inr, inrShort } from '../utils/format'

// ── Helpers ────────────────────────────────────────────────────────────────────

const RISK_LEVEL_META = {
  Low:    { icon: '🟢', cls: 'text-emerald-400 bg-emerald-900/20 border-emerald-700/30' },
  Medium: { icon: '🟡', cls: 'text-amber-400  bg-amber-900/20  border-amber-700/30' },
  High:   { icon: '🔴', cls: 'text-red-400    bg-red-900/20    border-red-700/30' },
}

const HEALTH_META: Record<string, { color: string; ringColor: string; badge: string }> = {
  Excellent:       { color: '#22c55e', ringColor: 'stroke-emerald-500', badge: 'badge-green' },
  Good:            { color: '#f59e0b', ringColor: 'stroke-amber-400',   badge: 'badge-amber' },
  Fair:            { color: '#f97316', ringColor: 'stroke-orange-400',  badge: 'badge-amber' },
  'Needs Attention': { color: '#ef4444', ringColor: 'stroke-red-500',  badge: 'badge-red'   },
}

function pct(v: number) { return `${v.toFixed(1)}%` }

// ── Sub-components ─────────────────────────────────────────────────────────────

function SectionHeader({ icon, title, subtitle }: { icon: string; title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <span className="text-2xl">{icon}</span>
      <div>
        <h2 className="text-xl font-display font-bold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

/** Horizontal allocation bar */
function AllocationRow({ label, amount, total, color }: { label: string; amount: number; total: number; color: string }) {
  const pctVal = total > 0 ? (amount / total) * 100 : 0
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-gray-400 w-36 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pctVal}%` }} />
      </div>
      <span className="text-sm font-semibold text-white w-20 text-right shrink-0">{inrShort(amount)}</span>
      <span className="text-xs text-gray-600 w-8 text-right shrink-0">{pctVal.toFixed(0)}%</span>
    </div>
  )
}

/** Scenario comparison card */
function ScenarioCard({
  scenario, highlight = false
}: { scenario: { name: string; monthly_revenue: number; monthly_expenses: number; monthly_profit: number; annual_profit: number; profit_margin_pct: number }; highlight?: boolean }) {
  const isLoss = scenario.monthly_profit < 0
  const profitColor = isLoss ? 'text-red-400' : 'text-emerald-400'
  const border = highlight ? 'border-primary-500/60 bg-primary-900/20' : 'border-surface-700/40'

  return (
    <div className={`card p-5 border ${border} transition-all`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-gray-300">{scenario.name}</span>
        {highlight && <span className="badge-green text-[10px]">Expected</span>}
      </div>
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Revenue/mo</span>
          <span className="font-semibold text-white">{inr(scenario.monthly_revenue)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Expenses/mo</span>
          <span className="font-semibold text-white">{inr(scenario.monthly_expenses)}</span>
        </div>
        <div className="border-t border-surface-700/40 pt-3 flex justify-between text-sm">
          <span className="text-gray-400">Profit/mo</span>
          <span className={`font-bold ${profitColor}`}>{inr(scenario.monthly_profit)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Annual Profit</span>
          <span className={`font-semibold ${profitColor}`}>{inr(scenario.annual_profit)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Margin</span>
          <span className="font-semibold text-white">{pct(scenario.profit_margin_pct)}</span>
        </div>
      </div>
    </div>
  )
}

/** KPI tile */
function KpiTile({ label, value, sub, color = 'text-white' }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="card p-5 flex flex-col gap-1">
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className={`text-2xl font-display font-bold ${color}`}>{value}</span>
      {sub && <span className="text-xs text-gray-600">{sub}</span>}
    </div>
  )
}

/** Financial Health radial ring */
function HealthRing({ score, status }: { score: number; status: string }) {
  const meta = HEALTH_META[status] ?? HEALTH_META['Fair']
  const c = 2 * Math.PI * 52
  const offset = c - (score / 100) * c
  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r="52" fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="60" cy="60" r="52" fill="none"
          stroke={meta.color} strokeWidth="8"
          strokeDasharray={c} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1.2s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
        <span className="text-3xl font-display font-bold text-white">{Math.round(score)}</span>
        <span className="text-xs text-gray-500">/ 100</span>
      </div>
    </div>
  )
}

/** Assumption slider/number input row */
function AssumptionRow({
  label, hint, value, min, max, step, format, onChange
}: {
  label: string; hint: string; value: number; min: number; max: number; step: number
  format: (v: number) => string
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-baseline">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <span className="text-sm font-bold text-primary-400">{format(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-2 bg-surface-700 rounded-full appearance-none cursor-pointer accent-primary-500"
      />
      <p className="text-xs text-gray-600">{hint}</p>
    </div>
  )
}

// ── Custom Recharts tooltip ────────────────────────────────────────────────────

function CashFlowTooltip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; fill?: string; stroke?: string }[]; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-800 border border-primary-800/40 rounded-xl p-3 shadow-xl text-xs">
      <p className="text-gray-400 mb-2 font-semibold">Month {label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex justify-between gap-4 mb-1">
          <span className="text-gray-400">{p.name}</span>
          <span className="font-bold" style={{ color: p.fill ?? p.stroke ?? '#fff' }}>
            {inrShort(p.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function FinancialAnalysis() {
  const { user } = useAuth()
  const { demoProfile } = useDemo()

  // Business list
  const [businesses, setBusinesses] = useState<BusinessPublic[]>([])
  const [bizLoading, setBizLoading] = useState(true)

  // Selections
  const [selectedBizId, setSelectedBizId] = useState('')
  const [capital, setCapital] = useState<number>(user?.available_capital ?? (demoProfile?.available_capital ?? 100000))
  const [capitalInput, setCapitalInput] = useState(String(user?.available_capital ?? (demoProfile?.available_capital ?? 100000)))

  // Assumptions (tweakable)
  const [assumptions, setAssumptions] = useState<FinancialAssumptions>({
    emergency_reserve_pct: 0.125,
    working_capital_pct: 0.20,
    monthly_revenue_growth: 0.02,
    monthly_expense_growth: 0.005,
    fixed_cost_ratio: 0.55,
    variable_cost_ratio: null,
  })
  const [showAssumptions, setShowAssumptions] = useState(false)

  // Analysis result
  const [analysis, setAnalysis] = useState<FullAnalysisOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Chart active scenario
  const [chartScenario, setChartScenario] = useState<'conservative' | 'expected' | 'optimistic'>('expected')

  // Load businesses
  useEffect(() => {
    businessService.list()
      .then(r => {
        setBusinesses(r.items)
        if (r.items.length > 0) setSelectedBizId(prev => prev || r.items[0].id)
      })
      .catch(() => {})
      .finally(() => setBizLoading(false))
  }, [])

  // Auto-run analysis when demo profile provided (non-destructive)
  useEffect(() => {
    if (!demoProfile) return
    // set capital from demo profile and run analysis for first business
    if (demoProfile.available_capital) {
      setCapital(demoProfile.available_capital)
      setCapitalInput(String(demoProfile.available_capital))
    }
    // attempt to run after businesses loaded
    if (businesses.length > 0) {
      setSelectedBizId(b => b || businesses[0].id)
      // run analysis for selected business
      setTimeout(() => { runAnalysis().catch(() => {}) }, 500)
    }
  }, [demoProfile, businesses])

  const runAnalysis = useCallback(async () => {
    if (!selectedBizId || capital <= 0) return
    setLoading(true)
    setError('')
    try {
      const result = await financeService.analyze(selectedBizId, capital, assumptions)
      setAnalysis(result)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err?.response?.data?.detail ?? 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [selectedBizId, capital, assumptions])

  const handleCapitalChange = (val: string) => {
    setCapitalInput(val)
    const n = parseFloat(val)
    if (!isNaN(n) && n > 0) setCapital(n)
  }

  // Build chart data from selected scenario's revenue/expenses
  const chartData = analysis
    ? analysis.cash_flow.map(m => ({
        month: m.month,
        Revenue: m.revenue,
        Expenses: m.expenses,
        Profit: m.profit,
        'Cumulative': m.cumulative_cash_flow,
      }))
    : []

  const selectedBiz = businesses.find(b => b.id === selectedBizId)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            💰 <span className="text-gradient">Financial Analysis</span>
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Deterministic financial planning engine — no AI/LLM involved in calculations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DemoProgress />
          <Link to="/recommendations" className="btn-outline text-sm px-4 py-2">
            ← Recommendations
          </Link>
        </div>
      </div>

      {/* ── Disclaimer ── */}
      <div className="rounded-xl bg-amber-900/10 border border-amber-700/30 px-4 py-3 flex items-start gap-3">
        <span className="text-amber-400 text-lg shrink-0">⚠️</span>
        <p className="text-xs text-amber-400/80">
          <strong>Financial projections are estimates for planning purposes only.</strong>{' '}
          Actual costs, revenue, and profits may vary significantly based on location, execution,
          market conditions, and other factors. Consult local experts before making investment decisions.
        </p>
      </div>

      {/* ── Input Panel ── */}
      <div className="card p-6 space-y-6">
        <SectionHeader icon="⚙️" title="Configure Analysis" />

        <div className="grid sm:grid-cols-2 gap-6">
          {/* Business selector */}
          <div>
            <label className="label">Select Business</label>
            {bizLoading ? (
              <div className="input flex items-center gap-2 text-gray-500 text-sm">
                <div className="w-4 h-4 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                Loading businesses…
              </div>
            ) : (
              <select
                id="biz-select"
                value={selectedBizId}
                onChange={e => { setSelectedBizId(e.target.value); setAnalysis(null) }}
                className="input"
              >
                {businesses.map(b => (
                  <option key={b.id} value={b.id}>{b.name} ({b.category})</option>
                ))}
              </select>
            )}
            {selectedBiz && (
              <p className="text-xs text-gray-600 mt-1.5">
                Min investment: {inrShort(selectedBiz.min_investment)} — {inrShort(selectedBiz.max_investment)} |{' '}
                Est. profit: {inrShort(selectedBiz.estimated_monthly_profit_min)}–{inrShort(selectedBiz.estimated_monthly_profit_max)}/mo
              </p>
            )}
          </div>

          {/* Capital input */}
          <div>
            <label className="label">Available Capital (₹)</label>
            <input
              id="capital-input"
              type="number"
              min={1000}
              step={1000}
              value={capitalInput}
              onChange={e => handleCapitalChange(e.target.value)}
              className="input"
              placeholder="e.g. 200000"
            />
            <p className="text-xs text-gray-600 mt-1.5">
              {capital > 0 ? `₹${capital.toLocaleString('en-IN')} ready to invest` : 'Enter a positive amount'}
            </p>
          </div>
        </div>

        {/* Advanced assumptions */}
        <div>
          <button
            id="toggle-assumptions"
            onClick={() => setShowAssumptions(x => !x)}
            className="text-sm text-primary-400 hover:text-primary-300 transition-colors flex items-center gap-1"
          >
            {showAssumptions ? '▲ Hide' : '▼ Show'} advanced assumptions
          </button>

          {showAssumptions && (
            <div className="mt-5 grid sm:grid-cols-2 gap-6 p-5 rounded-xl bg-surface-700/30 border border-surface-700/50">
              <AssumptionRow
                label="Emergency Reserve"
                hint="Fraction of capital kept as emergency fund"
                value={assumptions.emergency_reserve_pct}
                min={0.05} max={0.30} step={0.005}
                format={v => pct(v * 100)}
                onChange={v => setAssumptions(a => ({ ...a, emergency_reserve_pct: v }))}
              />
              <AssumptionRow
                label="Working Capital"
                hint="Fraction of capital as day-to-day working capital"
                value={assumptions.working_capital_pct}
                min={0.05} max={0.40} step={0.01}
                format={v => pct(v * 100)}
                onChange={v => setAssumptions(a => ({ ...a, working_capital_pct: v }))}
              />
              <AssumptionRow
                label="Monthly Revenue Growth"
                hint="Expected monthly revenue growth rate"
                value={assumptions.monthly_revenue_growth}
                min={0} max={0.15} step={0.005}
                format={v => pct(v * 100)}
                onChange={v => setAssumptions(a => ({ ...a, monthly_revenue_growth: v }))}
              />
              <AssumptionRow
                label="Fixed Cost Ratio"
                hint="Fraction of expenses that are fixed costs"
                value={assumptions.fixed_cost_ratio}
                min={0.2} max={0.85} step={0.05}
                format={v => pct(v * 100)}
                onChange={v => setAssumptions(a => ({ ...a, fixed_cost_ratio: v }))}
              />
            </div>
          )}
        </div>

        <button
          id="run-analysis-btn"
          onClick={runAnalysis}
          disabled={loading || !selectedBizId || capital <= 0}
          className="btn-primary w-full sm:w-auto px-8 py-3"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Calculating…
            </>
          ) : '📊 Generate Financial Analysis'}
        </button>

        {error && (
          <div className="rounded-xl bg-red-900/20 border border-red-700/30 p-4 text-sm text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* ── Results (only shown after analysis) ── */}
      {analysis && (
        <>
          {/* Business title bar */}
          <div className="card p-4 flex items-center justify-between gap-4 bg-gradient-to-r from-primary-900/30 to-transparent">
            <div>
              <h2 className="text-lg font-display font-bold text-white">{analysis.business_name}</h2>
              <p className="text-xs text-gray-500">
                Capital: {inr(analysis.available_capital)} ·{' '}
                {analysis.investment.is_feasible
                  ? <span className="text-emerald-400">✓ Feasible — no funding gap</span>
                  : <span className="text-red-400">⚠ Funding gap of {inr(analysis.investment.funding_gap)}</span>}
              </p>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-xs text-gray-500">Health Score</p>
              <p className="text-2xl font-display font-bold"
                style={{ color: HEALTH_META[analysis.health.status]?.color ?? '#fff' }}>
                {Math.round(analysis.health.total)}/100
              </p>
              <p className="text-xs text-gray-400">{analysis.health.status}</p>
            </div>
          </div>

          {/* ── 1. Startup Investment Plan ── */}
          <div className="card p-6">
            <SectionHeader
              icon="💰"
              title="Startup Investment Plan"
              subtitle="How your capital is recommended to be allocated"
            />

            {!analysis.investment.is_feasible && (
              <div className="mb-5 rounded-xl bg-red-900/20 border border-red-700/30 p-4 flex items-start gap-3">
                <span className="text-red-400 text-xl shrink-0">⚠️</span>
                <div>
                  <p className="text-sm font-semibold text-red-400">Funding Gap Detected</p>
                  <p className="text-xs text-red-400/80 mt-0.5">
                    Your capital of {inr(analysis.available_capital)} is{' '}
                    {inr(analysis.investment.funding_gap)} below the minimum investment of{' '}
                    {inr(analysis.available_capital + analysis.investment.funding_gap)}.
                    Consider MUDRA loans or government schemes.
                  </p>
                </div>
              </div>
            )}

            <div className="space-y-1">
              {Object.entries(analysis.investment.allocation_dict).map(([label, amount], i) => {
                const colors = [
                  'bg-primary-500', 'bg-sky-500', 'bg-violet-500',
                  'bg-rose-500', 'bg-amber-500', 'bg-emerald-500', 'bg-indigo-500'
                ]
                return (
                  <AllocationRow
                    key={label}
                    label={label}
                    amount={amount}
                    total={analysis.investment.total_allocated}
                    color={colors[i % colors.length]}
                  />
                )
              })}
              <div className="border-t border-surface-700/40 pt-3 mt-2 flex justify-between items-center">
                <span className="text-sm font-bold text-gray-300">Total Allocated</span>
                <span className="text-lg font-display font-bold text-white">
                  {inr(analysis.investment.total_allocated)}
                </span>
              </div>
            </div>
          </div>

          {/* ── 2. Financial Scenarios ── */}
          <div className="card p-6">
            <SectionHeader
              icon="📊"
              title="Financial Scenarios"
              subtitle="Three projections based on business performance ranges"
            />
            <div className="grid sm:grid-cols-3 gap-4">
              <ScenarioCard scenario={analysis.conservative} />
              <ScenarioCard scenario={analysis.expected} highlight />
              <ScenarioCard scenario={analysis.optimistic} />
            </div>
            <p className="text-xs text-amber-600 mt-4">
              ⚠️ Financial estimates are illustrative and actual results may vary.
            </p>
          </div>

          {/* ── 3. Financial Performance KPIs ── */}
          <div className="card p-6">
            <SectionHeader
              icon="📈"
              title="Financial Performance"
              subtitle="Based on the Expected scenario"
            />
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <KpiTile
                label="Monthly Revenue"
                value={inrShort(analysis.expected.monthly_revenue)}
                sub="Expected"
                color="text-white"
              />
              <KpiTile
                label="Monthly Expenses"
                value={inrShort(analysis.expected.monthly_expenses)}
                sub="Expected"
                color="text-white"
              />
              <KpiTile
                label="Monthly Profit"
                value={inrShort(analysis.expected.monthly_profit)}
                sub={analysis.expected.monthly_profit >= 0 ? 'Positive ✓' : 'Loss ⚠️'}
                color={analysis.expected.monthly_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}
              />
              <KpiTile
                label="Annual Profit"
                value={inrShort(analysis.expected.annual_profit)}
                sub="Projected"
                color={analysis.expected.annual_profit >= 0 ? 'text-primary-400' : 'text-red-400'}
              />
              <KpiTile
                label="ROI"
                value={`${analysis.roi_pct.toFixed(1)}%`}
                sub="Annual return"
                color={analysis.roi_pct >= 0 ? 'text-amber-400' : 'text-red-400'}
              />
              <KpiTile
                label="Payback Period"
                value={analysis.payback_feasible && analysis.payback_months != null
                  ? `${analysis.payback_months.toFixed(0)} mo`
                  : 'N/A'}
                sub={analysis.payback_feasible ? 'Months to recover' : 'Cannot estimate'}
                color={analysis.payback_feasible ? 'text-violet-400' : 'text-gray-500'}
              />
            </div>
            {analysis.payback_feasible && (
              <p className="text-xs text-gray-500 mt-3">{analysis.payback_note}</p>
            )}
          </div>

          {/* ── 4. Break-Even Analysis ── */}
          <div className="card p-6">
            <SectionHeader
              icon="🎯"
              title="Break-Even Analysis"
              subtitle={analysis.break_even.assumed ? 'Using assumed variable cost ratio (not exact data available)' : 'Using provided cost structure'}
            />
            <div className="grid sm:grid-cols-3 gap-6">
              <div className="rounded-xl bg-surface-700/30 p-4 text-center">
                <p className="text-xs text-gray-500 mb-1">Monthly Fixed Costs</p>
                <p className="text-2xl font-display font-bold text-white">{inr(analysis.break_even.fixed_costs_monthly)}</p>
                <p className="text-xs text-gray-600 mt-1">{pct(assumptions.fixed_cost_ratio * 100)} of expenses</p>
              </div>
              <div className="rounded-xl bg-surface-700/30 p-4 text-center">
                <p className="text-xs text-gray-500 mb-1">Contribution Margin</p>
                <p className="text-2xl font-display font-bold text-amber-400">
                  {pct(analysis.break_even.contribution_margin_ratio * 100)}
                </p>
                <p className="text-xs text-gray-600 mt-1">Revenue kept after variable costs</p>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-primary-900/30 to-transparent border border-primary-700/30 p-4 text-center">
                <p className="text-xs text-gray-500 mb-1">Break-Even Revenue</p>
                <p className="text-2xl font-display font-bold text-primary-400">
                  {isFinite(analysis.break_even.break_even_revenue)
                    ? inr(analysis.break_even.break_even_revenue)
                    : '∞ (cannot compute)'}
                </p>
                <p className="text-xs text-gray-600 mt-1">Monthly revenue needed to break even</p>
              </div>
            </div>
            {analysis.break_even.assumed && (
              <p className="text-xs text-amber-600 mt-3">
                * Variable cost ratio assumed as {pct(analysis.break_even.variable_cost_ratio * 100)} based on fixed cost ratio.
                Actual ratio may differ.
              </p>
            )}
          </div>

          {/* ── 5. 12-Month Cash Flow Chart ── */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📅</span>
                <div>
                  <h2 className="text-xl font-display font-bold text-white">12-Month Cash Flow Projection</h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Based on Expected scenario · 2% monthly revenue growth · ramp-up in first 2 months
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {(['conservative', 'expected', 'optimistic'] as const).map(s => (
                  <button
                    key={s}
                    onClick={() => setChartScenario(s)}
                    className={`text-xs px-3 py-1.5 rounded-lg transition-all capitalize ${chartScenario === s
                      ? 'bg-primary-600 text-white'
                      : 'bg-surface-700 text-gray-400 hover:text-white'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 11 }} label={{ value: 'Month', position: 'insideBottom', offset: -2, fill: '#6b7280', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={v => inrShort(v)} width={60} />
                  <Tooltip content={<CashFlowTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', color: '#9ca3af', paddingTop: '12px' }} />
                  <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 2" />
                  <Bar dataKey="Revenue" fill="#6366f1" radius={[3, 3, 0, 0]} opacity={0.8} />
                  <Bar dataKey="Expenses" fill="#f59e0b" radius={[3, 3, 0, 0]} opacity={0.7} />
                  <Line type="monotone" dataKey="Profit" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e', r: 3 }} />
                  <Area type="monotone" dataKey="Cumulative" stroke="#818cf8" fill="#818cf8" fillOpacity={0.08} strokeWidth={2} strokeDasharray="5 3" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Monthly table */}
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500 border-b border-surface-700/40">
                    <th className="pb-2 text-left font-medium">Month</th>
                    <th className="pb-2 text-right font-medium">Revenue</th>
                    <th className="pb-2 text-right font-medium">Expenses</th>
                    <th className="pb-2 text-right font-medium">Profit</th>
                    <th className="pb-2 text-right font-medium">Cumulative</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.cash_flow.map(m => (
                    <tr key={m.month} className="border-b border-surface-700/20 hover:bg-surface-700/20 transition-colors">
                      <td className="py-2 text-gray-400">Month {m.month}</td>
                      <td className="py-2 text-right text-white">{inrShort(m.revenue)}</td>
                      <td className="py-2 text-right text-white">{inrShort(m.expenses)}</td>
                      <td className={`py-2 text-right font-medium ${m.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {inrShort(m.profit)}
                      </td>
                      <td className={`py-2 text-right font-medium ${m.cumulative_cash_flow >= 0 ? 'text-primary-400' : 'text-red-400'}`}>
                        {inrShort(m.cumulative_cash_flow)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* ── 6. Financial Health Score ── */}
          <div className="card p-6">
            <SectionHeader icon="🩺" title="Financial Health Score" subtitle="Transparent breakdown of 6 factors (0–100)" />

            <div className="grid lg:grid-cols-3 gap-8">
              {/* Ring + status */}
              <div className="flex flex-col items-center gap-4">
                <HealthRing score={analysis.health.total} status={analysis.health.status} />
                <div className="text-center">
                  <p className="text-lg font-display font-bold text-white">{analysis.health.status}</p>
                  <p className="text-xs text-gray-500 mt-0.5">Overall financial health</p>
                </div>
              </div>

              {/* Score breakdown bars */}
              <div className="lg:col-span-2 space-y-3">
                {[
                  { label: 'Budget Sufficiency',  value: analysis.health.budget_sufficiency,       max: 20, color: 'bg-sky-500' },
                  { label: 'Profitability',        value: analysis.health.profitability,            max: 25, color: 'bg-emerald-500' },
                  { label: 'ROI Score',            value: analysis.health.roi_score,               max: 20, color: 'bg-amber-500' },
                  { label: 'Payback Score',        value: analysis.health.payback_score,           max: 15, color: 'bg-violet-500' },
                  { label: 'Emergency Reserve',    value: analysis.health.emergency_reserve_score, max: 10, color: 'bg-rose-500' },
                  { label: 'Expense Ratio',        value: analysis.health.expense_ratio_score,     max: 10, color: 'bg-primary-500' },
                ].map(item => (
                  <div key={item.label} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-36 shrink-0">{item.label}</span>
                    <div className="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full transition-all duration-700`}
                        style={{ width: `${(item.value / item.max) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-white font-semibold w-16 text-right shrink-0">
                      {item.value}/{item.max}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths / Risks / Recs */}
            <div className="grid sm:grid-cols-3 gap-4 mt-6">
              {analysis.health.strengths.length > 0 && (
                <div className="rounded-xl bg-emerald-900/10 border border-emerald-700/20 p-4">
                  <p className="text-xs font-semibold text-emerald-400 mb-2">✓ Strengths</p>
                  <ul className="space-y-1.5">
                    {analysis.health.strengths.map((s, i) => (
                      <li key={i} className="text-xs text-gray-400">• {s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {analysis.health.risks.length > 0 && (
                <div className="rounded-xl bg-red-900/10 border border-red-700/20 p-4">
                  <p className="text-xs font-semibold text-red-400 mb-2">⚠ Risks</p>
                  <ul className="space-y-1.5">
                    {analysis.health.risks.map((r, i) => (
                      <li key={i} className="text-xs text-gray-400">• {r}</li>
                    ))}
                  </ul>
                </div>
              )}
              {analysis.health.recommendations.length > 0 && (
                <div className="rounded-xl bg-primary-900/10 border border-primary-700/20 p-4">
                  <p className="text-xs font-semibold text-primary-400 mb-2">💡 Recommendations</p>
                  <ul className="space-y-1.5">
                    {analysis.health.recommendations.map((rec, i) => (
                      <li key={i} className="text-xs text-gray-400">• {rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* ── 7. Risk Indicators ── */}
          <div className="card p-6">
            <SectionHeader icon="🚦" title="Financial Risk Indicators" />
            <div className="grid sm:grid-cols-2 gap-4">
              {analysis.risks.map(r => {
                const meta = RISK_LEVEL_META[r.level as keyof typeof RISK_LEVEL_META] ?? RISK_LEVEL_META['Medium']
                return (
                  <div key={r.name} className={`rounded-xl border p-4 ${meta.cls}`}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-lg">{meta.icon}</span>
                      <span className="text-sm font-semibold">{r.name}</span>
                      <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${meta.cls}`}>{r.level} Risk</span>
                    </div>
                    <p className="text-xs text-gray-400">{r.explanation}</p>
                  </div>
                )
              })}
            </div>
          </div>

          {/* ── Final disclaimer ── */}
          <div className="rounded-xl bg-surface-800/60 border border-surface-700/30 px-5 py-4 text-xs text-gray-500 text-center">
            {analysis.disclaimer}
          </div>
        </>
      )}

      {/* ── Empty state ── */}
      {!analysis && !loading && (
        <div className="card p-12 text-center">
          <div className="text-5xl mb-4">📊</div>
          <h3 className="text-lg font-display font-bold text-white mb-2">Ready to Analyse</h3>
          <p className="text-sm text-gray-400 max-w-md mx-auto">
            Select a business, enter your available capital, and click{' '}
            <strong className="text-primary-400">Generate Financial Analysis</strong> to see
            your complete financial plan with ROI, break-even, cash flow, and risk assessment.
          </p>
        </div>
      )}
    </div>
  )
}
