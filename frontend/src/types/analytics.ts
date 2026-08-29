// Phase 9 TypeScript types — Analytics, Goals, Financial Progress, Actions

export type GoalStatus   = 'not_started' | 'in_progress' | 'completed' | 'overdue'
export type GoalPriority = 'low' | 'medium' | 'high'
export type GoalType     =
  | 'start_business' | 'revenue_target' | 'profit_target' | 'savings_capital'
  | 'apply_scheme' | 'business_registration' | 'improve_skills'
  | 'reduce_expenses' | 'customer_growth' | 'general'

export interface BusinessGoal {
  id:                  string
  user_id:             string
  title:               string
  description:         string | null
  goal_type:           GoalType
  status:              GoalStatus
  priority:            GoalPriority
  target_value:        number | null
  current_value:       number | null
  unit:                string | null
  start_date:          string | null
  target_date:         string | null
  progress_percentage: number
  days_remaining:      number | null
  is_overdue:          boolean
  created_at:          string
  updated_at:          string
}

export interface GoalCreate {
  title:          string
  description?:   string
  goal_type?:     GoalType
  priority?:      GoalPriority
  target_value?:  number
  current_value?: number
  unit?:          string
  start_date?:    string
  target_date?:   string
}

export interface GoalUpdate extends Partial<GoalCreate> {
  status?: GoalStatus
}

export interface GoalListOut {
  items: BusinessGoal[]
  total: number
}

export interface FinancialRecord {
  id:             string
  user_id:        string
  business_id:    string | null
  record_date:    string
  revenue:        number | null
  expenses:       number | null
  profit:         number | null
  customers:      number | null
  investment:     number | null
  savings:        number | null
  inventory_cost: number | null
  notes:          string | null
  created_at:     string
  updated_at:     string
}

export interface FinancialRecordCreate {
  record_date:     string
  revenue?:        number
  expenses?:       number
  customers?:      number
  investment?:     number
  savings?:        number
  inventory_cost?: number
  business_id?:    string
  notes?:          string
}

export interface FinancialRecordListOut {
  items:      FinancialRecord[]
  total:      number
  disclaimer: string
}

export interface TrendPoint {
  date:  string | null
  value: number
}

export interface FinancialAnalytics {
  status:               string
  record_count:         number
  period_months:        number
  total_revenue:        number
  total_expenses:       number
  total_profit:         number
  avg_monthly_revenue:  number
  avg_monthly_expenses: number
  avg_monthly_profit:   number
  revenue_growth_pct:   number | null
  expense_growth_pct:   number | null
  profit_growth_pct:    number | null
  revenue_trend:        string
  expense_trend:        string
  profit_trend:         string
  best_period:          string | null
  worst_period:         string | null
  revenue_series:       TrendPoint[]
  expense_series:       TrendPoint[]
  profit_series:        TrendPoint[]
  disclaimer:           string
}

export interface GoalAnalytics {
  total:          number
  completed:      number
  in_progress:    number
  not_started:    number
  overdue:        number
  completion_pct: number
  by_priority:    Record<string, number>
  by_type:        Record<string, number>
}

export interface ProgressScore {
  overall_score:    number
  category_scores:  Record<string, number>
  weights:          Record<string, number>
  strengths:        string[]
  improvement_areas: string[]
  confidence:       string
  score_explanation: string
  disclaimer:       string
}

export interface DashboardAnalytics {
  progress_score:      ProgressScore
  financial_analytics: FinancialAnalytics
  goal_analytics:      GoalAnalytics
  financial_insights:  string[]
  recent_activities:   Array<{ id: string; activity_type: string; title: string; created_at: string }>
  disclaimer:          string
}

export interface ActionItem {
  id:               string
  title:            string
  description:      string | null
  category:         string
  priority:         'low' | 'medium' | 'high' | 'critical'
  impact:           string
  estimated_effort: string | null
  related_phase:    string | null
  action_url:       string | null
  status:           'pending' | 'completed' | 'dismissed'
}

export interface ActionPlan {
  actions:   ActionItem[]
  generated: boolean
  total:     number
}

export interface TimelineEvent {
  id:            string
  activity_type: string
  title:         string
  description:   string | null
  reference_id:  string | null
  created_at:    string
}

export interface TimelineOut {
  items: TimelineEvent[]
  total: number
}
