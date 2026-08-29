/**
 * TypeScript types for Phase 5 Market Intelligence API.
 */

export interface LocationSearchResult {
  display_name: string
  latitude:     number
  longitude:    number
  place_id?:    string
  country?:     string
  state?:       string
  district?:    string
}

export interface MarketAnalyzeRequest {
  business_id: string
  latitude:    number
  longitude:   number
  radius_km?:  number
}

export interface NearbyRequest {
  latitude:  number
  longitude: number
  radius_km?: number
}

export interface NearbyPlaceOut {
  osm_id:          string
  name:            string
  category:        string
  latitude:        number
  longitude:       number
  distance_meters: number
}

export interface CompetitorSummaryOut {
  direct_count:      number
  related_count:     number
  total_businesses:  number
  competition_level: 'Low' | 'Moderate' | 'High'
  density_per_sqkm:  number
}

export interface MarketOpportunityOut {
  competition_score:    number
  infrastructure_score: number
  accessibility_score:  number
  diversity_score:      number
  market_size_score:    number
  total:                number
}

export interface LocationSuitabilityOut {
  competition_score:    number
  infrastructure_score: number
  customer_proxy_score: number
  business_density:     number
  total:                number
}

export interface MarketInsightOut {
  icon:    string
  message: string
  level:   'positive' | 'warning' | 'neutral'
}

export interface MarketAnalysisOut {
  latitude:            number
  longitude:           number
  radius_km:           number
  location_name:       string | null
  business_name:       string
  business_id:         string
  competitor_summary:  CompetitorSummaryOut
  opportunity:         MarketOpportunityOut
  suitability:         LocationSuitabilityOut
  nearby_places:       NearbyPlaceOut[]
  direct_competitors:  NearbyPlaceOut[]
  insights:            MarketInsightOut[]
  recommendations:     string[]
  disclaimer:          string
}

export interface NearbyResultOut {
  latitude:     number
  longitude:    number
  radius_km:    number
  total_places: number
  places:       NearbyPlaceOut[]
  categories:   Record<string, number>
  from_cache:   boolean
  error:        string | null
  disclaimer:   string
}
