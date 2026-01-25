import apiClient from '@core/api/client'
import type { SystemMetrics } from '@core/types'
import { mockSystemMetrics } from './mocks/admin.mock'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_ADMIN === 'true'

/**
 * Fetch system metrics (CPU, memory, disk, scheduler jobs)
 * Falls back to mock data if backend API is not available
 */
export async function getSystemMetrics(): Promise<SystemMetrics> {
  if (USE_MOCK) {
    return mockSystemMetrics()
  }

  try {
    const response = await apiClient.get<SystemMetrics>('/admin/system')
    return response.data
  } catch {
    // Silently fall back to mock data when API unavailable
    return mockSystemMetrics()
  }
}
