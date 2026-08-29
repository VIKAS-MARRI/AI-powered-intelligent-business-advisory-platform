import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { businessService } from '../services/businessService'
import type { BusinessPublic } from '../types/business'
import { inrShort, RISK_COLORS, RISK_DOT } from '../utils/format'

const CATEGORIES = [
  'All', 'Agriculture & Allied', 'Food & Beverage', 'Manufacturing',
  'Retail & Distribution', 'Services',
]
const RISK_LEVELS = ['All', 'Low', 'Medium', 'High']

function BusinessCard({ b }: { b: BusinessPublic }) {
  return (
    <div id={`biz-card-${b.id.slice(0, 8)}`} className="card p-5 flex flex-col gap-3 hover:border-primary-700/50 transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="font-display font-semibold text-white text-base leading-snug">{b.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{b.category} · {b.business_type}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded-full border ${RISK_COLORS[b.risk_level]} flex-shrink-0`}>
          {b.risk_level} Risk
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-400 line-clamp-2">{b.description}</p>

      {/* Financials */}
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-surface-800/60 px-3 py-2">
          <p className="text-[10px] text-gray-500 uppercase tracking-wide">Investment</p>
          <p className="text-sm font-semibold text-white mt-0.5">
            {inrShort(b.min_investment)}–{inrShort(b.max_investment)}
          </p>
        </div>
        <div className="rounded-lg bg-surface-800/60 px-3 py-2">
          <p className="text-[10px] text-gray-500 uppercase tracking-wide">Est. Profit/mo</p>
          <p className="text-sm font-semibold text-primary-400 mt-0.5">
            {inrShort(b.estimated_monthly_profit_min)}–{inrShort(b.estimated_monthly_profit_max)}
          </p>
        </div>
      </div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1.5">
        {b.required_skills_list.slice(0, 3).map(s => (
          <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-primary-900/30 text-primary-300 border border-primary-800/30">
            {s}
          </span>
        ))}
        {b.required_skills_list.length > 3 && (
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface-700/50 text-gray-500 border border-surface-600/30">
            +{b.required_skills_list.length - 3} more
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-surface-700/30">
        <span className="text-[10px] text-gray-600">
          Setup: {b.setup_time_weeks_min}–{b.setup_time_weeks_max} weeks
          {b.suitable_for_rural && ' · Rural-suitable'}
        </span>
        {b.is_demo_data && (
          <span className="text-[10px] text-amber-600">Est. values</span>
        )}
      </div>
    </div>
  )
}

export default function Businesses() {
  const [businesses, setBusinesses] = useState<BusinessPublic[]>([])
  const [total, setTotal]           = useState(0)
  const [loading, setLoading]       = useState(true)
  const [search, setSearch]         = useState('')
  const [category, setCategory]     = useState('All')
  const [riskLevel, setRiskLevel]   = useState('All')
  const [minInv, setMinInv]         = useState('')
  const [maxInv, setMaxInv]         = useState('')
  const [ruralOnly, setRuralOnly]   = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await businessService.list({
        category:    category !== 'All' ? category : undefined,
        risk_level:  riskLevel !== 'All' ? riskLevel : undefined,
        min_investment: minInv ? Number(minInv) : undefined,
        max_investment: maxInv ? Number(maxInv) : undefined,
        rural_only:  ruralOnly || undefined,
        search:      search.trim() || undefined,
      })
      setBusinesses(data.items)
      setTotal(data.total)
    } catch {
      // pass
    } finally {
      setLoading(false)
    }
  }, [category, riskLevel, minInv, maxInv, ruralOnly, search])

  useEffect(() => { load() }, [load])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Business Explorer</h1>
          <p className="text-gray-400 mt-1">
            Browse {total} business opportunities suited for rural micro-entrepreneurs.
          </p>
        </div>
        <Link to="/recommendations" id="get-recs-btn"
          className="btn-primary px-5 py-2.5 text-sm whitespace-nowrap">
          Get My Recommendations →
        </Link>
      </div>

      {/* Disclaimer */}
      <div className="mb-6 rounded-lg bg-amber-900/20 border border-amber-700/30 px-4 py-3 text-xs text-amber-500">
        ⚠️ Estimated financial values for advisory purposes only. Actual business results may vary.
      </div>

      {/* Filters */}
      <div id="business-filters" className="card p-5 mb-6">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div className="sm:col-span-2 lg:col-span-1">
            <label className="label text-xs">Search</label>
            <input
              id="biz-search"
              type="search"
              className="input text-sm"
              placeholder="Dairy, Tailoring…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Category */}
          <div>
            <label className="label text-xs">Category</label>
            <select id="biz-cat-filter" className="input text-sm" value={category} onChange={e => setCategory(e.target.value)}>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>

          {/* Risk */}
          <div>
            <label className="label text-xs">Risk Level</label>
            <select id="biz-risk-filter" className="input text-sm" value={riskLevel} onChange={e => setRiskLevel(e.target.value)}>
              {RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
            </select>
          </div>

          {/* Investment range */}
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="label text-xs">Min inv. (₹)</label>
              <input id="biz-min-inv" type="number" className="input text-sm" placeholder="0" value={minInv} onChange={e => setMinInv(e.target.value)} />
            </div>
            <div className="flex-1">
              <label className="label text-xs">Max inv. (₹)</label>
              <input id="biz-max-inv" type="number" className="input text-sm" placeholder="Any" value={maxInv} onChange={e => setMaxInv(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              id="biz-rural-filter"
              type="checkbox"
              checked={ruralOnly}
              onChange={e => setRuralOnly(e.target.checked)}
              className="rounded border-surface-600 bg-surface-700 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-300">Rural-suitable only</span>
          </label>

          <button
            id="biz-reset-filters"
            onClick={() => { setSearch(''); setCategory('All'); setRiskLevel('All'); setMinInv(''); setMaxInv(''); setRuralOnly(false) }}
            className="text-xs text-gray-500 hover:text-primary-400 transition-colors ml-auto"
          >
            Reset filters
          </button>
        </div>
      </div>

      {/* Risk legend */}
      <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
        {['Low', 'Medium', 'High'].map(r => (
          <span key={r} className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${RISK_DOT[r]}`} />
            {r} Risk
          </span>
        ))}
        <span className="ml-auto text-gray-600">{total} businesses found</span>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
        </div>
      ) : businesses.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-500 text-lg">No businesses match your filters.</p>
          <button onClick={() => { setCategory('All'); setRiskLevel('All'); setSearch('') }} className="mt-4 btn-outline text-sm px-4 py-2">
            Clear filters
          </button>
        </div>
      ) : (
        <div id="biz-grid" className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {businesses.map(b => <BusinessCard key={b.id} b={b} />)}
        </div>
      )}
    </div>
  )
}
