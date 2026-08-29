import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../services/api'

export interface DemoProfile {
  id: string
  name: string
  scenario?: string
  available_capital?: number
  skills?: string
  business_interests?: string
  state?: string
  monthly_income_goal?: number
}

export default function useDemo() {
  const loc = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(loc.search)
  const demoId = params.get('demo_profile')
  const [demoProfile, setDemoProfile] = useState<DemoProfile | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!demoId) {
      setDemoProfile(null)
      return
    }
    setLoading(true)
    api.get('/demo/profiles')
      .then(r => {
        const list: DemoProfile[] = r.data.profiles || []
        const found = list.find(p => p.id === demoId) ?? null
        setDemoProfile(found)
      })
      .catch(() => setDemoProfile(null))
      .finally(() => setLoading(false))
  }, [demoId])

  const exitDemo = () => {
    const p = new URLSearchParams(loc.search)
    p.delete('demo_profile')
    p.delete('autoplay')
    navigate({ pathname: loc.pathname, search: p.toString() }, { replace: true })
  }

  return { demoProfile, loading, isDemo: !!demoProfile, exitDemo }
}
