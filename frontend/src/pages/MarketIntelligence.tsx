/**
 * MarketIntelligence — Phase 5 Hyper-Local Market Intelligence page.
 *
 * Sections:
 *  1. Business + Location Configurator
 *  2. Interactive Leaflet Map with markers, radius circle, popups
 *  3. Competition Analysis Panel
 *  4. Market Opportunity Score (0-100) + breakdown
 *  5. Location Suitability Score (0-100) + breakdown
 *  6. Nearby Businesses list (filterable by category)
 *  7. Insights + Recommendations
 *  8. OpenStreetMap data disclaimer
 *
 * Uses Leaflet (OpenStreetMap tiles) — no paid API key required.
 */
import {
  useState, useEffect, useCallback, useMemo,
} from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { useAuth } from '../context/AuthContext'
import { businessService } from '../services/businessService'
import { marketService } from '../services/marketService'
import useDemo from '../hooks/useDemo'
import DemoProgress from '../components/DemoProgress'
import { useLocation } from 'react-router-dom'
import type { BusinessPublic } from '../types/business'
import type {
  LocationSearchResult,
  MarketAnalysisOut,
  MarketInsightOut,
} from '../types/market'

// Fix Leaflet default icon paths broken by Vite/bundlers — use CDN URLs
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl:        'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// ── Custom icons ─────────────────────────────────────────────────────────────
const SHADOW_URL = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'

const PIN_CENTER = new L.Icon({
  iconUrl:      'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl:    SHADOW_URL,
  iconSize:     [25, 41],
  iconAnchor:   [12, 41],
  popupAnchor:  [1, -34],
  shadowSize:   [41, 41],
})

const PIN_COMPETITOR = new L.Icon({
  iconUrl:      'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl:    SHADOW_URL,
  iconSize:     [20, 33],
  iconAnchor:   [10, 33],
  popupAnchor:  [1, -28],
  shadowSize:   [41, 41],
})

const PIN_PLACE = new L.Icon({
  iconUrl:      'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl:    SHADOW_URL,
  iconSize:     [17, 28],
  iconAnchor:   [8, 28],
  popupAnchor:  [1, -24],
  shadowSize:   [41, 41],
})


// ── Helper: auto-fly map to new location ─────────────────────────────────────
function FlyTo({ lat, lng, zoom = 13 }: { lat: number; lng: number; zoom?: number }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo([lat, lng], zoom, { duration: 1.2 })
  }, [lat, lng, zoom, map])
  return null
}

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({
  score, label, color, size = 100,
}: { score: number; label: string; color: string; size?: number }) {
  const r   = (size / 2) - 8
  const C   = 2 * Math.PI * r
  const off = C - (score / 100) * C
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth="7" />
          <circle
            cx={size/2} cy={size/2} r={r} fill="none"
            stroke={color} strokeWidth="7"
            strokeDasharray={C} strokeDashoffset={off}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-white leading-none">{Math.round(score)}</span>
          <span className="text-[10px] text-gray-500">/ 100</span>
        </div>
      </div>
      <span className="text-xs text-gray-400 text-center">{label}</span>
    </div>
  )
}

// ── Competition Badge ─────────────────────────────────────────────────────────
function CompBadge({ level }: { level: 'Low' | 'Moderate' | 'High' | string }) {
  const cfg: Record<string, { cls: string; icon: string }> = {
    Low:      { cls: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/40', icon: '🟢' },
    Moderate: { cls: 'bg-amber-900/40 text-amber-300 border-amber-700/40',       icon: '🟡' },
    High:     { cls: 'bg-red-900/40 text-red-300 border-red-700/40',             icon: '🔴' },
  }
  const { cls, icon } = cfg[level] ?? cfg['Moderate']
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-sm font-semibold ${cls}`}>
      {icon} {level} Competition
    </span>
  )
}

// ── Score Bar ─────────────────────────────────────────────────────────────────
function ScoreBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs text-gray-400 w-36 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-surface-700/60 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold text-white w-10 text-right shrink-0">
        {value.toFixed(1)}
      </span>
    </div>
  )
}

// ── Insight Row ───────────────────────────────────────────────────────────────
function InsightRow({ insight }: { insight: MarketInsightOut }) {
  const border = insight.level === 'positive'
    ? 'border-l-emerald-500' : insight.level === 'warning'
    ? 'border-l-amber-500' : 'border-l-slate-500'
  return (
    <div className={`flex items-start gap-3 px-4 py-2.5 border-l-2 ${border} bg-surface-800/30 rounded-r-lg`}>
      <span className="text-base shrink-0 mt-0.5">{insight.icon}</span>
      <p className="text-sm text-gray-300">{insight.message}</p>
    </div>
  )
}

// ── Category colours for map markers ─────────────────────────────────────────
const CATEGORY_DOT: Record<string, string> = {
  'Dairy & Milk':         '#38bdf8',
  'Tailoring & Clothing': '#f472b6',
  'Retail & Distribution':'#a78bfa',
  'Market':               '#fb923c',
  'Medical & Health':     '#4ade80',
  'Food Service':         '#facc15',
  'Education':            '#34d399',
  'Transport':            '#94a3b8',
  'Banking & Finance':    '#60a5fa',
}

// ── useDebounce ───────────────────────────────────────────────────────────────
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])
  return debounced
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629]   // Centre of India
const RADIUS_OPTIONS = [1, 2, 5, 10] as const

export default function MarketIntelligence() {
  const { } = useAuth()   // auth context available; user destructured if needed later
  const loc = useLocation()
  const params = new URLSearchParams(loc.search)
  const autoplay = params.get('autoplay') === '1'
  const { demoProfile } = useDemo()

  // ── State ─────────────────────────────────────────────────────────────────
  const [businesses, setBusinesses]   = useState<BusinessPublic[]>([])
  const [bizLoading, setBizLoading]   = useState(true)
  const [selectedBizId, setSelectedBizId] = useState('')

  const [locationQuery, setLocationQuery]     = useState('')
  const [locationResults, setLocationResults] = useState<LocationSearchResult[]>([])
  const [locSearching, setLocSearching]       = useState(false)
  const [showLocDropdown, setShowLocDropdown] = useState(false)

  const [selectedLat, setSelectedLat] = useState<number | null>(null)
  const [selectedLon, setSelectedLon] = useState<number | null>(null)
  const [locationLabel, setLocationLabel] = useState('')

  const [radiusKm, setRadiusKm] = useState<number>(5)

  const [analysis, setAnalysis] = useState<MarketAnalysisOut | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)

  const [catFilter, setCatFilter] = useState<string>('All')

  const debouncedQuery = useDebounce(locationQuery, 400)

  // ── Load businesses ────────────────────────────────────────────────────────
  useEffect(() => {
    businessService.recommend({ top_n: 10 })
      .then(r => {
        const list = r.recommendations.map(rec => rec.business)
        setBusinesses(list)
        if (list.length) setSelectedBizId(prev => prev || list[0].id)
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

  // ── Debounced location search ──────────────────────────────────────────────
  useEffect(() => {
    if (debouncedQuery.length < 3) {
      setLocationResults([])
      setShowLocDropdown(false)
      return
    }
    setLocSearching(true)
    marketService.searchLocation(debouncedQuery, 6)
      .then(res => {
        setLocationResults(res)
        setShowLocDropdown(res.length > 0)
      })
      .catch(() => setLocationResults([]))
      .finally(() => setLocSearching(false))
  }, [debouncedQuery])

  // If demo profile active, attempt to auto-select a location based on demo state
  useEffect(() => {
    if (!demoProfile) return
    if (!selectedLat && !selectedLon && demoProfile.state) {
      marketService.searchLocation(demoProfile.state, 1)
        .then(res => {
          if (res.length > 0) {
            const loc0 = res[0]
            setSelectedLat(loc0.latitude)
            setSelectedLon(loc0.longitude)
            setLocationLabel(loc0.display_name.split(',').slice(0,3).join(', '))
            setLocationQuery(loc0.display_name.split(',').slice(0,3).join(', '))
          }
        })
        .catch(() => {})
    }
  }, [demoProfile])

  // Auto-run analysis when autoplay=1 and demo active
  useEffect(() => {
    if (!autoplay || !demoProfile) return
    const t = setTimeout(() => {
      if (selectedBizId && selectedLat && selectedLon && !analysis && !loading) {
        void runAnalysis()
      }
    }, 700)
    return () => clearTimeout(t)
  }, [autoplay, demoProfile, selectedBizId, selectedLat, selectedLon, analysis, loading])

  // ── Select a location from dropdown ───────────────────────────────────────
  const selectLocation = useCallback((loc: LocationSearchResult) => {
    setSelectedLat(loc.latitude)
    setSelectedLon(loc.longitude)
    setLocationLabel(loc.display_name.split(',').slice(0, 3).join(', '))
    setLocationQuery(loc.display_name.split(',').slice(0, 3).join(', '))
    setShowLocDropdown(false)
    setLocationResults([])
  }, [])

  // ── Click on map to set location ───────────────────────────────────────────
  function MapClickHandler() {
    const map = useMap()
    useEffect(() => {
      const handler = (e: L.LeafletMouseEvent) => {
        setSelectedLat(e.latlng.lat)
        setSelectedLon(e.latlng.lng)
        setLocationLabel(`${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`)
        setLocationQuery(`${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`)
      }
      map.on('click', handler)
      return () => { map.off('click', handler) }
    }, [map])
    return null
  }

  // ── Run analysis ───────────────────────────────────────────────────────────
  const runAnalysis = useCallback(async () => {
    if (!selectedBizId) { setError('Please select a business.'); return }
    if (selectedLat === null || selectedLon === null) {
      setError('Please search for a location or click on the map to select one.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await marketService.analyze({
        business_id: selectedBizId,
        latitude:    selectedLat,
        longitude:   selectedLon,
        radius_km:   radiusKm,
      })
      setAnalysis(res)
      setCatFilter('All')
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [selectedBizId, selectedLat, selectedLon, radiusKm])

  // ── Derived data ───────────────────────────────────────────────────────────
  const categories = useMemo(() => {
    if (!analysis) return []
    const cats = new Set(analysis.nearby_places.map(p => p.category))
    return ['All', ...Array.from(cats).sort()]
  }, [analysis])

  const filteredPlaces = useMemo(() => {
    if (!analysis) return []
    return catFilter === 'All'
      ? analysis.nearby_places
      : analysis.nearby_places.filter(p => p.category === catFilter)
  }, [analysis, catFilter])

  const competitorIds = useMemo(() => {
    if (!analysis) return new Set<string>()
    return new Set(analysis.direct_competitors.map(p => p.osm_id))
  }, [analysis])

  const mapCenter: [number, number] = selectedLat && selectedLon
    ? [selectedLat, selectedLon]
    : DEFAULT_CENTER

  const mapKey = `${selectedLat}-${selectedLon}`   // force re-init when location changes

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            🗺️ <span className="text-gradient">Market Intelligence</span>
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            OpenStreetMap-powered hyper-local market analysis — competitor detection &amp; opportunity scoring.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {demoProfile && <div className="text-xs text-amber-300 font-semibold">Demo Data</div>}
          <DemoProgress />
          <Link to="/investment-optimizer" className="btn-outline text-sm px-4 py-2">
            ⚡ Investment Optimizer
          </Link>
        </div>
      </div>

      {/* ── Configurator ── */}
      <div className="card p-6 space-y-5">
        <h2 className="text-lg font-display font-bold text-white">Configure Analysis</h2>

        <div className="grid md:grid-cols-2 gap-5">
          {/* Business select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Select Business</label>
            {bizLoading ? (
              <div className="flex items-center gap-2 h-10 text-sm text-gray-500">
                <div className="w-4 h-4 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                Loading…
              </div>
            ) : (
              <select
                id="market-business-select"
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
          </div>

          {/* Location search */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Location <span className="text-gray-600 font-normal">(search or click the map)</span>
            </label>
            <div className="relative">
              <input
                id="market-location-search"
                type="text"
                value={locationQuery}
                onChange={e => {
                  setLocationQuery(e.target.value)
                  if (e.target.value.length < 3) setShowLocDropdown(false)
                }}
                onFocus={() => locationResults.length > 0 && setShowLocDropdown(true)}
                placeholder="Search: Manthani, Telangana…"
                className="w-full bg-surface-800 border border-surface-600/50 text-white text-sm rounded-lg px-3 py-2.5 pr-8 focus:ring-2 focus:ring-primary-500/50 focus:outline-none placeholder-gray-600"
              />
              {locSearching && (
                <div className="absolute right-3 top-3">
                  <div className="w-3.5 h-3.5 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                </div>
              )}
              {showLocDropdown && locationResults.length > 0 && (
                <ul className="absolute z-50 mt-1 w-full bg-surface-800 border border-surface-600/50 rounded-lg shadow-xl max-h-56 overflow-y-auto">
                  {locationResults.map((loc, i) => (
                    <li
                      key={i}
                      onClick={() => selectLocation(loc)}
                      className="px-3 py-2.5 text-sm text-gray-300 hover:bg-surface-700 cursor-pointer border-b border-surface-700/30 last:border-0"
                    >
                      <span className="font-medium text-white">
                        {loc.display_name.split(',')[0]}
                      </span>
                      <span className="text-gray-500 ml-1 text-xs">
                        {loc.display_name.split(',').slice(1, 3).join(',')}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {selectedLat && (
              <p className="text-xs text-gray-600">
                📍 {selectedLat.toFixed(4)}, {selectedLon?.toFixed(4)}
              </p>
            )}
          </div>
        </div>

        {/* Radius */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">Search Radius</label>
          <div className="flex gap-2 flex-wrap">
            {RADIUS_OPTIONS.map(r => (
              <button
                key={r}
                id={`radius-${r}km`}
                onClick={() => setRadiusKm(r)}
                className={`px-4 py-1.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                  radiusKm === r
                    ? 'border-primary-500/70 bg-primary-900/30 text-white'
                    : 'border-surface-700/40 bg-surface-800/40 text-gray-400 hover:text-white'
                }`}
              >
                {r} km
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5">
            {error}
          </div>
        )}

        <button
          id="run-market-analysis-btn"
          onClick={runAnalysis}
          disabled={loading || !selectedBizId || !selectedLat}
          className="btn-primary px-8 py-2.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing Market…
            </>
          ) : '🗺️ Analyze Market'}
        </button>
      </div>

      {/* ── Interactive Map ── */}
      <div className="card overflow-hidden" style={{ height: 420 }}>
        <MapContainer
          key={mapKey}
          center={mapCenter}
          zoom={selectedLat ? 13 : 5}
          style={{ width: '100%', height: '100%' }}
          className="rounded-xl"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler />

          {selectedLat && selectedLon && (
            <>
              <FlyTo lat={selectedLat} lng={selectedLon} />
              {/* Search radius circle */}
              <Circle
                center={[selectedLat, selectedLon]}
                radius={radiusKm * 1000}
                pathOptions={{ color: '#a78bfa', fillColor: '#a78bfa', fillOpacity: 0.07, weight: 1.5 }}
              />
              {/* Centre pin */}
              <Marker position={[selectedLat, selectedLon]} icon={PIN_CENTER}>
                <Popup>
                  <strong>📍 Selected Location</strong><br />
                  {locationLabel || `${selectedLat.toFixed(4)}, ${selectedLon.toFixed(4)}`}
                </Popup>
              </Marker>
            </>
          )}

          {/* Competitor markers */}
          {analysis?.direct_competitors.map(p => (
            <Marker key={`comp-${p.osm_id}`} position={[p.latitude, p.longitude]} icon={PIN_COMPETITOR}>
              <Popup>
                <strong>⚠️ {p.name}</strong><br />
                {p.category}<br />
                <span className="text-red-500">Direct competitor</span><br />
                {(p.distance_meters / 1000).toFixed(2)} km away
              </Popup>
            </Marker>
          ))}

          {/* Other nearby places (non-competitors) */}
          {analysis?.nearby_places
            .filter(p => !competitorIds.has(p.osm_id))
            .slice(0, 80)
            .map(p => (
              <Marker key={`place-${p.osm_id}`} position={[p.latitude, p.longitude]} icon={PIN_PLACE}>
                <Popup>
                  <strong>🏪 {p.name}</strong><br />
                  {p.category}<br />
                  {(p.distance_meters / 1000).toFixed(2)} km away
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </div>

      {/* ── Legend ── */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-400">
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-violet-500" />Selected location</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500" />Direct competitors</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500" />Other businesses</div>
        <div className="flex items-center gap-1.5"><span className="w-6 h-1 rounded bg-violet-500/40 border border-violet-500" />Search radius</div>
      </div>

      {/* ── Results ─────────────────────────────────────────────────────────── */}
      {analysis && (
        <>
          {/* ── Location Summary ── */}
          {analysis.location_name && (
            <div className="card p-4 bg-gradient-to-r from-primary-900/20 to-transparent">
              <p className="text-xs text-gray-500 mb-1">📍 Analyzed Location</p>
              <p className="text-white font-semibold text-sm">
                {analysis.location_name.split(',').slice(0, 4).join(', ')}
              </p>
              <p className="text-gray-600 text-xs mt-0.5">
                {analysis.latitude.toFixed(5)}, {analysis.longitude.toFixed(5)} · Radius: {analysis.radius_km} km
              </p>
            </div>
          )}

          {/* ── Score Row ── */}
          <div id="score-panel" className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-5 col-span-1 flex flex-col items-center justify-center gap-1">
              <ScoreRing score={analysis.opportunity.total} label="Market Opportunity" color="#a78bfa" size={96} />
            </div>
            <div className="card p-5 col-span-1 flex flex-col items-center justify-center gap-1">
              <ScoreRing score={analysis.suitability.total} label="Location Suitability" color="#34d399" size={96} />
            </div>
            <div className="card p-5 col-span-1 flex flex-col items-center justify-center gap-2 text-center">
              <p className="text-xs text-gray-500">Direct Competitors</p>
              <p className="text-3xl font-bold text-white">{analysis.competitor_summary.direct_count}</p>
              <CompBadge level={analysis.competitor_summary.competition_level} />
            </div>
            <div className="card p-5 col-span-1 flex flex-col items-center justify-center gap-2 text-center">
              <p className="text-xs text-gray-500">Businesses Nearby</p>
              <p className="text-3xl font-bold text-white">{analysis.competitor_summary.total_businesses}</p>
              <p className="text-xs text-gray-600">{analysis.radius_km} km radius</p>
            </div>
          </div>

          {/* ── Score Breakdowns ── */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Opportunity Breakdown */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-300 mb-1">📊 Market Opportunity Breakdown</h3>
              <p className="text-xs text-gray-600 mb-4">How attractive is this market for the selected business?</p>
              <ScoreBar label="Competition Factor"  value={analysis.opportunity.competition_score}    max={30} color="#a78bfa" />
              <ScoreBar label="Infrastructure"      value={analysis.opportunity.infrastructure_score} max={25} color="#38bdf8" />
              <ScoreBar label="Accessibility"       value={analysis.opportunity.accessibility_score}  max={20} color="#34d399" />
              <ScoreBar label="Business Diversity"  value={analysis.opportunity.diversity_score}      max={15} color="#fb923c" />
              <ScoreBar label="Market Size"         value={analysis.opportunity.market_size_score}    max={10} color="#facc15" />
              <div className="mt-3 pt-3 border-t border-surface-700/30 flex justify-between items-center">
                <span className="text-xs text-gray-500">Total Score</span>
                <span className="text-lg font-bold text-white">{analysis.opportunity.total.toFixed(1)} / 100</span>
              </div>
            </div>

            {/* Suitability Breakdown */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-300 mb-1">📍 Location Suitability Breakdown</h3>
              <p className="text-xs text-gray-600 mb-4">How physically suitable is this location for the business?</p>
              <ScoreBar label="Competition Factor"  value={analysis.suitability.competition_score}    max={25} color="#a78bfa" />
              <ScoreBar label="Infrastructure"      value={analysis.suitability.infrastructure_score} max={30} color="#38bdf8" />
              <ScoreBar label="Customer Footfall"   value={analysis.suitability.customer_proxy_score} max={25} color="#34d399" />
              <ScoreBar label="Business Density"    value={analysis.suitability.business_density}     max={20} color="#fb923c" />
              <div className="mt-3 pt-3 border-t border-surface-700/30 flex justify-between items-center">
                <span className="text-xs text-gray-500">Total Score</span>
                <span className="text-lg font-bold text-white">{analysis.suitability.total.toFixed(1)} / 100</span>
              </div>
            </div>
          </div>

          {/* ── Nearby Businesses ── */}
          {analysis.nearby_places.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-4 border-b border-surface-700/30 flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-gray-300">
                    🏪 Nearby Businesses ({analysis.nearby_places.length})
                  </h3>
                </div>
                {/* Category filter */}
                <div className="flex gap-1.5 flex-wrap">
                  {categories.slice(0, 6).map(cat => (
                    <button
                      key={cat}
                      onClick={() => setCatFilter(cat)}
                      className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                        catFilter === cat
                          ? 'border-primary-500/70 bg-primary-900/30 text-primary-300'
                          : 'border-surface-700/40 text-gray-500 hover:text-white hover:border-surface-600'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {filteredPlaces.length === 0 ? (
                  <p className="text-center text-gray-500 text-sm py-6">No businesses in this category.</p>
                ) : (
                  <table className="w-full text-sm">
                    <tbody>
                      {filteredPlaces.slice(0, 60).map(place => {
                        const isComp = competitorIds.has(place.osm_id)
                        return (
                          <tr
                            key={place.osm_id}
                            className={`border-b border-surface-700/20 hover:bg-surface-700/20 transition-colors ${
                              isComp ? 'bg-red-900/10' : ''
                            }`}
                          >
                            <td className="px-4 py-2.5">
                              <div className="flex items-center gap-2">
                                <span
                                  className="w-2 h-2 rounded-full shrink-0"
                                  style={{ background: isComp ? '#f87171' : (CATEGORY_DOT[place.category] ?? '#64748b') }}
                                />
                                <span className="font-medium text-white">{place.name}</span>
                                {isComp && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/40 text-red-300 border border-red-700/30">Competitor</span>}
                              </div>
                            </td>
                            <td className="px-4 py-2.5 text-gray-500 text-xs">{place.category}</td>
                            <td className="px-4 py-2.5 text-right text-gray-600 text-xs">
                              {(place.distance_meters / 1000).toFixed(2)} km
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* ── Insights ── */}
          {analysis.insights.length > 0 && (
            <div className="card p-5 space-y-2">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">💡 Market Insights</h3>
              <div className="space-y-2">
                {analysis.insights.map((ins, i) => (
                  <InsightRow key={i} insight={ins} />
                ))}
              </div>
            </div>
          )}

          {/* ── Recommendations ── */}
          {analysis.recommendations.length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">🎯 Recommendations</h3>
              <ul className="space-y-2.5">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-primary-400 mt-0.5 shrink-0">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* ── Disclaimer ── */}
          <div className="rounded-xl bg-amber-900/10 border border-amber-700/20 px-5 py-4">
            <p className="text-xs text-amber-600/80">
              ⚠️ <strong>Disclaimer:</strong> {analysis.disclaimer}
            </p>
          </div>
        </>
      )}

      {/* ── Empty state ── */}
      {!analysis && !loading && (
        <div className="card p-10 text-center text-gray-500">
          <div className="text-5xl mb-4">🗺️</div>
          <p className="text-lg font-semibold text-gray-400 mb-2">Ready for Market Analysis</p>
          <p className="text-sm">
            Select a business, search for a location (or click the map), choose your radius,
            and click <strong className="text-white">Analyze Market</strong>.
          </p>
        </div>
      )}
    </div>
  )
}
