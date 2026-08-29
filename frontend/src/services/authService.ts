import api from './api'

export interface RegisterPayload {
  email: string
  password: string
  full_name?: string
  phone?: string
  preferred_language?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  full_name: string | null
  phone: string | null
  preferred_language: string
  state: string | null
  district: string | null
  village_town: string | null
  available_capital: number | null
  skills: string | null
  experience_years: number | null
  business_interests: string | null
  monthly_income_goal: number | null
  is_active: boolean
  created_at: string
}

export const authService = {
  async register(data: RegisterPayload): Promise<User> {
    const res = await api.post<User>('/auth/register', data)
    return res.data
  },

  async login(data: LoginPayload): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>('/auth/login', data)
    return res.data
  },

  async getMe(): Promise<User> {
    const res = await api.get<User>('/users/me')
    return res.data
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const res = await api.patch<User>('/users/me', data)
    return res.data
  },
}
