/**
 * Phase 8 service client — Personalized Recommendations, Natural Query,
 * Saved Businesses, Interactions, Entrepreneur Profile.
 */
import api from './api'
import type {
  PersonalizedRecommendationRequest,
  PersonalizedRecommendationResponse,
  NaturalQueryResponse,
  PreferenceSummary,
  SavedBusinessListOut,
  SavedBusinessOut,
  EntrepreneurProfileIn,
  EntrepreneurProfileOut,
} from '../types/phase8'

export const phase8Service = {
  // ── Personalized recommendations ──────────────────────────────────────────
  async getPersonalized(req: PersonalizedRecommendationRequest = {}): Promise<PersonalizedRecommendationResponse> {
    const res = await api.post<PersonalizedRecommendationResponse>('/recommendations/personalized', req)
    return res.data
  },

  // ── Natural language query ─────────────────────────────────────────────────
  async naturalQuery(query: string, topN = 5): Promise<NaturalQueryResponse> {
    const res = await api.post<NaturalQueryResponse>('/recommendations/natural-query', {
      query,
      top_n: topN,
      use_ai_parsing: true,
    })
    return res.data
  },

  // ── Interaction tracking ───────────────────────────────────────────────────
  async recordInteraction(businessId: string, type: string): Promise<void> {
    await api.post(`/recommendations/${businessId}/interaction`, { interaction_type: type })
  },

  // ── Preferences ───────────────────────────────────────────────────────────
  async getPreferences(): Promise<PreferenceSummary> {
    const res = await api.get<PreferenceSummary>('/recommendations/preferences')
    return res.data
  },

  // ── Entrepreneur profile ───────────────────────────────────────────────────
  async getProfile(): Promise<EntrepreneurProfileOut | null> {
    try {
      const res = await api.get<EntrepreneurProfileOut>('/recommendations/profile')
      return res.data
    } catch {
      return null
    }
  },

  async upsertProfile(data: EntrepreneurProfileIn): Promise<EntrepreneurProfileOut> {
    const res = await api.put<EntrepreneurProfileOut>('/recommendations/profile', data)
    return res.data
  },

  // ── Saved businesses ──────────────────────────────────────────────────────
  async getSaved(): Promise<SavedBusinessListOut> {
    const res = await api.get<SavedBusinessListOut>('/saved-businesses')
    return res.data
  },

  async saveBusiness(businessId: string, notes?: string): Promise<SavedBusinessOut> {
    const res = await api.post<SavedBusinessOut>(`/saved-businesses/${businessId}`, { notes })
    return res.data
  },

  async deleteSaved(businessId: string): Promise<void> {
    await api.delete(`/saved-businesses/${businessId}`)
  },
}
