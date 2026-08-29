/**
 * Government Scheme API service client — Phase 6.
 */
import api from './api'
import type {
  SchemesListOut,
  SchemeOut,
  CategoriesOut,
  MatchResultOut,
  SchemeMatchOut,
  SchemeMatchRequest,
  SchemeCompareRequest,
} from '../types/scheme'

export const schemeService = {
  /** List all active schemes (optionally filtered). */
  async list(params?: {
    category?:    string
    sector?:      string
    state?:       string
    data_status?: string
  }): Promise<SchemesListOut> {
    const res = await api.get<SchemesListOut>('/schemes', { params })
    return res.data
  },

  /** Get available categories and sectors. */
  async categories(): Promise<CategoriesOut> {
    const res = await api.get<CategoriesOut>('/schemes/categories')
    return res.data
  },

  /** Get full details for a single scheme by ID or slug. */
  async get(idOrSlug: string): Promise<SchemeOut> {
    const res = await api.get<SchemeOut>(`/schemes/${idOrSlug}`)
    return res.data
  },

  /** Match and rank schemes for a business and financial profile. */
  async match(req: SchemeMatchRequest): Promise<MatchResultOut> {
    const res = await api.post<MatchResultOut>('/schemes/match', req)
    return res.data
  },

  /** Compare 2–4 specific schemes side-by-side. */
  async compare(req: SchemeCompareRequest): Promise<SchemeMatchOut[]> {
    const res = await api.post<SchemeMatchOut[]>('/schemes/compare', req)
    return res.data
  },
}
