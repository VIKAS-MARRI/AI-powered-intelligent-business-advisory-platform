import api from './api'
import type { BusinessPublic, BusinessListResponse, RecommendationResponse } from '../types/business'

export const businessService = {
  async list(params?: {
    category?: string
    risk_level?: string
    min_investment?: number
    max_investment?: number
    rural_only?: boolean
    search?: string
  }): Promise<BusinessListResponse> {
    const res = await api.get<BusinessListResponse>('/businesses', { params })
    return res.data
  },

  async categories(): Promise<string[]> {
    const res = await api.get<string[]>('/businesses/categories')
    return res.data
  },

  async getOne(id: string): Promise<BusinessPublic> {
    const res = await api.get<BusinessPublic>(`/businesses/${id}`)
    return res.data
  },

  async recommend(params?: {
    available_capital?: number
    skills?: string
    business_interests?: string
    monthly_income_goal?: number
    preferred_risk?: string
    top_n?: number
  }): Promise<RecommendationResponse> {
    const res = await api.post<RecommendationResponse>('/recommendations', params ?? {})
    return res.data
  },
}
