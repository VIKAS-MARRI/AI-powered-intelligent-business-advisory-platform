/**
 * Phase 8 — Saved Businesses Page.
 * Shows the user's starred/saved businesses with match data and quick actions.
 */
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { phase8Service } from '../services/phase8Service'
import type { SavedBusinessOut } from '../types/phase8'

// Use basic business info from the saved list + fetch scores on-demand
// For a hackathon demo we display saved metadata and link to analysis pages.

export default function SavedBusinesses() {
  const [items,   setItems]   = useState<SavedBusinessOut[]>([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)
  const [removing, setRemoving] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await phase8Service.getSaved()
      setItems(res.items)
    } catch {
      setError('Failed to load saved businesses.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleRemove = async (businessId: string) => {
    setRemoving(businessId)
    try {
      await phase8Service.deleteSaved(businessId)
      setItems(prev => prev.filter(i => i.business_id !== businessId))
    } catch {
      setError('Failed to remove. Please try again.')
    } finally {
      setRemoving(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            ★ <span className="text-gradient">Saved Businesses</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Your shortlisted opportunities — {items.length} saved
          </p>
        </div>
        <Link to="/recommendations" className="btn-primary text-sm px-4 py-2">
          + Explore More
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="card p-10 text-center">
          <div className="w-8 h-8 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-400">Loading saved businesses…</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="card p-12 text-center text-gray-500">
          <div className="text-5xl mb-4">⭐</div>
          <p className="text-base font-semibold text-gray-400 mb-2">No saved businesses yet</p>
          <p className="text-sm mb-6">
            Explore recommendations and click "☆ Save" to shortlist businesses you like.
          </p>
          <Link to="/recommendations" className="btn-primary text-sm px-6 py-2">
            Explore Recommendations →
          </Link>
        </div>
      )}

      {/* Saved list */}
      {!loading && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item, i) => (
            <div
              key={item.id}
              id={`saved-item-${item.business_id}`}
              className="card p-5 border hover:border-amber-600/30 transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {/* Rank */}
                  <div className="w-7 h-7 rounded-full bg-amber-900/30 border border-amber-700/30 flex items-center justify-center text-xs font-bold text-amber-400 shrink-0">
                    {i + 1}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-amber-400 text-sm">★</span>
                      <h3 className="text-sm font-bold text-white">Saved Business</h3>
                      <span className="text-[10px] text-gray-500">{item.business_id.slice(0, 8)}…</span>
                    </div>
                    {item.notes && (
                      <p className="text-xs text-gray-400 mt-1 italic">"{item.notes}"</p>
                    )}
                    <p className="text-[10px] text-gray-600 mt-1">
                      Saved {new Date(item.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric', month: 'short', year: 'numeric'
                      })}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to={`/recommendations`}
                    className="text-xs text-primary-400 hover:text-primary-300 border border-primary-700/30 px-2.5 py-1.5 rounded-lg hover:border-primary-600 transition-colors"
                  >
                    View Analysis
                  </Link>
                  <Link
                    to={`/financial-analysis?business_id=${item.business_id}`}
                    className="text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-700/30 px-2.5 py-1.5 rounded-lg hover:border-emerald-600 transition-colors"
                  >
                    💰 Finance
                  </Link>
                  <button
                    onClick={() => handleRemove(item.business_id)}
                    disabled={removing === item.business_id}
                    className="text-xs text-red-400 hover:text-red-300 border border-red-700/30 px-2.5 py-1.5 rounded-lg hover:border-red-600 transition-colors disabled:opacity-50"
                  >
                    {removing === item.business_id ? '…' : '✕ Remove'}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Disclaimer */}
          <p className="text-center text-xs text-gray-600 pb-2">
            ⚠️ Saving a business does not constitute financial advice. All figures are estimates.
          </p>
        </div>
      )}
    </div>
  )
}
