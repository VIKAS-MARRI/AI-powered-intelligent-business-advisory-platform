import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'

import { phase8Service } from '../services/phase8Service'
import { financeService } from '../services/financeService'
import { optimizerService } from '../services/optimizerService'
import { marketService } from '../services/marketService'
import { schemeService } from '../services/schemeService'
import { advisoryService } from '../services/advisoryService'

export default function FinalActionPlan() {
  const { demoProfile } = useDemo()
  const navigate = useNavigate()
  // params not needed here; demoProfile is read from hook

  const [loading, setLoading] = useState(false)
  const [recommendation, setRecommendation] = useState<any|null>(null)
  const [finance, setFinance] = useState<any|null>(null)
  const [optimizer, setOptimizer] = useState<any|null>(null)
  const [market, setMarket] = useState<any|null>(null)
  const [schemes, setSchemes] = useState<any|null>(null)
  const [advice, setAdvice] = useState<any|null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!demoProfile) return
    let mounted = true
    setLoading(true)
    setError(null)

    ;(async () => {
      try {
        // 1) Recommendations (top 1)
        const rec = await phase8Service.getPersonalized({ top_n: 1, available_capital: demoProfile.available_capital, skills: demoProfile.skills, business_interests: demoProfile.business_interests })
        if (!mounted) return
        setRecommendation(rec.recommendations?.[0] ?? null)

        // 2) Finance quick analysis for that business
        if (rec.recommendations?.[0]) {
          const bizId = rec.recommendations[0].business_id
          try {
            const f = await financeService.analyze(bizId, demoProfile.available_capital || 0)
            if (mounted) setFinance(f)
          } catch {}

          // 3) Optimizer: run a quick optimize using profile capital
          try {
            const opt = await optimizerService.optimize({ business_id: bizId, available_capital: demoProfile.available_capital || 0, risk_preference: 'balanced' })
            if (mounted) setOptimizer(opt)
          } catch {}
        }

        // 4) Market analysis using state search (best effort)
        try {
          if (demoProfile.state) {
            const locs = await marketService.searchLocation(demoProfile.state, 1)
            if (locs.length > 0) {
              const l0 = locs[0]
              const m = await marketService.analyze({ business_id: recommendation?.business_id ?? undefined, latitude: l0.latitude, longitude: l0.longitude, radius_km: 5 })
              if (mounted) setMarket(m)
            }
          }
        } catch {}

        // 5) Scheme matching
        try {
          if (recommendation?.business_id) {
            const ms = await schemeService.match({ business_id: recommendation.business_id, estimated_investment: finance?.total_estimated_investment ?? undefined, available_capital: demoProfile.available_capital ?? 0, state: demoProfile.state })
            if (mounted) setSchemes(ms)
          }
        } catch {}

        // 6) Advisory (advisoryService.query) — attempt a short question
        try {
          const q = demoProfile.scenario || `What business suits ${demoProfile.name}?`
          const adv = await advisoryService.query({ question: q, available_capital: demoProfile.available_capital ?? 0, state_name: demoProfile.state })
          if (mounted) setAdvice(adv)
        } catch {}

      } catch (e: unknown) {
        if (!mounted) return
        setError('Failed to gather final action plan. Some sections may be missing.')
      } finally {
        if (mounted) setLoading(false)
      }
    })()

    return () => { mounted = false }
  }, [demoProfile])

  if (!demoProfile) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center text-gray-500">
        <p>No demo profile selected. Please start the demo first.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🎯 Final Action Plan</h1>
          <p className="text-xs text-gray-400">Demo Data — Estimates and advisory notes are labeled.</p>
        </div>
        <div className="flex items-center gap-3">
          <DemoProgress />
          <button aria-label="Restart demo" onClick={() => navigate('/demo?demo_profile=' + demoProfile.id)} className="btn-outline px-3 py-1">Restart Demo</button>
          <button aria-label="Exit demo" onClick={() => navigate('/')} className="btn-ghost px-3 py-1">Exit Demo</button>
          <button aria-label="Back to dashboard" onClick={() => navigate('/dashboard')} className="btn-primary px-3 py-1">Back to Dashboard</button>
        </div>
      </div>

      {loading && <div className="card p-6 text-center">Assembling final plan…</div>}

      {error && <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5">{error}</div>}

      <div className="space-y-4">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">💡 Recommended Business</h3>
          {!recommendation && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {recommendation && (
            <div className="mt-2">
              <p className="text-lg font-bold text-white">{recommendation.business_name}</p>
              <p className="text-xs text-gray-400">Rank #{recommendation.rank} — {recommendation.category}</p>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">💰 Financial Outlook</h3>
          {!finance && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {finance && (
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm text-gray-300">
              <div>Estimated investment: <div className="font-bold text-white mt-1">₹{Number(finance.estimated_investment ?? finance.total_estimated_investment ?? 0).toLocaleString('en-IN')}</div></div>
              <div>Est. monthly profit: <div className="font-bold text-emerald-400 mt-1">{finance.monthly_profit ? `₹${Number(finance.monthly_profit).toLocaleString('en-IN')}` : 'Estimate not available'}</div></div>
              <div>Break-even (months): <div className="font-bold text-white mt-1">{finance.break_even_months ?? '—'}</div></div>
              <div>ROI (annual): <div className="font-bold text-white mt-1">{finance.annual_roi_pct ? `${Number(finance.annual_roi_pct).toFixed(1)}%` : '—'}</div></div>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">⚡ Investment Strategy</h3>
          {!optimizer && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {optimizer && (
            <div className="mt-2">
              <p className="text-sm text-gray-400">Recommended strategy: <span className="font-bold text-white">{optimizer.recommended_strategy}</span></p>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">🗺️ Market Intelligence</h3>
          {!market && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {market && (
            <div className="mt-2 text-sm text-gray-300">
              <p>Opportunity score: <span className="font-bold text-white">{market.opportunity?.total ?? market.opportunity?.score ?? '—'}</span></p>
              <p>Location: <span className="font-bold text-white">{market.location_name ?? `${market.latitude}, ${market.longitude}`}</span></p>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">🏛️ Government Support Matches</h3>
          {!schemes && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {schemes && schemes.matches && (
            <ul className="mt-2 space-y-2 text-sm text-gray-300">
              {schemes.matches.slice(0,5).map((m: any, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-primary-400 font-bold">•</span>
                  <div>
                    <div className="font-semibold text-white">{m.scheme_name}</div>
                    <div className="text-xs text-gray-400">Score: {Math.round(m.score_breakdown?.total ?? 0)}/100 — {m.key_benefit}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300">🤖 AI Advisor</h3>
          {!advice && <p className="text-xs text-gray-500">Not analyzed yet</p>}
          {advice && (
            <div className="mt-2 text-sm text-gray-300">
              <p className="font-semibold text-white">Summary</p>
              <p className="text-xs text-gray-400">{advice.final_advice?.summary ?? 'No summary available'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
