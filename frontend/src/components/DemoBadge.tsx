import useDemo from '../hooks/useDemo'

export default function DemoBadge() {
  const { demoProfile, isDemo, exitDemo } = useDemo()
  if (!isDemo || !demoProfile) return null
  return (
    <div className="fixed right-4 top-20 z-50 flex items-center gap-3 bg-amber-900/20 border border-amber-700/30 px-3 py-2 rounded-lg">
      <div className="text-xs text-amber-200 font-semibold">DEMO MODE</div>
      <div className="text-xs text-gray-200">{demoProfile.name}</div>
      <button aria-label="Exit demo" onClick={exitDemo} className="text-xs btn-ghost px-2 py-1">Exit Demo</button>
    </div>
  )
}
