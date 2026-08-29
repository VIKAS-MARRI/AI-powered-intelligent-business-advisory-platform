/**
 * Phase 11 — Section 10: One-click Demo Scenarios
 * Guides users/judges to each major feature with pre-filled questions.
 */
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface Scenario {
  id:          string
  icon:        string
  title:       string
  description: string
  route:       string
  feature:     string
  badge:       string
  badgeColor:  string
}

const SCENARIOS: Scenario[] = [
  {
    id:          'find-business',
    icon:        '💡',
    title:       'Find My Business',
    description: 'Get AI-powered personalized business recommendations based on your capital, skills, and location.',
    route:       '/recommendations',
    feature:     'Phase 2 — Recommendation Engine',
    badge:       'AI-Powered',
    badgeColor:  'bg-primary-800/60 text-primary-300',
  },
  {
    id:          'plan-investment',
    icon:        '💰',
    title:       'Plan My Investment',
    description: 'Financial analysis, break-even calculation, and OR-Tools investment optimization.',
    route:       '/investment-optimizer',
    feature:     'Phase 3 + 4 — Financial + OR-Tools',
    badge:       'Optimization',
    badgeColor:  'bg-emerald-900/60 text-emerald-300',
  },
  {
    id:          'analyze-market',
    icon:        '🗺️',
    title:       'Analyze My Market',
    description: 'Hyper-local market intelligence using real OpenStreetMap and Overpass API data.',
    route:       '/market-intelligence',
    feature:     'Phase 5 — OpenStreetMap',
    badge:       'Real Map Data',
    badgeColor:  'bg-teal-900/60 text-teal-300',
  },
  {
    id:          'government-support',
    icon:        '🏛️',
    title:       'Find Government Support',
    description: 'Discover PMEGP, MUDRA, PMFME and other schemes you may qualify for.',
    route:       '/scheme-support',
    feature:     'Phase 6 — Scheme Intelligence',
    badge:       'Schemes',
    badgeColor:  'bg-indigo-900/60 text-indigo-300',
  },
  {
    id:          'ai-advisor',
    icon:        '🤖',
    title:       'Ask AI Advisor',
    description: 'Multi-agent AI advisory system: 4 specialists + synthesizer powered by LangGraph & Gemini.',
    route:       '/advisor',
    feature:     'Phase 7 — LangGraph Multi-Agent',
    badge:       'LangGraph + Gemini',
    badgeColor:  'bg-violet-900/60 text-violet-300',
  },
  {
    id:          'analytics',
    icon:        '📊',
    title:       'Track My Progress',
    description: 'Entrepreneur analytics dashboard: goals, milestones, financial progress tracking.',
    route:       '/analytics',
    feature:     'Phase 9 — Entrepreneur Analytics',
    badge:       'Analytics',
    badgeColor:  'bg-orange-900/60 text-orange-300',
  },
]

interface Props {
  className?: string
  compact?: boolean
}

export default function DemoScenarios({ className = '', compact = false }: Props) {
  const navigate   = useNavigate()
  const { isAuthenticated } = useAuth()

  const handleScenario = (route: string) => {
    if (!isAuthenticated) {
      navigate('/register')
      return
    }
    navigate(route)
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-display font-bold text-white">
            🚀 Quick Demo Scenarios
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            One-click access to every major feature
          </p>
        </div>
        <span className="text-[10px] px-2 py-1 rounded-full bg-primary-900/40 text-primary-400 border border-primary-800/30">
          💡 Demo Data Available
        </span>
      </div>

      {/* Scenario cards */}
      <div className={`grid gap-3 ${compact ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            id={`demo-scenario-${s.id}`}
            onClick={() => handleScenario(s.route)}
            className="group text-left rounded-2xl bg-surface-800/60 hover:bg-surface-700/70 border border-surface-700/30 hover:border-primary-700/40 p-4 transition-all duration-200 hover:shadow-glow-sm hover:-translate-y-0.5"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl group-hover:scale-110 transition-transform duration-200" aria-hidden="true">
                {s.icon}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-sm font-semibold text-white">{s.title}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${s.badgeColor}`}>
                    {s.badge}
                  </span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">
                  {s.description}
                </p>
                <p className="text-[10px] text-gray-600 mt-1.5">{s.feature}</p>
              </div>
              <span className="text-gray-600 group-hover:text-primary-400 transition-colors mt-0.5">→</span>
            </div>
          </button>
        ))}
      </div>

      {!isAuthenticated && (
        <p className="text-center text-xs text-gray-500 mt-4">
          <button onClick={() => navigate('/register')} className="text-primary-400 hover:underline">
            Create a free account
          </button>{' '}
          to access all features
        </p>
      )}
    </div>
  )
}
