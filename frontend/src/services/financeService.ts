/**
 * Finance API service — calls Phase 3 /finance endpoints.
 */
import api from './api'
import type {
  FullAnalysisOut,
  CashFlowOut,
  AnalyzeRequest,
  CashFlowRequest,
  FinancialAssumptions,
} from '../types/finance'

const DEFAULT_ASSUMPTIONS: FinancialAssumptions = {
  emergency_reserve_pct: 0.125,
  working_capital_pct: 0.20,
  monthly_revenue_growth: 0.02,
  monthly_expense_growth: 0.005,
  fixed_cost_ratio: 0.55,
  variable_cost_ratio: null,
}

export const financeService = {
  /** Run the full financial analysis for a business + capital amount. */
  async analyze(
    business_id: string,
    available_capital: number,
    assumptions: Partial<FinancialAssumptions> = {}
  ): Promise<FullAnalysisOut> {
    const body: AnalyzeRequest = {
      business_id,
      available_capital,
      assumptions: { ...DEFAULT_ASSUMPTIONS, ...assumptions },
    }
    const res = await api.post<FullAnalysisOut>('/finance/analyze', body)
    return res.data
  },

  /** Get quick analysis using the authenticated user's profile capital. */
  async quickAnalysis(business_id: string): Promise<FullAnalysisOut> {
    const res = await api.get<FullAnalysisOut>(`/finance/business/${business_id}`)
    return res.data
  },

  /** Generate a custom cash flow projection. */
  async cashFlow(params: CashFlowRequest): Promise<CashFlowOut> {
    const res = await api.post<CashFlowOut>('/finance/cash-flow', params)
    return res.data
  },

  defaultAssumptions: DEFAULT_ASSUMPTIONS,
}
