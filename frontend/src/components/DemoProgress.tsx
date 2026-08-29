import { } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import useDemo from '../hooks/useDemo'

const ROUTE_ORDER = [
  '/recommendations',
  '/financial-analysis',
  '/investment-optimizer',
  '/market-intelligence',
  '/scheme-support',
  '/advisor',
  '/demo/final',
]

export default function DemoProgress() {
  const { demoProfile } = useDemo()
  const loc = useLocation()
  const navigate = useNavigate()
  // URLSearchParams can be created ad-hoc where needed; avoid unused memo
  const qp = (name: string, val?: string) => {
    const p = new URLSearchParams(loc.search)
    if (val === undefined) p.delete(name)
    else p.set(name, val)
    return `?${p.toString()}`
  }

  if (!demoProfile) return null

  const path = loc.pathname
  const idx = ROUTE_ORDER.indexOf(path)
  const step = idx >= 0 ? idx + 1 : 0

  const goTo = (i: number) => {
    const route = ROUTE_ORDER[i] || '/recommendations'
    navigate(route + qp('demo_profile', demoProfile.id))
  }

  return (
    <div className="flex items-center gap-3">
      <div className="text-sm text-gray-300">Step {step || 1} of {ROUTE_ORDER.length}</div>
      <div className="inline-flex items-center gap-2">
        <button aria-label="Previous step" onClick={() => goTo(Math.max(0, (idx === -1 ? 0 : idx) - 1))} className="btn-ghost px-3 py-1">Previous</button>
        <button aria-label="Next step" onClick={() => goTo(Math.min(ROUTE_ORDER.length - 1, (idx === -1 ? 0 : idx) + 1))} className="btn-primary px-3 py-1">Next</button>
        <button aria-label="Restart demo" onClick={() => navigate('/demo' + qp('demo_profile', demoProfile.id))} className="btn-outline px-3 py-1">Restart Demo</button>
        <button aria-label="Exit demo" onClick={() => navigate('/' )} className="btn-ghost px-3 py-1">Exit Demo</button>
      </div>
    </div>
  )
}
