/**
 * Phase 11 — Section 12: Hackathon Demo Dashboard (/demo)
 * Live demonstration of the complete RuralBiz AI workflow.
 * Links to real working features — no fake functionality.
 */
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DemoScenarios from '../components/DemoScenarios'
import DemoWalkthrough from '../components/DemoWalkthrough'

// ── Workflow Steps ─────────────────────────────────────────────────────────────

const WORKFLOW = [
  {
    step:    1,
    icon:    '👤',
    title:   'Entrepreneur Profile',
    desc:    'Set capital, skills, location, income goals',
    route:   '/profile',
    color:   'from-primary-600 to-primary-800',
    badge:   'Phase 1',
  },
  {
    step:    2,
    icon:    '💼',
    title:   'AI Business Recommendations',
    desc:    'Personalized, scored recommendations using Phase 2 engine',
    route:   '/recommendations',
    color:   'from-emerald-600 to-emerald-800',
    badge:   'Phase 2',
  },
  {
    step:    3,
    icon:    '📊',
    title:   'Financial Analysis',
    desc:    'ROI, break-even, cash flow, monthly projections',
    route:   '/financial-analysis',
    color:   'from-teal-600 to-teal-800',
    badge:   'Phase 3',
  },
  {
    step:    4,
    icon:    '⚡',
    title:   'Investment Optimization',
    desc:    'OR-Tools portfolio optimizer for best capital allocation',
    route:   '/investment-optimizer',
    color:   'from-yellow-600 to-yellow-800',
    badge:   'Phase 4',
  },
  {
    step:    5,
    icon:    '🗺️',
    title:   'Market Intelligence',
    desc:    'Hyper-local competitor analysis via OpenStreetMap + Overpass',
    route:   '/market-intelligence',
    color:   'from-cyan-600 to-cyan-800',
    badge:   'Phase 5',
  },
  {
    step:    6,
    icon:    '🏛️',
    title:   'Government Scheme Matching',
    desc:    'PMEGP, MUDRA, PMFME — automated eligibility scoring',
    route:   '/scheme-support',
    color:   'from-indigo-600 to-indigo-800',
    badge:   'Phase 6',
  },
  {
    step:    7,
    icon:    '🤖',
    title:   'Multi-Agent AI Advisor',
    desc:    'LangGraph + Gemini: 4 specialists synthesize your action plan',
    route:   '/advisor',
    color:   'from-violet-600 to-violet-800',
    badge:   'Phase 7',
  },
  {
    step:    8,
    icon:    '📋',
    title:   'Personalized Action Plan',
    desc:    'Step-by-step roadmap — risks, next steps, resources',
    route:   '/advisor',
    color:   'from-rose-600 to-rose-800',
    badge:   'Phase 8',
  },
  {
    step:    9,
    icon:    '📈',
    title:   'Analytics & Goal Tracking',
    desc:    'Track milestones, progress, and entrepreneur growth',
    route:   '/analytics',
    color:   'from-orange-600 to-orange-800',
    badge:   'Phase 9',
  },
  {
    step:    10,
    icon:    '🌐',
    title:   'Multilingual + Voice',
    desc:    'English, Hindi, Telugu — voice input and TTS',
    route:   '/advisor',
    color:   'from-pink-600 to-pink-800',
    badge:   'Phase 10',
  },
]

// ── Tech Stack ────────────────────────────────────────────────────────────────

const TECH = [
  { icon: '⚛️',  label: 'React + TypeScript',   category: 'Frontend'   },
  { icon: '⚡',  label: 'Vite + Tailwind CSS',   category: 'Frontend'   },
  { icon: '🐍',  label: 'FastAPI + SQLAlchemy',  category: 'Backend'    },
  { icon: '🤖',  label: 'Gemini 1.5 Flash',      category: 'AI'         },
  { icon: '🕸️',  label: 'LangGraph',             category: 'AI'         },
  { icon: '🗺️',  label: 'OpenStreetMap + Overpass', category: 'Maps'   },
  { icon: '⚙️',  label: 'OR-Tools (Google)',      category: 'Optimizer'  },
  { icon: '🗄️',  label: 'SQLite / PostgreSQL',   category: 'Database'   },
  { icon: '🔐',  label: 'JWT Auth',               category: 'Security'   },
  { icon: '🌍',  label: 'i18next (en/hi/te)',     category: 'I18n'       },
]

export default function Demo() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
      {/* ── Hero ── */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-900/40 border border-primary-700/30 text-primary-400 text-sm font-medium mb-6">
          🏆 Hackathon Demo Dashboard
        </div>
        <h1 className="text-4xl sm:text-5xl font-display font-bold text-white mb-4">
          RuralBiz <span className="text-primary-400">AI</span>
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed mb-6">
          AI-powered business advisory for rural micro-entrepreneurs in India.
          Multilingual, voice-enabled, fully offline-fallback.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {!isAuthenticated ? (
            <>
              <button onClick={() => navigate('/register')} className="btn-primary px-8 py-3 text-base">
                🚀 Try Live Demo
              </button>
              <button onClick={() => navigate('/login')} className="btn-ghost px-8 py-3 text-base">
                Sign In
              </button>
            </>
          ) : (
            <button onClick={() => navigate('/dashboard')} className="btn-primary px-8 py-3 text-base">
              📊 Open Dashboard
            </button>
          )}
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
            className="btn-ghost px-6 py-3 text-base">
            📖 API Docs
          </a>
          <button onClick={() => navigate('/architecture')} className="btn-ghost px-6 py-3 text-base">
            🏗️ Architecture
          </button>
        </div>
      </div>

      {/* ── Demo Scenarios ── */}
      <div className="card p-6 mb-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <DemoScenarios />
          </div>
          <div className="lg:col-span-1">
            <DemoWalkthrough />
          </div>
        </div>
      </div>

      {/* ── Complete Workflow ── */}
      <div className="mb-10">
        <h2 className="text-xl font-display font-bold text-white mb-2">
          📋 Complete RuralBiz AI Workflow
        </h2>
        <p className="text-sm text-gray-400 mb-6">
          Every card below links to a live, working feature
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {WORKFLOW.map((w, i) => (
            <button
              key={w.step}
              id={`workflow-step-${w.step}`}
              onClick={() => navigate(isAuthenticated ? w.route : '/register')}
              className="group relative text-left rounded-2xl bg-surface-800/60 hover:bg-surface-700/60 border border-surface-700/30 hover:border-surface-600/50 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-glow-sm"
            >
              {/* Connector arrow — hidden on mobile */}
              {i < WORKFLOW.length - 1 && (
                <span className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 text-gray-700 text-sm z-10">
                  →
                </span>
              )}
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${w.color} flex items-center justify-center text-sm mb-3 group-hover:scale-110 transition-transform duration-200`}>
                {w.icon}
              </div>
              <div className="text-[10px] text-gray-600 mb-1">{w.badge}</div>
              <div className="text-sm font-semibold text-white mb-1 leading-tight">{w.title}</div>
              <div className="text-[11px] text-gray-400 leading-relaxed line-clamp-2">{w.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Key Differentiators ── */}
      <div className="grid sm:grid-cols-3 gap-4 mb-10">
        {[
          { icon: '🔌', title: 'Works Without AI Key', desc: 'Full deterministic fallback mode — no Gemini API key required for demo', color: 'border-primary-800/40 bg-primary-900/10' },
          { icon: '🌐', title: 'Multilingual & Voice', desc: 'English, Hindi, Telugu with voice input and text-to-speech', color: 'border-emerald-800/40 bg-emerald-900/10' },
          { icon: '🗺️', title: 'Real Map Data', desc: 'Live hyper-local intelligence using OpenStreetMap & Overpass API', color: 'border-teal-800/40 bg-teal-900/10' },
        ].map(d => (
          <div key={d.title} className={`rounded-2xl border p-5 ${d.color}`}>
            <div className="text-3xl mb-3">{d.icon}</div>
            <h3 className="font-semibold text-white mb-2">{d.title}</h3>
            <p className="text-sm text-gray-400">{d.desc}</p>
          </div>
        ))}
      </div>

      {/* ── Tech Stack ── */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-display font-bold text-white mb-4">🛠️ Technology Stack</h2>
        <div className="flex flex-wrap gap-2">
          {TECH.map(t => (
            <div key={t.label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-700/40 border border-surface-600/30 text-sm text-gray-300"
              title={t.category}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
              <span className="text-[9px] text-gray-600 ml-1">{t.category}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { value: '10',   label: 'Phases', icon: '🎯' },
          { value: '574+', label: 'Tests',  icon: '✅' },
          { value: '3',    label: 'Languages', icon: '🌐' },
          { value: '100%', label: 'Fallback Coverage', icon: '🔌' },
        ].map(s => (
          <div key={s.label} className="card p-4 text-center">
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="text-2xl font-display font-bold text-primary-400">{s.value}</div>
            <div className="text-xs text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="rounded-xl bg-surface-800/40 border border-surface-700/20 p-4 text-center">
        <p className="text-xs text-gray-500">
          💡 RuralBiz AI provides AI-assisted guidance for planning purposes only.
          Always verify financial, legal, and government scheme information through official sources.
        </p>
      </div>
    </div>
  )
}
