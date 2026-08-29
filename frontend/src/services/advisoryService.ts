/**
 * AI Advisory service client — Phase 7.
 */
import api from './api'
import type {
  AdvisoryQueryRequest,
  AdvisoryResultOut,
  AIStatusOut,
  AdvisoryHistoryOut,
} from '../types/advisory'

export const advisoryService = {
  async query(req: AdvisoryQueryRequest): Promise<AdvisoryResultOut> {
    const res = await api.post<AdvisoryResultOut>('/advisor/query', req)
    return res.data
  },

  async analyze(req: AdvisoryQueryRequest): Promise<AdvisoryResultOut> {
    const res = await api.post<AdvisoryResultOut>('/advisor/analyze', req)
    return res.data
  },

  async status(): Promise<AIStatusOut> {
    const res = await api.get<AIStatusOut>('/advisor/status')
    return res.data
  },

  async history(limit = 20): Promise<AdvisoryHistoryOut> {
    const res = await api.get<AdvisoryHistoryOut>('/advisor/history', { params: { limit } })
    return res.data
  },
}
