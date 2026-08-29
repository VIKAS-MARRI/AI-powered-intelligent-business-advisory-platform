/**
 * Market Intelligence API service client — Phase 5.
 */
import api from './api'
import type {
  LocationSearchResult,
  MarketAnalyzeRequest,
  MarketAnalysisOut,
  NearbyRequest,
  NearbyResultOut,
} from '../types/market'

export const marketService = {
  /** Search for a location by name using Nominatim / OpenStreetMap. */
  async searchLocation(query: string, limit = 5): Promise<LocationSearchResult[]> {
    const res = await api.get<LocationSearchResult[]>('/locations/search', {
      params: { q: query, limit },
    })
    return res.data
  },

  /** Run the full hyper-local market intelligence analysis. */
  async analyze(req: MarketAnalyzeRequest): Promise<MarketAnalysisOut> {
    const res = await api.post<MarketAnalysisOut>('/market/analyze', req)
    return res.data
  },

  /** Fetch only nearby businesses at a location (no competition analysis). */
  async nearby(req: NearbyRequest): Promise<NearbyResultOut> {
    const res = await api.post<NearbyResultOut>('/market/nearby', req)
    return res.data
  },
}
