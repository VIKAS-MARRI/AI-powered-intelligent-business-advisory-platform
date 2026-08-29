import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { User } from '../services/authService'
import { authService } from '../services/authService'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore session from sessionStorage on mount
  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (!token) {
      setIsLoading(false)
      return
    }
    authService
      .getMe()
      .then(setUser)
      .catch(() => {
        // Token is invalid/expired — clear it
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('user')
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (token: string) => {
    sessionStorage.setItem('access_token', token)
    const me = await authService.getMe()
    setUser(me)
    sessionStorage.setItem('user', JSON.stringify(me))
  }, [])

  const logout = useCallback(() => {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('user')
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const me = await authService.getMe()
    setUser(me)
    sessionStorage.setItem('user', JSON.stringify(me))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
