import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { User } from '@core/types'
import { getAccessToken, setTokens, clearTokens } from '@core/api/client'
import { authApi } from '@api/auth.api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  isAdmin: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user
  const isAdmin = user?.role === 'admin'

  const refreshUser = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const userData = await authApi.verify()
      setUser(userData)
    } catch {
      clearTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await authApi.login(email, password)
      setTokens(response.access_token, response.refresh_token)
      const userData = await authApi.verify()
      setUser(userData)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore logout errors
    } finally {
      clearTokens()
      setUser(null)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    isAdmin,
    login,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export { AuthContext }
