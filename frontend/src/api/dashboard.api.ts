import { apiClient } from '@/core/api/client'
import type { DashboardSummary } from '@/core/types'

/** Fetch dashboard summary data */
export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>('/dashboard/summary')
  return response.data
}
