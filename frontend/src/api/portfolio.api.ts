import { apiClient } from '@/core/api/client'
import type { PortfolioSummary, DepositHistoryResponse } from '@/core/types'

/** Fetch portfolio summary with profit calculations */
export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await apiClient.get<PortfolioSummary>('/portfolio/summary')
  return response.data
}

/** Fetch deposit/withdrawal history */
export async function fetchDepositHistory(): Promise<DepositHistoryResponse> {
  const response = await apiClient.get<DepositHistoryResponse>('/portfolio/deposits')
  return response.data
}
