/**
 * TypeScript types for Phase 3 Finance API responses.
 */

export interface FinancialAssumptions {
  emergency_reserve_pct: number   // 0.125 default
  working_capital_pct: number     // 0.20 default
  monthly_revenue_growth: number  // 0.02 default
  monthly_expense_growth: number  // 0.005 default
  fixed_cost_ratio: number        // 0.55 default
  variable_cost_ratio?: number | null
}

export interface AnalyzeRequest {
  business_id: string
  available_capital: number
  assumptions: FinancialAssumptions
}

export interface CashFlowRequest {
  business_id: string
  initial_monthly_revenue: number
  initial_monthly_expenses: number
  months: number
  monthly_revenue_growth: number
  monthly_expense_growth: number
  ramp_up_months: number
  ramp_up_factor: number
}

export interface InvestmentAllocationOut {
  equipment: number
  initial_inventory: number
  business_setup: number
  licensing: number
  marketing: number
  working_capital: number
  emergency_reserve: number
  total_allocated: number
  available_capital: number
  funding_gap: number
  is_feasible: boolean
  allocation_dict: Record<string, number>
}

export interface ScenarioOut {
  name: string
  monthly_revenue: number
  monthly_expenses: number
  monthly_profit: number
  annual_revenue: number
  annual_profit: number
  profit_margin_pct: number
}

export interface BreakEvenOut {
  fixed_costs_monthly: number
  variable_cost_ratio: number
  contribution_margin_ratio: number
  break_even_revenue: number
  assumed: boolean
}

export interface CashFlowMonthOut {
  month: number
  revenue: number
  expenses: number
  profit: number
  cumulative_cash_flow: number
}

export interface HealthScoreOut {
  budget_sufficiency: number
  profitability: number
  roi_score: number
  payback_score: number
  emergency_reserve_score: number
  expense_ratio_score: number
  total: number
  status: string
  strengths: string[]
  risks: string[]
  recommendations: string[]
}

export interface RiskIndicatorOut {
  name: string
  level: 'Low' | 'Medium' | 'High'
  explanation: string
}

export interface FullAnalysisOut {
  business_id: string
  business_name: string
  available_capital: number
  investment: InvestmentAllocationOut
  conservative: ScenarioOut
  expected: ScenarioOut
  optimistic: ScenarioOut
  roi_pct: number
  payback_months: number | null
  payback_feasible: boolean
  payback_note: string
  break_even: BreakEvenOut
  health: HealthScoreOut
  risks: RiskIndicatorOut[]
  cash_flow: CashFlowMonthOut[]
  disclaimer: string
}

export interface CashFlowOut {
  business_id: string
  months: CashFlowMonthOut[]
  disclaimer: string
}
