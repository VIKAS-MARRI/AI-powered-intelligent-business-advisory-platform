import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import { businessService } from '../services/businessService'
import { financeService } from '../services/financeService'
import type { RecommendationItem } from '../types/business'
import type { FullAnalysisOut } from '../types/finance'
import { inrShort, RISK_COLORS } from '../utils/format'

interface HealthData { status: string; version: string; environment: string }

const quickActions = [
  { icon: '🤖', label: 'AI Advisor',           to: '/advisor',             color: 'from-primary-900/50 to-violet-900/20 border-primary-700/30', badge: 'Phase 7 ✨', live: true },
  { icon: '🎯', label: 'Recommendations',       to: '/recommendations',      color: 'from-primary-900/40 to-primary-800/20 border-primary-700/30', badge: 'Phase 2', live: true },
  { icon: '🏪', label: 'Business Explorer',     to: '/businesses',           color: 'from-sky-900/40 to-sky-800/20 border-sky-700/30', badge: 'Phase 2', live: true },
  { icon: '💰', label: 'Financial Plan',        to: '/financial-analysis',   color: 'from-green-900/40 to-green-800/20 border-green-700/30', badge: 'Phase 3', live: true },
  { icon: '⚡', label: 'Investment Optimizer',  to: '/investment-optimizer', color: 'from-violet-900/40 to-violet-800/20 border-violet-700/30', badge: 'Phase 4', live: true },
  { icon: '🗺️', label: 'Market Intelligence',  to: '/market-intelligence',  color: 'from-teal-900/40 to-teal-800/20 border-teal-700/30', badge: 'Phase 5', live: true },
  { icon: '🏛️', label: 'Scheme Support',       to: '/scheme-support',       color: 'from-indigo-900/40 to-indigo-800/20 border-indigo-700/30', badge: 'Phase 6', live: true },
]

const upcomingModules = [
  { phase: 8, name: 'What-If Simulator',    icon: '🔮', desc: 'Business scenario simulation engine' },
  { phase: 9, name: 'Supply Chain',         icon: '🔗', desc: 'Rural supply chain optimization' },
]

// ── Score ring (mini) ─────────────────────────────────────────────────────────
function MiniScoreRing({ score }: { score: number }) {
  const c = 2 * Math.PI * 20
  const offset = c - (score / 100) * c
  const color = score >= 75 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444'
  return (
    <div className="relative w-14 h-14 flex-shrink-0">
      <svg viewBox="0 0 48 48" className="w-full h-full -rotate-90">
        <circle cx="24" cy="24" r="20" fill="none" stroke="#1e293b" strokeWidth="4" />
        <circle cx="24" cy="24" r="20" fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold text-white">{Math.round(score)}</span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [health, setHealth]   = useState<HealthData | null>(null)
  const [healthError, setHealthError] = useState(false)
  const [topRec, setTopRec]   = useState<RecommendationItem | null>(null)
  const [recLoading, setRecLoading] = useState(true)
  const [finSnapshot, setFinSnapshot] = useState<FullAnalysisOut | null>(null)
  const [finLoading, setFinLoading] = useState(false)

  useEffect(() => {
    api.get<HealthData>('/health')
      .then(r => setHealth(r.data))
      .catch(() => setHealthError(true))
  }, [])

  useEffect(() => {
    businessService.recommend({ top_n: 1 })
      .then(r => setTopRec(r.recommendations[0] ?? null))
      .catch(() => { /* profile may be empty */ })
      .finally(() => setRecLoading(false))
  }, [])

  // Load financial snapshot for top recommendation
  useEffect(() => {
    if (!topRec || !user?.available_capital) return
    setFinLoading(true)
    financeService
      .analyze(topRec.business.id, user.available_capital)
      .then(setFinSnapshot)
      .catch(() => {})
      .finally(() => setFinLoading(false))
  }, [topRec, user?.available_capital])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }
  const firstName = user?.full_name?.split(' ')[0] ?? user?.email?.split('@')[0] ?? 'Entrepreneur'
  const hasProfile = user?.available_capital != null && user?.skills

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

      {/* ── Welcome header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            {greeting()}, <span className="text-gradient">{firstName}</span> 👋
          </h1>
          <p className="text-gray-400 mt-1">
            {hasProfile
              ? 'Your AI business advisor has personalised recommendations ready.'
              : 'Complete your profile to unlock personalised business recommendations.'}
          </p>
        </div>
        <Link to="/profile" className="btn-primary text-sm px-5 py-2.5 shrink-0">
          {hasProfile ? 'Edit Profile' : 'Complete Profile'} →
        </Link>
      </div>

      {/* ── Journey / Progress Card ── */}
      {/* Derived from real user data; do not fake completion */}
      <div className="card p-5 bg-gradient-to-br from-surface-800/40 to-transparent">
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-title">🚦 RuralBiz AI Command Center</h2>
          <div className="text-sm text-gray-400">Progress: <span className="font-bold text-white">{Math.round(((hasProfile ? 1 : 0) + (topRec ? 1 : 0) + (finSnapshot ? 1 : 0)) / 7 * 100)}%</span></div>
        </div>

        <div className="mb-3">
          <div className="h-2 w-full bg-surface-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary-500 to-primary-400" style={{ width: `${Math.round(((hasProfile ? 1 : 0) + (topRec ? 1 : 0) + (finSnapshot ? 1 : 0)) / 7 * 100)}%` }} />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { id: 'profile', label: 'Profile Completed', done: Boolean(hasProfile), route: '/profile' },
            { id: 'business', label: 'Business Selected', done: Boolean(topRec), route: '/recommendations' },
            { id: 'financial', label: 'Financial Analysis Completed', done: Boolean(finSnapshot), route: '/financial-analysis' },
            { id: 'investment', label: 'Investment Plan Generated', done: false, route: '/investment-optimizer' },
            { id: 'market', label: 'Market Analyzed', done: false, route: '/market-intelligence' },
            { id: 'schemes', label: 'Government Schemes Matched', done: false, route: '/scheme-support' },
            { id: 'advisor', label: 'AI Advisor Used', done: false, route: '/advisor' },
          ].map(s => (
            <button key={s.id} onClick={() => window.location.assign(s.route)}
              className={`text-left rounded-lg p-3 border ${s.done ? 'border-primary-700 bg-primary-900/10' : 'border-surface-700/30 bg-surface-800/50'}`}>
              <div className="flex items-center justify-between">
                <div className="text-sm text-white font-semibold">{s.label}</div>
                <div className={`text-xs px-2 py-0.5 rounded-full ${s.done ? 'bg-emerald-600 text-white' : 'bg-gray-700 text-gray-300'}`}>
                  {s.done ? 'Done' : 'Pending'}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Top Recommendation Widget ── */}
      <div className="card p-5 bg-gradient-to-br from-primary-900/20 to-transparent">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Your Top Business Opportunity</h2>
          <Link to="/recommendations" id="view-all-recs-link" className="text-xs text-primary-400 hover:text-primary-300 transition-colors">
            View all →
          </Link>
        </div>

        {recLoading ? (
          <div className="flex items-center gap-3 py-3">
            <div className="w-6 h-6 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
            <span className="text-sm text-gray-400">Scoring businesses…</span>
          </div>
        ) : !hasProfile ? (
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 py-2">
            <div className="flex-1">
              <p className="text-sm text-gray-400">
                Add your capital, skills, and interests to get AI-matched recommendations.
              </p>
            </div>
            <Link to="/profile" id="complete-profile-btn" className="btn-outline text-sm px-4 py-2 shrink-0">
              Complete Profile
            </Link>
          </div>
        ) : topRec ? (
          <div id="top-rec-widget">
            <div className="flex items-center gap-4">
              <MiniScoreRing score={topRec.final_score} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-0.5">
                  <span className="text-base">🥇</span>
                  <h3 className="font-display font-bold text-white truncate">{topRec.business.name}</h3>
                </div>
                <p className="text-xs text-gray-500">{topRec.business.category}</p>
                <div className="flex items-center gap-3 mt-2 flex-wrap text-xs">
                  <span className="text-gray-400">
                    Investment: <span className="text-white font-medium">
                      {inrShort(topRec.business.min_investment)}–{inrShort(topRec.business.max_investment)}
                    </span>
                  </span>
                  <span className="text-gray-400">
                    Est. Profit: <span className="text-primary-400 font-medium">
                      {inrShort(topRec.business.estimated_monthly_profit_min)}–{inrShort(topRec.business.estimated_monthly_profit_max)}/mo
                    </span>
                  </span>
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] ${RISK_COLORS[topRec.business.risk_level]}`}>
                    {topRec.business.risk_level} Risk
                  </span>
                </div>
              </div>
              <Link to="/recommendations" id="view-recs-btn" className="btn-primary text-xs px-4 py-2 shrink-0 hidden sm:block">
                View →
              </Link>
            </div>
            <p className="text-[10px] text-amber-600 mt-3">
              ⚠️ Estimated values — actual results may vary based on location and execution.
            </p>

            {/* ── Financial Snapshot ── */}
            {finLoading && (
              <div className="mt-4 pt-4 border-t border-surface-700/30 flex items-center gap-2 text-xs text-gray-500">
                <div className="w-3.5 h-3.5 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                Loading financial snapshot…
              </div>
            )}
            {!finLoading && finSnapshot && (
              <div className="mt-4 pt-4 border-t border-surface-700/30" id="fin-snapshot-widget">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-gray-400">💰 Financial Snapshot</p>
                  <Link to="/financial-analysis" id="view-financial-plan-btn" className="text-xs text-primary-400 hover:text-primary-300 transition-colors">
                    View Financial Plan →
                  </Link>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-lg bg-surface-700/40 px-3 py-2 text-center">
                    <p className="text-[10px] text-gray-500 mb-1">Est. Monthly Profit</p>
                    <p className={`text-sm font-bold ${finSnapshot.expected.monthly_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {inrShort(finSnapshot.expected.monthly_profit)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-surface-700/40 px-3 py-2 text-center">
                    <p className="text-[10px] text-gray-500 mb-1">Annual ROI</p>
                    <p className={`text-sm font-bold ${finSnapshot.roi_pct >= 0 ? 'text-amber-400' : 'text-red-400'}`}>
                      {finSnapshot.roi_pct.toFixed(0)}%
                    </p>
                  </div>
                  <div className="rounded-lg bg-surface-700/40 px-3 py-2 text-center">
                    <p className="text-[10px] text-gray-500 mb-1">Health Score</p>
                    <p className="text-sm font-bold text-primary-400">{Math.round(finSnapshot.health.total)}/100</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 py-2">No recommendations available yet. Complete your profile.</p>
        )}
      </div>

      {/* ── Investment Optimizer Card ── */}
      <div id="optimizer-dashboard-card" className="card p-5 bg-gradient-to-br from-violet-900/20 to-transparent border border-violet-800/30">
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-title">⚡ Investment Optimizer</h2>
          <Link to="/investment-optimizer" id="open-optimizer-btn" className="text-xs text-violet-400 hover:text-violet-300 transition-colors">
            Open →
          </Link>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          Use <strong className="text-white">Google OR-Tools</strong> to optimally allocate your capital across
          equipment, inventory, marketing, and reserves — with Conservative, Balanced &amp; Growth strategies.
        </p>
        {user?.available_capital ? (
          <Link
            to="/investment-optimizer"
            id="optimize-investment-btn"
            className="btn-primary text-sm px-5 py-2 inline-flex items-center gap-2"
          >
            ⚡ Optimize Investment
          </Link>
        ) : (
          <Link to="/profile" className="btn-outline text-sm px-4 py-2">
            Set Capital in Profile →
          </Link>
        )}
      </div>

      {/* ── Market Intelligence Card ── */}
      <div id="market-dashboard-card" className="card p-5 bg-gradient-to-br from-teal-900/20 to-transparent border border-teal-800/30">
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-title">🗺️ Hyper-Local Market Intelligence</h2>
          <Link to="/market-intelligence" id="open-market-btn" className="text-xs text-teal-400 hover:text-teal-300 transition-colors">
            Open →
          </Link>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          Analyze your local market using <strong className="text-white">OpenStreetMap</strong> data —
          identify competitors, measure market saturation, and get opportunity scores before starting your business.
        </p>
        <Link
          to="/market-intelligence"
          id="analyze-market-btn"
          className="btn-primary text-sm px-5 py-2 inline-flex items-center gap-2"
          style={{ background: 'linear-gradient(135deg, #0f766e, #0d9488)' }}
        >
          🗺️ Analyze My Market
        </Link>
      </div>

      {/* ── Government Schemes Card ── */}
      <div id="schemes-dashboard-card" className="card p-5 bg-gradient-to-br from-indigo-900/20 to-transparent border border-indigo-800/30">
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-title">🏛️ Government Scheme Support</h2>
          <Link to="/scheme-support" id="open-schemes-btn" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
            Open →
          </Link>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          Find government <strong className="text-white">schemes, subsidies, and loans</strong> that may support your business.
          Get a match score, eligibility status, and official application guidance.
        </p>
        <Link
          to="/scheme-support"
          id="find-schemes-btn"
          className="btn-primary text-sm px-5 py-2 inline-flex items-center gap-2"
          style={{ background: 'linear-gradient(135deg, #3730a3, #4f46e5)' }}
        >
          🏛️ Find Support Schemes
        </Link>
      </div>

      {/* ── Profile stats ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <span className="stat-label">Location</span>
          <span className="stat-value text-lg">
            {user?.village_town ?? user?.district ?? user?.state ?? '—'}
          </span>
          <span className="text-xs text-gray-600">{user?.state ?? 'Not set'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Available Capital</span>
          <span className="stat-value text-lg text-accent-400">
            {user?.available_capital != null ? `₹${user.available_capital.toLocaleString('en-IN')}` : '—'}
          </span>
          <span className="text-xs text-gray-600">Ready to invest</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Income Goal</span>
          <span className="stat-value text-lg text-primary-400">
            {user?.monthly_income_goal != null ? `₹${user.monthly_income_goal.toLocaleString('en-IN')}/mo` : '—'}
          </span>
          <span className="text-xs text-gray-600">Monthly target</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Language</span>
          <span className="stat-value text-lg">
            {user?.preferred_language === 'te' ? '🇮🇳 Telugu' : '🇬🇧 English'}
          </span>
          <span className="text-xs text-gray-600">Preferred</span>
        </div>
      </div>

      {/* ── Backend health ── */}
      <div className="card p-5 flex items-center gap-4">
        <div className={`w-3 h-3 rounded-full shrink-0 ${
          health?.status === 'ok' ? 'bg-primary-400 shadow-glow-sm animate-pulse-slow'
          : healthError ? 'bg-red-400' : 'bg-gray-600 animate-pulse'
        }`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-200">
            {health?.status === 'ok' ? `Backend Connected — RuralBiz AI v${health.version}`
              : healthError ? 'Backend Unavailable — Start the FastAPI server'
              : 'Connecting to backend…'}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {health ? `Environment: ${health.environment}` : 'Checking health endpoint…'}
          </p>
        </div>
        <span className={`badge-${health?.status === 'ok' ? 'green' : healthError ? 'red' : 'gray'} shrink-0`}>
          {health?.status === 'ok' ? 'Online' : healthError ? 'Offline' : 'Checking'}
        </span>
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="section-title mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((a) =>
            a.live ? (
              <Link
                key={a.label}
                to={a.to}
                id={`quick-action-${a.label.toLowerCase().replace(/ /g, '-')}`}
                className={`card p-5 bg-gradient-to-br ${a.color} border hover:scale-[1.02] active:scale-100 transition-all duration-200`}
              >
                <div className="text-3xl mb-3">{a.icon}</div>
                <p className="text-sm font-semibold text-white">{a.label}</p>
                <span className="badge-green text-[10px] mt-1">Live</span>
              </Link>
            ) : (
              <div
                key={a.label}
                className={`relative card p-5 bg-gradient-to-br ${a.color} border opacity-50 cursor-not-allowed`}
                title="Coming in a future phase"
              >
                <div className="text-3xl mb-3">{a.icon}</div>
                <p className="text-sm font-semibold text-gray-300">{a.label}</p>
                <span className="absolute top-3 right-3 badge-gray text-[10px]">{a.badge}</span>
              </div>
            )
          )}
        </div>
      </div>

      {/* ── Roadmap ── */}
      <div>
        <h2 className="section-title mb-1">Upcoming Modules</h2>
        <p className="section-subtitle mb-5 text-sm">
          Phase 1 ✅ Auth · Phase 2 ✅ Recommendations · Phase 3 ✅ Financial Intelligence · Phase 4 ✅ Investment Optimizer · Phase 5 ✅ Market Intelligence · Phase 6 ✅ Scheme Support — next phases below
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {upcomingModules.map((m) => (
            <div key={m.phase} className="card p-5 flex gap-4 opacity-70">
              <div className="text-2xl shrink-0">{m.icon}</div>
              <div className="min-w-0">
                <span className="badge-gray text-[10px]">Phase {m.phase}</span>
                <p className="text-sm font-semibold text-white mt-1">{m.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
