/**
 * Phase 9 — Goals Management Page
 * Create, edit, delete, track progress, filter by status/priority
 */
import { useState, useEffect, useCallback } from 'react'
import { goalService } from '../services/analyticsService'
import type { BusinessGoal, GoalCreate, GoalStatus, GoalPriority } from '../types/analytics'

const STATUS_COLORS: Record<GoalStatus, string> = {
  not_started: 'text-slate-400 bg-slate-800/30 border-slate-700/30',
  in_progress: 'text-amber-400 bg-amber-900/20 border-amber-700/30',
  completed:   'text-emerald-400 bg-emerald-900/20 border-emerald-700/30',
  overdue:     'text-red-400 bg-red-900/20 border-red-700/30',
}

const PRIORITY_DOT: Record<GoalPriority, string> = {
  low:    'bg-slate-500',
  medium: 'bg-amber-500',
  high:   'bg-red-500',
}

const GOAL_TYPE_LABELS: Record<string, string> = {
  start_business:        '🚀 Start Business',
  revenue_target:        '💰 Revenue Target',
  profit_target:         '📈 Profit Target',
  savings_capital:       '🏦 Savings Capital',
  apply_scheme:          '🏛️ Apply for Scheme',
  business_registration: '📋 Business Registration',
  improve_skills:        '🎓 Improve Skills',
  reduce_expenses:       '📉 Reduce Expenses',
  customer_growth:       '👥 Customer Growth',
  general:               '🎯 General Goal',
}

// ── Form Component ────────────────────────────────────────────────────────────

function GoalForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: Partial<GoalCreate>
  onSave:   (data: GoalCreate) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState<GoalCreate>({
    title:         initial?.title         ?? '',
    description:   initial?.description   ?? '',
    goal_type:     initial?.goal_type     ?? 'general',
    priority:      initial?.priority      ?? 'medium',
    target_value:  initial?.target_value  ?? undefined,
    current_value: initial?.current_value ?? 0,
    unit:          initial?.unit          ?? '',
    start_date:    initial?.start_date    ?? '',
    target_date:   initial?.target_date   ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) { setError('Title is required'); return }
    setSaving(true); setError(null)
    try {
      const payload: GoalCreate = {
        ...form,
        target_value:  form.target_value  ? Number(form.target_value)  : undefined,
        current_value: form.current_value ? Number(form.current_value) : 0,
        start_date:    form.start_date  || undefined,
        target_date:   form.target_date || undefined,
        unit:          form.unit        || undefined,
        description:   form.description || undefined,
      }
      await onSave(payload)
    } catch {
      setError('Failed to save goal. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const field = (key: keyof GoalCreate) => ({
    value:    form[key]?.toString() ?? '',
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value })),
  })

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-xs text-red-400">{error}</p>}

      <div>
        <label className="block text-xs text-gray-400 mb-1">Goal Title *</label>
        <input {...field('title')} placeholder="e.g. Reach ₹20,000 monthly revenue"
          className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-primary-500/50 focus:outline-none" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Goal Type</label>
          <select {...field('goal_type')}
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none">
            {Object.entries(GOAL_TYPE_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Priority</label>
          <select {...field('priority')}
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Target Value</label>
          <input {...field('target_value')} type="number" min="0" placeholder="e.g. 20000"
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Current Value</label>
          <input {...field('current_value')} type="number" min="0" placeholder="0"
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Unit</label>
          <input {...field('unit')} placeholder="₹, %, customers"
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Start Date</label>
          <input {...field('start_date')} type="date"
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none [color-scheme:dark]" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Target Date</label>
          <input {...field('target_date')} type="date"
            className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none [color-scheme:dark]" />
        </div>
      </div>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Description</label>
        <textarea {...field('description')} rows={2} placeholder="Optional details…"
          className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none resize-none" />
      </div>

      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} className="btn-ghost text-sm px-4 py-2">
          Cancel
        </button>
        <button type="submit" disabled={saving} className="btn-primary text-sm px-5 py-2 disabled:opacity-50">
          {saving ? 'Saving…' : 'Save Goal'}
        </button>
      </div>
    </form>
  )
}

// ── Progress Update Modal ─────────────────────────────────────────────────────

function ProgressModal({
  goal,
  onSave,
  onClose,
}: { goal: BusinessGoal; onSave: (v: number) => Promise<void>; onClose: () => void }) {
  const [value,  setValue]  = useState(goal.current_value ?? 0)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try { await onSave(value) } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={onClose}>
      <div className="card p-6 w-full max-w-sm" onClick={e => e.stopPropagation()}>
        <h3 className="text-sm font-bold text-white mb-4">Update Progress: {goal.title}</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              Current Value {goal.unit ? `(${goal.unit})` : ''}
              {goal.target_value ? ` / ${goal.target_value}` : ''}
            </label>
            <input
              type="number" min="0" value={value}
              onChange={e => setValue(Number(e.target.value))}
              className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none"
            />
          </div>
          {goal.target_value && (
            <div>
              <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                <span>Progress</span>
                <span>{Math.min(100, Math.round((value / goal.target_value) * 100))}%</span>
              </div>
              <div className="h-2 bg-surface-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (value / goal.target_value) * 100)}%` }}
                />
              </div>
            </div>
          )}
          <div className="flex gap-2 justify-end">
            <button onClick={onClose} className="btn-ghost text-sm px-3 py-1.5">Cancel</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary text-sm px-4 py-1.5">
              {saving ? 'Saving…' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Goal Card ─────────────────────────────────────────────────────────────────

function GoalCard({
  goal,
  onEdit,
  onDelete,
  onUpdateProgress,
}: {
  goal: BusinessGoal
  onEdit:           (g: BusinessGoal) => void
  onDelete:         (id: string) => void
  onUpdateProgress: (g: BusinessGoal) => void
}) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (!confirm('Delete this goal?')) return
    setDeleting(true)
    try { onDelete(goal.id) } finally { setDeleting(false) }
  }

  return (
    <div id={`goal-card-${goal.id}`} className={`card p-5 border transition-all duration-200 ${
      goal.is_overdue ? 'border-red-700/30 hover:border-red-600/40' : 'hover:border-surface-600/50'
    }`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <div className={`w-2 h-2 rounded-full shrink-0 ${PRIORITY_DOT[goal.priority]}`} />
            <h3 className="text-sm font-bold text-white">{goal.title}</h3>
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${STATUS_COLORS[goal.status]}`}>
              {goal.status.replace('_', ' ')}
            </span>
            {goal.is_overdue && (
              <span className="text-[10px] text-red-400">⚠ Overdue</span>
            )}
          </div>
          <p className="text-[11px] text-gray-500 mt-0.5">
            {GOAL_TYPE_LABELS[goal.goal_type] ?? goal.goal_type}
          </p>
          {goal.description && (
            <p className="text-[11px] text-gray-400 mt-1">{goal.description}</p>
          )}
        </div>
        <div className="shrink-0 text-center">
          <p className="text-lg font-bold text-white">{goal.progress_percentage}%</p>
          <p className="text-[10px] text-gray-500">complete</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-3">
        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
          <span>
            {goal.current_value !== null ? goal.current_value : '—'}
            {goal.unit ? ` ${goal.unit}` : ''}
          </span>
          <span>
            {goal.target_value !== null ? goal.target_value : 'No target'}
            {goal.unit ? ` ${goal.unit}` : ''}
          </span>
        </div>
        <div className="h-2 bg-surface-700/50 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              goal.is_overdue ? 'bg-red-500' : goal.progress_percentage >= 100 ? 'bg-emerald-500' : 'bg-primary-500'
            }`}
            style={{ width: `${goal.progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Meta */}
      <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-500">
        {goal.target_date && (
          <span>🗓 Target: {new Date(goal.target_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
        )}
        {goal.days_remaining !== null && goal.days_remaining >= 0 && (
          <span>{goal.days_remaining}d remaining</span>
        )}
      </div>

      {/* Actions */}
      <div className="mt-3 flex gap-2 flex-wrap">
        <button
          onClick={() => onUpdateProgress(goal)}
          className="text-[11px] text-emerald-400 border border-emerald-700/30 px-2.5 py-1 rounded-lg hover:border-emerald-600 transition-colors">
          📊 Update Progress
        </button>
        <button
          onClick={() => onEdit(goal)}
          className="text-[11px] text-primary-400 border border-primary-700/30 px-2.5 py-1 rounded-lg hover:border-primary-600 transition-colors">
          ✏️ Edit
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-[11px] text-red-400 border border-red-700/30 px-2.5 py-1 rounded-lg hover:border-red-600 transition-colors disabled:opacity-50">
          {deleting ? '…' : '✕ Delete'}
        </button>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Goals() {
  const [goals,       setGoals]       = useState<BusinessGoal[]>([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState<string | null>(null)
  const [showForm,    setShowForm]    = useState(false)
  const [editGoal,    setEditGoal]    = useState<BusinessGoal | null>(null)
  const [progressGoal, setProgressGoal] = useState<BusinessGoal | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await goalService.list({
        status:   statusFilter   || undefined,
        priority: priorityFilter || undefined,
      })
      setGoals(res.items)
    } catch { setError('Failed to load goals.') }
    finally { setLoading(false) }
  }, [statusFilter, priorityFilter])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data: GoalCreate) => {
    const g = await goalService.create(data)
    setGoals(prev => [g, ...prev])
    setShowForm(false)
  }

  const handleEdit = async (data: GoalCreate) => {
    if (!editGoal) return
    const g = await goalService.update(editGoal.id, data)
    setGoals(prev => prev.map(item => item.id === g.id ? g : item))
    setEditGoal(null)
  }

  const handleDelete = async (id: string) => {
    await goalService.delete(id)
    setGoals(prev => prev.filter(g => g.id !== id))
  }

  const handleProgressSave = async (value: number) => {
    if (!progressGoal) return
    const g = await goalService.updateProgress(progressGoal.id, value)
    setGoals(prev => prev.map(item => item.id === g.id ? g : item))
    setProgressGoal(null)
  }

  const stats = {
    total:      goals.length,
    completed:  goals.filter(g => g.status === 'completed').length,
    overdue:    goals.filter(g => g.is_overdue).length,
    inProgress: goals.filter(g => g.status === 'in_progress').length,
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* Progress modal */}
      {progressGoal && (
        <ProgressModal goal={progressGoal} onSave={handleProgressSave} onClose={() => setProgressGoal(null)} />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            🎯 <span className="text-gradient">Business Goals</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">Track your entrepreneur journey milestones</p>
        </div>
        <button
          id="create-goal-btn"
          onClick={() => { setShowForm(true); setEditGoal(null) }}
          className="btn-primary text-sm px-4 py-2">
          + Create Goal
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: 'Total',       value: stats.total,      color: 'text-white' },
          { label: 'Completed',   value: stats.completed,  color: 'text-emerald-400' },
          { label: 'In Progress', value: stats.inProgress, color: 'text-amber-400' },
          { label: 'Overdue',     value: stats.overdue,    color: 'text-red-400' },
        ].map(s => (
          <div key={s.label} className="card p-3 text-center">
            <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-gray-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Create / Edit Form */}
      {(showForm || editGoal) && (
        <div className="card p-5">
          <h2 className="text-sm font-bold text-white mb-4">
            {editGoal ? '✏️ Edit Goal' : '+ New Goal'}
          </h2>
          <GoalForm
            initial={editGoal ? {
              title:         editGoal.title,
              description:   editGoal.description ?? undefined,
              goal_type:     editGoal.goal_type as GoalCreate['goal_type'],
              priority:      editGoal.priority as GoalCreate['priority'],
              target_value:  editGoal.target_value  ?? undefined,
              current_value: editGoal.current_value ?? undefined,
              unit:          editGoal.unit          ?? undefined,
              start_date:    editGoal.start_date    ?? undefined,
              target_date:   editGoal.target_date   ?? undefined,
            } : undefined}
            onSave={editGoal ? handleEdit : handleCreate}
            onCancel={() => { setShowForm(false); setEditGoal(null) }}
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-surface-700/30 border border-surface-600/40 text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none">
          <option value="">All Status</option>
          <option value="not_started">Not Started</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="overdue">Overdue</option>
        </select>
        <select
          value={priorityFilter}
          onChange={e => setPriorityFilter(e.target.value)}
          className="bg-surface-700/30 border border-surface-600/40 text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none">
          <option value="">All Priority</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        {(statusFilter || priorityFilter) && (
          <button
            onClick={() => { setStatusFilter(''); setPriorityFilter('') }}
            className="text-xs text-gray-500 hover:text-white transition-colors">
            ✕ Clear
          </button>
        )}
      </div>

      {/* Error */}
      {error && <p className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">{error}</p>}

      {/* Loading */}
      {loading && (
        <div className="card p-8 text-center">
          <div className="w-8 h-8 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-400">Loading goals…</p>
        </div>
      )}

      {/* Goals list */}
      {!loading && goals.length === 0 ? (
        <div className="card p-12 text-center text-gray-500">
          <div className="text-5xl mb-4">🎯</div>
          <p className="text-base font-semibold text-gray-400 mb-2">No goals yet</p>
          <p className="text-sm mb-6">Create your first business goal to start tracking your journey.</p>
          <button onClick={() => setShowForm(true)} className="btn-primary text-sm px-5 py-2">
            Create Your First Goal
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {goals.map(g => (
            <GoalCard
              key={g.id}
              goal={g}
              onEdit={goal => {
            setEditGoal(goal)
            setShowForm(false)
          }}
              onDelete={handleDelete}
              onUpdateProgress={setProgressGoal}
            />
          ))}
        </div>
      )}
    </div>
  )
}
