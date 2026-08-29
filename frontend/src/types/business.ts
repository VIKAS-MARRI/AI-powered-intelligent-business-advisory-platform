export interface BusinessPublic {
  id: string
  name: string
  category: string
  description: string
  business_type: string
  suitable_for_rural: boolean
  min_investment: number
  max_investment: number
  estimated_monthly_revenue_min: number
  estimated_monthly_revenue_max: number
  estimated_monthly_expenses_min: number
  estimated_monthly_expenses_max: number
  estimated_monthly_profit_min: number
  estimated_monthly_profit_max: number
  risk_level: 'Low' | 'Medium' | 'High'
  required_skills: string
  required_skills_list: string[]
  risk_factors: string | null
  risk_factors_list: string[]
  key_challenges: string | null
  key_challenges_list: string[]
  setup_time_weeks_min: number
  setup_time_weeks_max: number
  avg_investment: number
  avg_monthly_profit: number
  is_demo_data: boolean
}

export interface BusinessListResponse {
  items: BusinessPublic[]
  total: number
  disclaimer: string
}

export interface ScoreBreakdown {
  budget: number
  skills: number
  interest: number
  profit: number
  risk: number
  income_goal: number
}

export interface RecommendationItem {
  rank: number
  business: BusinessPublic
  final_score: number
  score_breakdown: ScoreBreakdown
  reasons: string[]
  disclaimer: string
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[]
  profile_completeness: number
  total_businesses_scored: number
  disclaimer: string
}
