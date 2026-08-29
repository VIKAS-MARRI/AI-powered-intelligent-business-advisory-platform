/**
 * Phase 9 — Financial Progress Tracking Page
 * Add, view, edit, delete financial records with charts and monthly summaries
 */
import { useState, useEffect, useCallback } from 'react'
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts'
import { progressService, analyticsService } from '../services/analyticsService'
import type { FinancialRecord, FinancialRecordCreate, FinancialAnalytics } from '../types/analytics'

const fmt = (n: number | null) =>
  n === null ? '—' : `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

// ── Add Record Form ───────────────────────────────────────────────────────────

function RecordForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: Partial<FinancialRecordCreate>
  onSave:   (data: FinancialRecordCreate) => Promise<void>
  onCancel: () => void
}) {
  const today = new Date().toISOString().split('T')[0]
  const [form,   setForm]   = useState<FinancialRecordCreate>({
    record_date:  initial?.record_date  ?? today,
    revenue:      initial?.revenue      ?? undefined,
    expenses:     initial?.expenses     ?? undefined,
    customers:    initial?.customers    ?? undefined,
    investment:   initial?.investment   ?? undefined,
    savings:      initial?.savings      ?? undefined,
    inventory_cost: initial?.inventory_cost ?? undefined,
    notes:        initial?.notes        ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState<string | null>(null)

  const estProfit = (form.revenue ?? 0) - (form.expenses ?? 0)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.record_date) { setError('Date is required'); return }
    setSaving(true); setError(null)
    try {
      await onSave({
        ...form,
        revenue:      form.revenue      ? Number(form.revenue)      : undefined,
        expenses:     form.expenses     ? Number(form.expenses)     : undefined,
        customers:    form.customers    ? Number(form.customers)    : undefined,
        investment:   form.investment   ? Number(form.investment)   : undefined,
        savings:      form.savings      ? Number(form.savings)      : undefined,
        inventory_cost: form.inventory_cost ? Number(form.inventory_cost) : undefined,
        notes:        form.notes || undefined,
      })
    } catch { setError('Failed to save record.') }
    finally { setSaving(false) }
  }

  const inp = (key: keyof FinancialRecordCreate, label: string, placeholder = '') => (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <input
        type="number" min="0" placeholder={placeholder}
        value={(form[key] as number | undefined)?.toString() ?? ''}
        onChange={e => setForm(prev => ({ ...prev, [key]: e.target.value }))}
        className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none"
      />
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-xs text-red-400">{error}</p>}

      <div>
        <label className="block text-xs text-gray-400 mb-1">Record Month *</label>
        <input
          type="date" required value={form.record_date}
          onChange={e => setForm(prev => ({ ...prev, record_date: e.target.value }))}
          className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none [color-scheme:dark]"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {inp('revenue',      '💰 Revenue (₹)',     'e.g. 25000')}
        {inp('expenses',     '📉 Expenses (₹)',     'e.g. 15000')}
      </div>

      {/* Computed profit preview */}
      {(form.revenue !== undefined || form.expenses !== undefined) && (
        <div className={`text-xs px-3 py-2 rounded-lg border ${
          estProfit >= 0
            ? 'text-emerald-400 bg-emerald-900/20 border-emerald-700/30'
            : 'text-red-400 bg-red-900/20 border-red-700/30'
        }`}>
          Calculated Profit: ₹{estProfit.toLocaleString('en-IN')}
          <span className="text-gray-500 ml-2">(revenue − expenses)</span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        {inp('customers',      '👥 Customers',    'count')}
        {inp('savings',        '🏦 Savings (₹)',  'amount')}
        {inp('inventory_cost', '📦 Inventory (₹)', 'cost')}
      </div>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Notes</label>
        <textarea
          rows={2} value={form.notes ?? ''}
          onChange={e => setForm(prev => ({ ...prev, notes: e.target.value }))}
          placeholder="Optional notes for this period…"
          className="w-full bg-surface-700/30 border border-surface-600/40 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none resize-none"
        />
      </div>

      <p className="text-[10px] text-gray-600">
        ⚠️ Data you enter is for personal tracking only — not verified financial data.
      </p>

      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} className="btn-ghost text-sm px-4 py-2">Cancel</button>
        <button type="submit" disabled={saving} className="btn-primary text-sm px-5 py-2 disabled:opacity-50">
          {saving ? 'Saving…' : 'Save Record'}
        </button>
      </div>
    </form>
  )
}

// ── Record Row ────────────────────────────────────────────────────────────────

function RecordRow({ record, onDelete }: { record: FinancialRecord; onDelete: (id: string) => void }) {
  const [deleting, setDeleting] = useState(false)
  const d = new Date(record.record_date)

  const handleDelete = async () => {
    if (!confirm('Delete this record?')) return
    setDeleting(true)
    try { onDelete(record.id) } finally { setDeleting(false) }
  }

  return (
    <tr className="border-b border-surface-700/30 hover:bg-surface-700/10 transition-colors">
      <td className="py-3 px-4 text-xs text-gray-300">
        {d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
      </td>
      <td className="py-3 px-4 text-xs text-white text-right">{fmt(record.revenue)}</td>
      <td className="py-3 px-4 text-xs text-white text-right">{fmt(record.expenses)}</td>
      <td className={`py-3 px-4 text-xs text-right font-semibold ${
        (record.profit ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
      }`}>{fmt(record.profit)}</td>
      <td className="py-3 px-4 text-xs text-gray-400 text-right">{record.customers?.toFixed(0) ?? '—'}</td>
      <td className="py-3 px-4 text-xs text-gray-400">{record.notes?.slice(0, 30) ?? ''}</td>
      <td className="py-3 px-4 text-right">
        <button
          onClick={handleDelete} disabled={deleting}
          className="text-[10px] text-red-400 hover:text-red-300 border border-red-700/30 px-2 py-0.5 rounded transition-colors disabled:opacity-50">
          {deleting ? '…' : 'Delete'}
        </button>
      </td>
    </tr>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function FinancialProgress() {
  const [records,   setRecords]   = useState<FinancialRecord[]>([])
  const [analytics, setAnalytics] = useState<FinancialAnalytics | null>(null)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)
  const [showForm,  setShowForm]  = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [recRes, anRes] = await Promise.all([
        progressService.list({ limit: 24 }),
        analyticsService.getFinancial(),
      ])
      // records are newest-first for table; reverse for chart
      setRecords(recRes.items)
      setAnalytics(anRes)
    } catch { setError('Failed to load financial data.') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data: FinancialRecordCreate) => {
    const r = await progressService.create(data)
    setRecords(prev => [r, ...prev])
    setShowForm(false)
    // Reload analytics
    const anRes = await analyticsService.getFinancial()
    setAnalytics(anRes)
  }

  const handleDelete = async (id: string) => {
    await progressService.delete(id)
    setRecords(prev => prev.filter(r => r.id !== id))
    const anRes = await analyticsService.getFinancial()
    setAnalytics(anRes)
  }

  // Chart data — oldest first
  const chartData = [...records].reverse().map(r => ({
    name:     r.record_date.slice(0, 7),
    Revenue:  r.revenue  ?? 0,
    Expenses: r.expenses ?? 0,
    Profit:   r.profit   ?? 0,
  }))

  const hasFin = analytics?.status === 'ok'

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">
            💰 <span className="text-gradient">Financial Progress</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Track your monthly revenue, expenses, and profit
          </p>
        </div>
        <button
          id="add-record-btn"
          onClick={() => setShowForm(true)}
          className="btn-primary text-sm px-4 py-2">
          + Add Record
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="card p-5">
          <h2 className="text-sm font-bold text-white mb-4">📝 Add Financial Record</h2>
          <RecordForm onSave={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {/* Summary cards */}
      {hasFin && analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total Revenue',  value: fmt(analytics.total_revenue),        color: 'text-emerald-400' },
            { label: 'Total Expenses', value: fmt(analytics.total_expenses),       color: 'text-red-400' },
            { label: 'Total Profit',   value: fmt(analytics.total_profit),         color: 'text-cyan-400' },
            { label: 'Avg Monthly',    value: fmt(analytics.avg_monthly_revenue),  color: 'text-white' },
          ].map(s => (
            <div key={s.label} className="card p-4">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">{s.label}</p>
              <p className={`text-lg font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Chart */}
      {chartData.length > 1 && (
        <div className="card p-5">
          <h2 className="text-sm font-display font-bold text-white mb-4">📈 Revenue vs Expenses vs Profit</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }}
                tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : String(v)} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                formatter={(v: unknown) => [`₹${Number(v).toLocaleString('en-IN')}`, ''] as [string, string]}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="Revenue"  fill="#22c55e" radius={[3,3,0,0]} />
              <Bar dataKey="Expenses" fill="#ef4444" radius={[3,3,0,0]} />
              <Bar dataKey="Profit"   fill="#06b6d4" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Error */}
      {error && <p className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">{error}</p>}

      {/* Loading */}
      {loading && (
        <div className="card p-8 text-center">
          <div className="w-8 h-8 border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-400">Loading records…</p>
        </div>
      )}

      {/* Table */}
      {!loading && records.length > 0 && (
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-surface-700/30">
            <h2 className="text-sm font-bold text-white">📋 Record History</h2>
            <span className="text-[10px] text-gray-500">{records.length} records</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-surface-700/30">
                  {['Period', 'Revenue', 'Expenses', 'Profit', 'Customers', 'Notes', ''].map(h => (
                    <th key={h} className={`text-[10px] text-gray-500 uppercase tracking-wider py-2 px-4 ${
                      h && h !== 'Period' && h !== 'Notes' && h !== '' ? 'text-right' : 'text-left'
                    }`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <RecordRow key={r.id} record={r} onDelete={handleDelete} />
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-gray-600 italic px-5 py-3 border-t border-surface-700/30">
            ⚠️ Data entered by entrepreneur for personal tracking. Not verified financial records.
          </p>
        </div>
      )}

      {/* Empty state */}
      {!loading && records.length === 0 && !error && (
        <div className="card p-12 text-center text-gray-500">
          <div className="text-5xl mb-4">📊</div>
          <p className="text-base font-semibold text-gray-400 mb-2">No financial records yet</p>
          <p className="text-sm mb-6">Start tracking your monthly revenue and expenses to unlock analytics.</p>
          <button onClick={() => setShowForm(true)} className="btn-primary text-sm px-5 py-2">
            Add Your First Record
          </button>
        </div>
      )}
    </div>
  )
}
