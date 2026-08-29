/**
 * TypeScript types for Phase 6 Government Scheme Intelligence API.
 */

export interface SchemeSummaryOut {
  id:                     string
  name:                   string
  slug:                   string
  short_description:      string
  category:               string
  sector:                 string
  location_scope:         string
  key_benefit:            string | null
  maximum_loan_amount:    number | null
  maximum_subsidy_amount: number | null
  subsidy_percentage:     number | null
  is_women_specific:      boolean
  is_sc_st_specific:      boolean
  is_rural_specific:      boolean
  is_youth_specific:      boolean
  official_url:           string
  data_status:            string
  last_reviewed:          string
}

export interface SchemeOut extends SchemeSummaryOut {
  full_description:         string | null
  target_beneficiaries:     string
  states:                   string
  business_categories:      string
  minimum_age:              number | null
  maximum_age:              number | null
  minimum_investment:       number | null
  maximum_investment:       number | null
  eligibility_requirements: string[]
  required_documents:       string[]
  application_steps:        string[]
  official_source:          string
  sort_order:               number
}

export interface ScoreBreakdownOut {
  business_relevance:       number
  sector_match:             number
  investment_compatibility: number
  location_eligibility:     number
  profile_eligibility:      number
  total:                    number
}

export interface EligibilityFlagOut {
  status:              string
  reasons:             string[]
  missing_information: string[]
}

export interface SchemeMatchOut {
  scheme_id:         string
  scheme_name:       string
  scheme_slug:       string
  category:          string
  sector:            string
  data_status:       string
  key_benefit:       string
  official_url:      string
  score_breakdown:   ScoreBreakdownOut
  eligibility:       EligibilityFlagOut
  match_reasons:     string[]
  funding_relevance: 'Loan' | 'Subsidy' | 'Both' | 'Support'
  tags:              string[]
}

export interface FundingGapOut {
  estimated_investment: number
  available_capital:    number
  funding_gap:          number
  gap_percentage:       number
  has_gap:              boolean
  gap_label:            string
}

export interface MatchResultOut {
  funding_gap:   FundingGapOut
  matches:       SchemeMatchOut[]
  best_overall:  string | null
  best_loan:     string | null
  best_subsidy:  string | null
  best_rural:    string | null
  total_schemes: number
  disclaimer:    string
}

export interface SchemesListOut {
  items: SchemeSummaryOut[]
  total: number
}

export interface CategoriesOut {
  categories: string[]
  sectors:    string[]
}

export interface SchemeMatchRequest {
  business_id:          string
  estimated_investment: number
  available_capital:    number
  state?:               string
  user_age?:            number
  is_woman?:            boolean
  is_sc_st?:            boolean
  is_rural?:            boolean
}

export interface SchemeCompareRequest {
  scheme_ids:           string[]
  business_id?:         string
  estimated_investment?: number
  available_capital?:   number
  state?:               string
}
