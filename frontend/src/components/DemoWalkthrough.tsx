import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface DemoProfile { id: string; name: string; description?: string; available_capital?: number }
export default function DemoWalkthrough() {
  const [profiles, setProfiles] = useState<DemoProfile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null)
  const [step, setStep] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/demo/profiles').then(r => setProfiles(r.data.profiles || [])).catch(() => setProfiles([]))
  }, [])

  const steps = [
    { id: 'profile', title: 'Entrepreneur Profile', desc: 'Choose a demo entrepreneur to drive the walkthrough.' },
    { id: 'recommend', title: 'Personalized Recommendation', desc: 'Show the AI recommendation for this profile.' },
    { id: 'finance', title: 'Financial Intelligence', desc: 'Open the financial analysis and projections.' },
    { id: 'investment', title: 'Investment Optimization', desc: 'Run the optimizer to allocate capital.' },
    { id: 'market', title: 'Market Intelligence', desc: 'Show hyper-local market insights.' },
    { id: 'schemes', title: 'Government Scheme Support', desc: 'List matched schemes for the profile.' },
    { id: 'advisor', title: 'AI Business Advisor', desc: 'Ask the multi-agent advisor a question.' },
  ]

  const cur = steps[step]

  const openFeature = (idx: number) => {
    const map = ['','/recommendations','/financial-analysis','/investment-optimizer','/market-intelligence','/scheme-support','/advisor']
    const route = map[idx] || '/recommendations'
    // pass demo profile id as query param for demo-safe rendering
    const qp = selectedProfile ? `?demo_profile=${encodeURIComponent(selectedProfile)}` : ''
    navigate(route + qp)
  }

  const startDemo = () => {
    if (!selectedProfile) return
    // Start demo at recommendations and enable autoplay on pages
    const qp = `?demo_profile=${encodeURIComponent(selectedProfile)}&autoplay=1`
    navigate('/recommendations' + qp)
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">🎬 Guided Demo Walkthrough</h3>
        <div className="text-xs text-gray-400">Demo Mode — uses demo data only</div>
      </div>

      <div className="mb-4">
        <div className="text-sm text-gray-300 mb-2">1. Select a demo entrepreneur</div>
        <div className="flex gap-2 flex-wrap">
          {profiles.length === 0 ? (
            <div className="text-xs text-gray-500">Loading demo profiles…</div>
          ) : profiles.map(p => (
            <button key={p.id} onClick={() => setSelectedProfile(p.id)}
              className={`px-3 py-2 rounded-lg text-sm ${selectedProfile === p.id ? 'bg-primary-700 text-white' : 'bg-surface-800 text-gray-300'}`}>
              {p.name}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <div className="text-sm text-gray-300 mb-2">Step {step + 1} — {cur.title}</div>
        <div className="rounded-lg bg-surface-800/30 p-4 text-sm text-gray-300 mb-3">{cur.desc}</div>

        <div className="flex items-center gap-2">
          <button aria-label="Previous step" onClick={() => setStep(s => Math.max(0, s - 1))} className="btn-ghost px-4 py-2">Previous</button>
          <button aria-label="Next step" onClick={() => setStep(s => Math.min(steps.length - 1, s + 1))} className="btn-primary px-4 py-2">Next</button>
          <div className="ml-auto flex items-center gap-2">
            <button aria-label="Open feature" onClick={() => openFeature(step)} className="btn-outline px-4 py-2">Open Feature →</button>
            <button aria-label="Start demo" onClick={startDemo} className="btn-primary px-4 py-2">Start Demo</button>
          </div>
        </div>
      </div>

      <div className="text-xs text-gray-500">Tip: 'Open Feature' will open the live feature using demo-safe profile query param where supported.</div>
    </div>
  )
}
