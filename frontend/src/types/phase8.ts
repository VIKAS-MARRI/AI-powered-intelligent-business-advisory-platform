/**
 * Phase 8 TypeScript types — Personalized Recommendations, Saved Businesses,
 * Natural Language Query, Interaction Tracking, Entrepreneur Profile.
 */

export interface SemanticMatchDetail {
  semantic_score:    number
  matched_concepts:  string[]
  explanation:       string
  method:            string
}

export interface PersonalizedBreakdown {
  semantic_skill:       number
  budget:               number
  market_opportunity:   number
  financial_potential:  number
  experience:           number
  gov_support:          number
  risk:                 number
  interest:             number
  income_goal:          number
  location:             number
  preference_modifier:  number
}

export interface PersonalizedScoreRaw {
  semantic_skill:       number
  budget:               number
  market_opportunity:   number
  financial_potential:  number
  experience:           number
  gov_support:          number
  risk:                 number
  interest:             number
  income_goal:          number
  location:             number
}

export interface FinancialOutlook {
  min_investment:       number
  max_investment:       number
  monthly_profit_min:   number
  monthly_profit_max:   number
  risk_level:           string
}

export interface SemanticMatchSummary {
  score:        number
  concepts:     string[]
  explanation:  string
}

export interface RecommendationExplanation {
  why_recommended:   string[]
  strengths:         string[]
  challenges:        string[]
  next_steps:        string[]
  financial_outlook: FinancialOutlook
  semantic_match:    SemanticMatchSummary
  disclaimer:        string
}

export interface PersonalizedRecommendationItem {
  rank:               number
  business_id:        string
  business_name:      string
  category:           string
  business_type:      string
  risk_level:         string
  min_investment:     number
  max_investment:     number
  monthly_profit_min: number
  monthly_profit_max: number
  setup_time_weeks_min: number
  setup_time_weeks_max: number
  suitable_for_rural: boolean
  description:        string
  required_skills:    string

  final_score:        number
  breakdown:          PersonalizedBreakdown
  raw_scores:         PersonalizedScoreRaw
  semantic_detail:    SemanticMatchDetail
  explanation:        RecommendationExplanation
  is_saved:           boolean
  disclaimer:         string
}

export interface PersonalizedRecommendationRequest {
  available_capital?:   number
  skills?:              string
  business_interests?:  string
  monthly_income_goal?: number
  preferred_risk?:      string
  experience_years?:    number
  location_type?:       string
  top_n?:               number
  use_preferences?:     boolean
}

export interface PersonalizedRecommendationResponse {
  recommendations:         PersonalizedRecommendationItem[]
  profile_completeness:    number
  total_businesses_scored: number
  ai_mode:                 string
  disclaimer:              string
}

export interface ExtractedIntent {
  budget:               number | null
  skills:               string | null
  risk_preference:      string | null
  business_type_hints:  string[]
  location_type:        string | null
  raw_query:            string
}

export interface NaturalQueryResponse {
  recommendations: PersonalizedRecommendationItem[]
  extracted_intent: ExtractedIntent
  parse_method:    string
  disclaimer:      string
}

export interface PreferenceSummary {
  preferred_categories: Record<string, number>
  avoided_categories:   Record<string, number>
  preferred_risk:       string | null
  total_interactions:   number
  disclaimer:           string
}

export interface SavedBusinessOut {
  id:          string
  business_id: string
  notes:       string | null
  created_at:  string
}

export interface SavedBusinessListOut {
  items: SavedBusinessOut[]
  total: number
}

export interface EntrepreneurProfileIn {
  detailed_skills?:            string
  education_level?:            string
  experience_description?:     string
  preferred_work_style?:       string
  daily_available_hours?:      number
  location_type?:              string
  preferred_business_types?:   string
  family_business_experience?: boolean
  existing_assets?:            string
  growth_preference?:          string
  business_goal?:              string
}

export interface EntrepreneurProfileOut extends EntrepreneurProfileIn {
  id:         string
  user_id:    string
  created_at: string
  updated_at: string
}
