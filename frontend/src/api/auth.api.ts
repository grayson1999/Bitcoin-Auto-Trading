import { authClient, getRefreshToken } from '@core/api/client'
import type { User, AuthTokens } from '@core/types'

interface LoginResponse extends AuthTokens {}

interface RefreshResponse extends AuthTokens {}

export const authApi = {
  /** Login with email and password */
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await authClient.post<LoginResponse>('/auth/login', {
      email,
      password,
    })
    return response.data
  },

  /** Logout current user */
  async logout(): Promise<void> {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      await authClient.post('/auth/logout', {
        refresh_token: refreshToken,
      })
    }
  },

  /** Refresh access token */
  async refresh(): Promise<RefreshResponse> {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    const response = await authClient.post<RefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  /** Verify current token and get user info */
  async verify(): Promise<User> {
    const response = await authClient.get<User>('/auth/verify')
    return response.data
  },
}

export default authApi
