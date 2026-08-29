/**
 * TypeScript types for Phase 4 Investment Optimizer API.
 */

export interface OptimizeRequest {
  business_id: string
  available_capital: number
  risk_preference?: 'conservative' | 'balanced' | 'growth'
  minimum_emergency_reserve?: number
  minimum_working_capital?: number
  maximum_marketing_budget?: number
}

export interface StrategyRequest {
  business_id: string
  available_capital: number
  strategy: 'conservative' | 'balanced' | 'growth'
  minimum_emergency_reserve?: number
  minimum_working_capital?: number
  maximum_marketing_budget?: number
}

export interface AllocationResultOut {
  name: string
  allocated: number
  minimum: number
  recommended: number
  maximum: number
  pct_of_total: number
}

export interface StrategyResultOut {
  name: 'conservative' | 'balanced' | 'growth'
  label: string
  total_allocated: number
  remaining_capital: number
  optimization_score: number
  risk_level: 'Low' | 'Medium' | 'High'
  allocations: AllocationResultOut[]
  tradeoffs: string[]
  explanations: string[]
  allocation_dict: Record<string, number>
}

export interface InsufficientCapitalInfoOut {
  minimum_required_capital: number
  funding_gap: number
  suggestions: string[]
}

export interface OptimizationResultOut {
  status: 'optimal' | 'insufficient_capital'
  recommended_strategy: 'conservative' | 'balanced' | 'growth'
  available_capital: number
  minimum_required_capital: number
  funding_gap: number
  strategies: StrategyResultOut[]
  insufficient_info: InsufficientCapitalInfoOut | null
  disclaimer: string
}
