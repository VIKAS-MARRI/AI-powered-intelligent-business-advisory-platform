/**
 * Phase 11 — Section 13: System Architecture Page (/architecture)
 * Visual diagram of the RuralBiz AI system for hackathon judges.
 */
import { useNavigate } from 'react-router-dom'

// ── Layer definitions ─────────────────────────────────────────────────────────

const FRONTEND_LAYERS = [
  { icon: '⚛️',  label: 'React 18 + TypeScript', note: 'Vite build system' },
  { icon: '🎨',  label: 'Tailwind CSS',           note: 'Custom design system' },
  { icon: '🌐',  label: 'react-i18next',          note: 'en / hi / te' },
  { icon: '🎙️',  label: 'Web Speech API',         note: 'Voice input + TTS' },
  { icon: '🧭',  label: 'React Router v6',        note: 'Client-side routing' },
]

const BACKEND_SERVICES = [
  { icon: '🐍',  label: 'FastAPI',               note: 'Async REST API', phase: '1' },
  { icon: '🔐',  label: 'JWT Auth',              note: 'bcrypt + HS256', phase: '1' },
  { icon: '💼',  label: 'Recommendation Engine', note: 'Weighted scoring', phase: '2' },
  { icon: '📊',  label: 'Financial Intelligence', note: 'ROI, break-even, CF', phase: '3' },
  { icon: '⚡',  label: 'OR-Tools Optimizer',    note: 'ILP portfolio opt.', phase: '4' },
  { icon: '🗺️',  label: 'Market Intelligence',   note: 'OSM + Overpass', phase: '5' },
  { icon: '🏛️',  label: 'Scheme Matcher',        note: 'PMEGP, MUDRA…', phase: '6' },
  { icon: '🤖',  label: 'LangGraph AI Graph',    note: '4 agents + synth', phase: '7' },
  { icon: '📋',  label: 'Personalization Engine', note: 'Semantic matching', phase: '8' },
  { icon: '📈',  label: 'Analytics Engine',      note: 'Goals, progress', phase: '9' },
  { icon: '🌍',  label: 'Translation Service',   note: 'Fallback + Gemini', phase: '10' },
]

const EXTERNAL_SERVICES = [
  { icon: '🧠',  label: 'Gemini 1.5 Flash',     type: 'AI',   note: 'Optional — fallback exists' },
  { icon: '🗺️',  label: 'OpenStreetMap',         type: 'Maps', note: 'Free, open data' },
  { icon: '🌐',  label: 'Overpass API',          type: 'Maps', note: 'POI queries' },
  { icon: '⚙️',  label: 'OR-Tools (Google)',     type: 'Opt',  note: 'Local, no API key' },
]

const AGENTS = [
  { icon: '💼', label: 'Business Agent',   color: 'text-primary-400',  note: 'Ideas, scoring' },
  { icon: '📊', label: 'Finance Agent',    color: 'text-emerald-400',  note: 'ROI, break-even' },
  { icon: '🗺️', label: 'Market Agent',    color: 'text-teal-400',     note: 'Competition, OSM' },
  { icon: '🏛️', label: 'Scheme Agent',    color: 'text-indigo-400',   note: 'PMEGP, MUDRA' },
  { icon: '🧠', label: 'Synthesizer',     color: 'text-violet-400',   note: 'Final action plan' },
]

const DATA_FLOW = [
  'User submits question',
  'Supervisor routes to agents',
  'Agents run in parallel',
  'Synthesizer merges results',
  'Translated & voiced response',
]

export default function Architecture() {
  const navigate = useNavigate()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">

      {/* ── Header ── */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <button onClick={() => navigate('/demo')} className="text-gray-500 hover:text-gray-300 text-sm transition-colors">
            ← Demo Dashboard
          </button>
        </div>
        <h1 className="text-3xl font-display font-bold text-white mb-2">
          🏗️ System Architecture
        </h1>
        <p className="text-gray-400">
          RuralBiz AI internal architecture — designed for hackathon judges and technical reviewers.
        </p>
      </div>

      {/* ── Main Architecture Diagram ── */}
      <div className="space-y-4 mb-10">

        {/* Frontend */}
        <div className="rounded-2xl bg-primary-900/20 border border-primary-700/30 p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xl">🖥️</span>
            <h2 className="font-display font-bold text-primary-300">Frontend Layer</h2>
            <span className="text-xs text-gray-600 ml-auto">React + TypeScript + Vite</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {FRONTEND_LAYERS.map(f => (
              <div key={f.label} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-primary-900/40 border border-primary-800/30">
                <span>{f.icon}</span>
                <div>
                  <div className="text-sm text-white font-medium">{f.label}</div>
                  <div className="text-[10px] text-gray-500">{f.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Arrow down */}
        <div className="flex justify-center text-gray-600 text-xl">↕</div>

        {/* API Gateway */}
        <div className="rounded-2xl bg-surface-800/60 border border-surface-600/30 p-4">
          <div className="flex items-center justify-center gap-3">
            <span className="text-xl">🔐</span>
            <div className="text-center">
              <div className="font-semibold text-white">FastAPI Gateway + JWT Authentication</div>
              <div className="text-xs text-gray-500">CORS · Rate limiting · Security headers · Request IDs · Error handling</div>
            </div>
          </div>
        </div>

        {/* Arrow down */}
        <div className="flex justify-center text-gray-600 text-xl">↕</div>

        {/* Backend Services Grid */}
        <div className="rounded-2xl bg-surface-800/40 border border-surface-700/30 p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xl">⚙️</span>
            <h2 className="font-display font-bold text-white">Internal RuralBiz AI Services</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {BACKEND_SERVICES.map(s => (
              <div key={s.label} className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-surface-700/30 border border-surface-600/20">
                <span className="text-lg mt-0.5">{s.icon}</span>
                <div>
                  <div className="text-xs font-semibold text-white">{s.label}</div>
                  <div className="text-[10px] text-gray-500">{s.note}</div>
                  <div className="text-[9px] text-primary-600 mt-0.5">Phase {s.phase}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Arrow down */}
        <div className="flex justify-center text-gray-600 text-xl">↕</div>

        {/* Database */}
        <div className="rounded-2xl bg-surface-800/60 border border-surface-600/30 p-4">
          <div className="flex items-center justify-center gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🗄️</span>
              <div>
                <div className="text-sm font-semibold text-white">SQLite (dev) / PostgreSQL (prod)</div>
                <div className="text-xs text-gray-500">SQLAlchemy async ORM · Alembic migrations</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Multi-Agent AI System ── */}
      <div className="mb-10">
        <h2 className="text-xl font-display font-bold text-white mb-2">🤖 Multi-Agent AI Advisory System</h2>
        <p className="text-sm text-gray-400 mb-4">Phase 7 — LangGraph orchestrated workflow</p>

        <div className="rounded-2xl bg-violet-900/15 border border-violet-700/25 p-5">
          {/* Data flow */}
          <div className="flex items-center gap-2 flex-wrap mb-5">
            {DATA_FLOW.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <div className="text-xs px-2.5 py-1 rounded-full bg-violet-900/40 text-violet-300 border border-violet-800/30">
                  {i + 1}. {step}
                </div>
                {i < DATA_FLOW.length - 1 && <span className="text-gray-600">→</span>}
              </div>
            ))}
          </div>

          {/* Agent cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {AGENTS.map((a, i) => (
              <div key={a.label}
                className={`rounded-xl bg-surface-800/60 border border-surface-600/30 p-3 text-center ${i === 4 ? 'sm:col-span-1 ring-1 ring-violet-600/30' : ''}`}>
                <div className="text-2xl mb-1.5">{a.icon}</div>
                <div className={`text-xs font-semibold mb-0.5 ${a.color}`}>{a.label}</div>
                <div className="text-[10px] text-gray-500">{a.note}</div>
                {i === 4 && <div className="text-[9px] text-violet-500 mt-1">★ Synthesizer</div>}
              </div>
            ))}
          </div>

          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              🔌 <strong className="text-gray-400">Fallback mode:</strong> All agents produce structured results
              using deterministic algorithms when Gemini is unavailable.
            </p>
          </div>
        </div>
      </div>

      {/* ── External Services ── */}
      <div className="mb-10">
        <h2 className="text-xl font-display font-bold text-white mb-2">🌐 External Services</h2>
        <p className="text-sm text-gray-400 mb-4">
          All external services degrade gracefully — the app works offline
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {EXTERNAL_SERVICES.map(e => (
            <div key={e.label} className="rounded-2xl bg-surface-800/40 border border-surface-700/30 p-4 text-center">
              <div className="text-3xl mb-2">{e.icon}</div>
              <div className="text-sm font-semibold text-white mb-1">{e.label}</div>
              <div className="text-[10px] text-gray-500 mb-2">{e.note}</div>
              <div className="text-[10px] px-2 py-0.5 rounded-full bg-surface-700/40 text-gray-600">{e.type}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Security & Production ── */}
      <div className="mb-8">
        <h2 className="text-xl font-display font-bold text-white mb-4">🔒 Production Readiness (Phase 11)</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { icon: '🛡️', title: 'Security Headers',    desc: 'X-Frame-Options, CSP, HSTS, XSS-Protection' },
            { icon: '⏱️', title: 'Rate Limiting',       desc: 'slowapi — configurable per endpoint' },
            { icon: '📋', title: 'Structured Logging',  desc: 'JSON in prod, colored in dev' },
            { icon: '🏥', title: 'Health Probes',       desc: '/health/live + /health/ready + /health/details' },
            { icon: '🐳', title: 'Docker Ready',        desc: 'Multi-stage builds, compose, PostgreSQL' },
            { icon: '🔍', title: 'Request Tracing',     desc: 'X-Request-ID on every response' },
          ].map(p => (
            <div key={p.title} className="rounded-xl bg-surface-800/40 border border-surface-700/30 p-4">
              <div className="text-xl mb-1.5">{p.icon}</div>
              <div className="text-sm font-semibold text-white mb-1">{p.title}</div>
              <div className="text-xs text-gray-500">{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Back links */}
      <div className="flex flex-wrap gap-3 justify-center">
        <button onClick={() => navigate('/demo')} className="btn-primary px-6 py-2.5">← Demo Dashboard</button>
        <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="btn-ghost px-6 py-2.5">📖 API Docs</a>
        <button onClick={() => navigate('/dashboard')} className="btn-ghost px-6 py-2.5">📊 Dashboard</button>
      </div>
    </div>
  )
}
