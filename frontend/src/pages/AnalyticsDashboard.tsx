/**
 * Phase 9 — Entrepreneur Analytics Dashboard
 * Sections: Progress Score, Financial Overview, Goals, Actions, Timeline, Insights
 */
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import { analyticsService, actionsService, timelineService } from '../services/analyticsService'
import type { DashboardAnalytics, ActionItem, TimelineEvent } from '../types/analytics'

// ── Colours ──────────────────────────────────────────────────────────────────

const TREND_COLORS: Record<string, string> = {
  improving:         'text-emerald-400',
  stable:            'text-amber-400',
  declining:         'text-red-400',
  insufficient_data: 'text-gray-500',
}

const TREND_ICONS: Record<string, string> = {
  improving: '↑', stable: '→', declining: '↓', insufficient_data: '—',
}

const PRIORITY_BADGE: Record<string, string> = {
  critical: 'bg-red-900/40 text-red-400 border-red-700/40',
  high:     'bg-orange-900/30 text-orange-400 border-orange-700/40',
  medium:   'bg-amber-900/30 text-amber-400 border-amber-700/40',
  low:      'bg-slate-800/40 text-slate-400 border-slate-700/40',
}

const CATEGORY_ICON: Record<string, string> = {
  business:           '💼',
  finance:            '💰',
  market:             '🗺️',
  government_support: '🏛️',
  profile:            '👤',
  growth:             '📈',
}

const ACTIVITY_ICON: Record<string, string> = {
  account_created:        '🎉',
  profile_completed:      '✅',
  recommendation_viewed:  '👁️',
  business_saved:         '⭐',
  financial_analysis:     '💰',
  investment_optimized:   '⚡',
  market_analyzed:        '🗺️',
  scheme_matched:         '🏛️',
  goal_created:           '🎯',
  goal_completed:         '🏆',
  goal_updated:           '📊',
  financial_record_added: '📝',
  ai_advisory:            '🤖',
  advisor_query:          '💬',
}

const PIE_COLORS = ['#22c55e', '#f59e0b', '#64748b', '#ef4444']

// ── Sub-components ────────────────────────────────────────────────────────────

function ProgressRing({ score, size = 120 }: { score: number; size?: number }) {
  const r   = size * 0.38
  const c   = 2 * Math.PI * r
  const off = c - (score / 100) * c
  const col = score >= 70 ? '#22c55e' : score >= 45 ? '#f59e0b' : '#ef4444'
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={8} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={col} strokeWidth={8}
          strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{Math.round(score)}</span>
        <span className="text-[10px] text-gray-500">/100</span>
      </div>
    </div>
  )
}

function TrendBadge({ trend }: { trend: string }) {
  return (
    <span className={`text-xs font-semibold ${TREND_COLORS[trend] ?? 'text-gray-500'}`}>
      {TREND_ICONS[trend] ?? '?'} {trend.replace('_', ' ')}
    </span>
  )
}

function StatCard({ label, value, sub, color = 'text-white' }: {
  label: string; value: string; sub?: string; color?: string
}) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-xl font-bold font-display ${color}`}>{value}</p>
      {sub && <p className="text-[11px] text-gray-500">{sub}</p>}
    </div>
  )
}

function ActionCard({ action, onComplete }: { action: ActionItem; onComplete: (id: string) => void }) {
  return (
    <div className="card p-4 border hover:border-surface-600/50 transition-all">
      <div className="flex items-start gap-3">
        <span className="text-lg shrink-0">{CATEGORY_ICON[action.category] ?? '•'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-semibold text-white">{action.title}</h4>
            <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded border ${PRIORITY_BADGE[action.priority] ?? ''}`}>
              {action.priority}
            </span>
          </div>
          {action.description && (
            <p className="text-[11px] text-gray-400 mt-0.5">{action.description}</p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {action.estimated_effort && (
              <span className="text-[10px] text-gray-500">⏱ {action.estimated_effort}</span>
            )}
            <span className="text-[10px] text-gray-500">Impact: {action.impact}</span>
            {action.related_phase && (
              <span className="text-[10px] text-gray-600">{action.related_phase}</span>
            )}
          </div>
          <div className="mt-2 flex gap-2">
            {action.action_url && (
              <Link to={action.action_url}
                className="text-[11px] text-primary-400 hover:text-primary-300 border border-primary-700/30 px-2 py-1 rounded-lg transition-colors">
                Go →
              </Link>
            )}
            <button
              onClick={() => onComplete(action.id)}
              className="text-[11px] text-emerald-400 hover:text-emerald-300 border border-emerald-700/30 px-2 py-1 rounded-lg transition-colors">
              ✓ Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function TimelineItem({ event }: { event: TimelineEvent }) {
  const d = new Date(event.created_at)
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-surface-700/50 border border-surface-600/30 flex items-center justify-center text-sm shrink-0">
          {ACTIVITY_ICON[event.activity_type] ?? '•'}
        </div>
        <div className="flex-1 w-px bg-surface-700/30 mt-1" />
      </div>
      <div className="pb-4 flex-1 min-w-0">
        <p className="text-xs font-semibold text-white">{event.title}</p>
        {event.description && (
          <p className="text-[10px] text-gray-500">{event.description}</p>
        )}
        <p className="text-[10px] text-gray-600 mt-0.5">
          {d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
        </p>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AnalyticsDashboard() {
  const [data,      setData]      = useState<DashboardAnalytics | null>(null)
  const [actions,   setActions]   = useState<ActionItem[]>([])
  const [timeline,  setTimeline]  = useState<TimelineEvent[]>([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [dash, actionPlan, tl] = await Promise.all([
        analyticsService.getDashboard(),
        actionsService.getNextActions(),
        timelineService.getTimeline(10),
      ])
      setData(dash)
      setActions(actionPlan.actions)
      setTimeline(tl.items)
    } catch {
      setError('Failed to load analytics. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCompleteAction = async (id: string) => {
    try {
      await actionsService.updateStatus(id, 'completed')
      setActions(prev => prev.filter(a => a.id !== id))
    } catch {}
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="card p-12 text-center">
          <div className="w-10 h-10 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-400">Loading your analytics dashboard…</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="card p-8 text-center text-red-400 border-red-700/30">
          <p>{error ?? 'Could not load analytics'}</p>
          <button onClick={load} className="mt-4 btn-primary text-sm px-4 py-2">Retry</button>
        </div>
      </div>
    )
  }

  const { progress_score, financial_analytics, goal_analytics, financial_insights } = data

  const goalPieData = [
    { name: 'Completed',   value: goal_analytics.completed },
    { name: 'In Progress', value: goal_analytics.in_progress },
    { name: 'Not Started', value: goal_analytics.not_started },
    { name: 'Overdue',     value: goal_analytics.overdue },
  ].filter(d => d.value > 0)

  const fmt = (n: number) => n >= 100000
    ? `₹${(n / 100000).toFixed(1)}L`
    : `₹${(n / 1000).toFixed(0)}k`

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            📊 <span className="text-gradient">Entrepreneur Analytics</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Your complete business journey dashboard
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/goals" className="btn-outline text-xs px-3 py-1.5">🎯 Goals</Link>
          <Link to="/financial-progress" className="btn-outline text-xs px-3 py-1.5">💰 Progress</Link>
        </div>
      </div>

      {/* ── Top KPI row ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="card p-4 col-span-2 lg:col-span-1">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Progress Score</p>
          <div className="flex items-center gap-3">
            <ProgressRing score={progress_score.overall_score} size={80} />
            <div className="space-y-1">
              {Object.entries(progress_score.category_scores).map(([k, v]) => (
                <div key={k} className="flex items-center gap-1.5">
                  <div className="flex-1 h-1 bg-surface-700/50 rounded-full">
                    <div className="h-full bg-primary-500 rounded-full" style={{ width: `${v}%` }} />
                  </div>
                  <span className="text-[9px] text-gray-600 w-5 text-right">{v.toFixed(0)}</span>
                </div>
              ))}
            </div>
          </div>
          <p className="text-[9px] text-gray-600 mt-2">
            {progress_score.confidence} confidence
          </p>
        </div>

        <StatCard
          label="Total Revenue"
          value={financial_analytics.status === 'ok' ? fmt(financial_analytics.total_revenue) : '—'}
          sub={`${financial_analytics.record_count} records`}
          color="text-emerald-400"
        />
        <StatCard
          label="Total Profit"
          value={financial_analytics.status === 'ok' ? fmt(financial_analytics.total_profit) : '—'}
          sub={`avg ${financial_analytics.status === 'ok' ? fmt(financial_analytics.avg_monthly_profit) : '—'}/mo`}
          color="text-cyan-400"
        />
        <StatCard
          label="Goals Completed"
          value={`${goal_analytics.completed} / ${goal_analytics.total}`}
          sub={`${goal_analytics.completion_pct.toFixed(0)}% complete`}
          color="text-amber-400"
        />
      </div>

      {/* ── Main grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Financial trends */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-display font-bold text-white">💹 Financial Trends</h2>
            <div className="flex gap-3">
              <TrendBadge trend={financial_analytics.revenue_trend} />
              <TrendBadge trend={financial_analytics.profit_trend} />
            </div>
          </div>

          {financial_analytics.status === 'insufficient_data' ? (
            <div className="h-40 flex flex-col items-center justify-center text-gray-500">
              <div className="text-3xl mb-2">📊</div>
              <p className="text-sm">No financial data yet</p>
              <Link to="/financial-progress" className="mt-3 btn-primary text-xs px-3 py-1.5">
                + Add Records
              </Link>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={financial_analytics.revenue_series.map((p, i) => ({
                name:    p.date ?? `P${i+1}`,
                Revenue: financial_analytics.revenue_series[i]?.value ?? 0,
                Profit:  financial_analytics.profit_series[i]?.value  ?? 0,
                Expenses: financial_analytics.expense_series[i]?.value ?? 0,
              }))}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="prof" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#06b6d4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }}
                  tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : String(v)} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  formatter={(v: unknown) => [`₹${Number(v).toLocaleString('en-IN')}`, ''] as [string, string]}
                />
                <Area type="monotone" dataKey="Revenue"  stroke="#22c55e" fill="url(#rev)"  strokeWidth={2} />
                <Area type="monotone" dataKey="Profit"   stroke="#06b6d4" fill="url(#prof)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Goals pie */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-display font-bold text-white">🎯 Goal Status</h2>
            <Link to="/goals" className="text-[10px] text-primary-400 hover:text-primary-300">
              Manage →
            </Link>
          </div>

          {goal_analytics.total === 0 ? (
            <div className="h-40 flex flex-col items-center justify-center text-gray-500">
              <div className="text-3xl mb-2">🎯</div>
              <p className="text-xs">No goals yet</p>
              <Link to="/goals" className="mt-3 btn-primary text-xs px-3 py-1.5">
                + Create Goal
              </Link>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={goalPieData} cx="50%" cy="50%" outerRadius={55}
                    dataKey="value" label={({ value }) => `${value}`} labelLine={false}>
                    {goalPieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-1 mt-2">
                {goalPieData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-1.5 text-[10px]">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: PIE_COLORS[i] }} />
                    <span className="text-gray-400">{d.name}</span>
                    <span className="text-white ml-auto">{d.value}</span>
                  </div>
                ))}
              </div>
              {goal_analytics.overdue > 0 && (
                <p className="mt-2 text-[10px] text-red-400">
                  ⚠ {goal_analytics.overdue} overdue goal(s)
                </p>
              )}
            </>
          )}
        </div>

        {/* AI Next Actions */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-display font-bold text-white">⚡ AI Next Actions</h2>
            <span className="text-[10px] text-gray-500">{actions.length} pending</span>
          </div>
          {actions.length === 0 ? (
            <div className="card p-6 text-center text-gray-500 text-sm">
              🎉 All actions completed! Keep up the great work.
            </div>
          ) : (
            actions.slice(0, 4).map(a => (
              <ActionCard key={a.id} action={a} onComplete={handleCompleteAction} />
            ))
          )}
        </div>

        {/* Timeline */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-display font-bold text-white">🗓️ Journey Timeline</h2>
          </div>
          {timeline.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-6">No activity yet. Start exploring the platform!</p>
          ) : (
            <div className="space-y-0 max-h-64 overflow-y-auto">
              {timeline.map(event => (
                <TimelineItem key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Insights & Strengths */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Financial insights */}
        <div className="card p-5">
          <h2 className="text-sm font-display font-bold text-white mb-3">💡 Financial Insights</h2>
          {financial_insights.length === 0 ? (
            <p className="text-xs text-gray-500">Add financial records to unlock insights.</p>
          ) : (
            <ul className="space-y-2">
              {financial_insights.map((insight, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <span className="text-primary-400 shrink-0 mt-0.5">•</span>
                  {insight}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Strengths & improvements */}
        <div className="card p-5 space-y-3">
          <h2 className="text-sm font-display font-bold text-white">🏆 Progress Analysis</h2>
          {progress_score.strengths.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider mb-1.5">Strengths</p>
              <ul className="space-y-1">
                {progress_score.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[11px] text-gray-300">
                    <span className="text-emerald-400 shrink-0">✓</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {progress_score.improvement_areas.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider mb-1.5">Areas to Improve</p>
              <ul className="space-y-1">
                {progress_score.improvement_areas.map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[11px] text-gray-300">
                    <span className="text-amber-400 shrink-0">→</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-[10px] text-gray-600 italic pt-1">{progress_score.disclaimer}</p>
        </div>
      </div>

      {/* Global disclaimer */}
      <p className="text-center text-[11px] text-gray-600 pb-2">
        {data.disclaimer}
      </p>
    </div>
  )
}
