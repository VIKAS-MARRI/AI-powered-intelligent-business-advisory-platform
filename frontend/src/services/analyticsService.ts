/**
 * Phase 9 service clients — Analytics, Goals, Financial Progress
 */
import api from './api'
import type {
  DashboardAnalytics, FinancialAnalytics, GoalAnalytics, ProgressScore,
  ActionPlan, TimelineOut,
  BusinessGoal, GoalCreate, GoalUpdate, GoalListOut,
  FinancialRecord, FinancialRecordCreate, FinancialRecordListOut,
} from '../types/analytics'

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsService = {
  async getDashboard(): Promise<DashboardAnalytics> {
    const r = await api.get<DashboardAnalytics>('/analytics/dashboard')
    return r.data
  },
  async getFinancial(): Promise<FinancialAnalytics> {
    const r = await api.get<FinancialAnalytics>('/analytics/financial')
    return r.data
  },
  async getGoalAnalytics(): Promise<GoalAnalytics> {
    const r = await api.get<GoalAnalytics>('/analytics/goals')
    return r.data
  },
  async getProgressScore(): Promise<ProgressScore> {
    const r = await api.get<ProgressScore>('/analytics/progress-score')
    return r.data
  },
  async getTrends(): Promise<Record<string, unknown>> {
    const r = await api.get('/analytics/trends')
    return r.data
  },
}

// ── Goals ─────────────────────────────────────────────────────────────────────
export const goalService = {
  async list(params?: { status?: string; priority?: string }): Promise<GoalListOut> {
    const r = await api.get<GoalListOut>('/goals', { params })
    return r.data
  },
  async get(id: string): Promise<BusinessGoal> {
    const r = await api.get<BusinessGoal>(`/goals/${id}`)
    return r.data
  },
  async create(data: GoalCreate): Promise<BusinessGoal> {
    const r = await api.post<BusinessGoal>('/goals', data)
    return r.data
  },
  async update(id: string, data: GoalUpdate): Promise<BusinessGoal> {
    const r = await api.patch<BusinessGoal>(`/goals/${id}`, data)
    return r.data
  },
  async delete(id: string): Promise<void> {
    await api.delete(`/goals/${id}`)
  },
  async updateProgress(id: string, currentValue: number): Promise<BusinessGoal> {
    const r = await api.post<BusinessGoal>(`/goals/${id}/progress`, { current_value: currentValue })
    return r.data
  },
}

// ── Financial Progress ────────────────────────────────────────────────────────
export const progressService = {
  async list(params?: { from_date?: string; to_date?: string; limit?: number; offset?: number }): Promise<FinancialRecordListOut> {
    const r = await api.get<FinancialRecordListOut>('/progress/financial', { params })
    return r.data
  },
  async create(data: FinancialRecordCreate): Promise<FinancialRecord> {
    const r = await api.post<FinancialRecord>('/progress/financial', data)
    return r.data
  },
  async update(id: string, data: Partial<FinancialRecordCreate>): Promise<FinancialRecord> {
    const r = await api.patch<FinancialRecord>(`/progress/financial/${id}`, data)
    return r.data
  },
  async delete(id: string): Promise<void> {
    await api.delete(`/progress/financial/${id}`)
  },
}

// ── Actions ───────────────────────────────────────────────────────────────────
export const actionsService = {
  async getNextActions(): Promise<ActionPlan> {
    const r = await api.get<ActionPlan>('/actions/next')
    return r.data
  },
  async updateStatus(id: string, status: string): Promise<void> {
    await api.patch(`/actions/${id}/status`, { status })
  },
}

// ── Timeline ─────────────────────────────────────────────────────────────────
export const timelineService = {
  async getTimeline(limit = 20): Promise<TimelineOut> {
    const r = await api.get<TimelineOut>('/activity/timeline', { params: { limit } })
    return r.data
  },
}
