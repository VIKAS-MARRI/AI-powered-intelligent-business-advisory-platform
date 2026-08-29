/**
 * TypeScript types for Phase 7 AI Advisory API.
 */

export interface FinalAdviceOut {
  summary:            string
  recommendation?:    string
  financial_plan?:    string
  market_insight?:    string
  government_support?: string
  risks:              string[]
  next_steps:         string[]
  ai_generated:       boolean
  data_source?:       string
  disclaimer:         string
  ai_generated_text?: string
}

export interface AdvisoryResultOut {
  session_id:      string
  status:          string
  required_agents: string[]
  ai_status:       string
  results:         Record<string, unknown>
  final_advice:    FinalAdviceOut
  errors:          string[]
  disclaimer:      string
}

export interface AIStatusOut {
  ai_available:       boolean
  provider:           string
  model:              string
  fallback_available: boolean
  status:             string
}

export interface AdvisoryHistoryItem {
  id:              string
  question:        string
  required_agents: string[]
  ai_status:       string
  status:          string
  created_at:      string
  summary?:        string
}

export interface AdvisoryHistoryOut {
  items: AdvisoryHistoryItem[]
  total: number
}

export interface AdvisoryQueryRequest {
  question:           string
  available_capital?: number
  business_id?:       string
  latitude?:          number
  longitude?:         number
  state_name?:        string
  radius_km?:         number
}
