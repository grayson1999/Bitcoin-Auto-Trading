import { apiClient } from '@/core/api/client'
import type { PortfolioSummary } from '@/core/types'

/** Fetch portfolio summary with profit calculations */
export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await apiClient.get<PortfolioSummary>('/portfolio/summary')
  return response.data
}
