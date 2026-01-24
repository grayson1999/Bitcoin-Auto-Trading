import { apiClient } from '@/core/api/client'
import type { MarketData, OHLCVData, MarketSummary, ChartInterval } from '@/core/types'

interface MarketHistoryParams {
  interval?: ChartInterval
  count?: number
}

interface MarketHistoryResponse {
  items: OHLCVData[]
  total: number
}

/** Fetch current market data */
export async function fetchMarketData(): Promise<MarketData> {
  const response = await apiClient.get<MarketData>('/market')
  return response.data
}

/** Fetch market history for charts */
export async function fetchMarketHistory(
  params: MarketHistoryParams = {}
): Promise<MarketHistoryResponse> {
  const { interval = '1m', count = 200 } = params
  const response = await apiClient.get<MarketHistoryResponse>('/market/history', {
    params: { interval, count },
  })
  return response.data
}

/** Fetch market summary statistics */
export async function fetchMarketSummary(): Promise<MarketSummary> {
  const response = await apiClient.get<MarketSummary>('/market/summary')
  return response.data
}

/** Fetch latest market data from DB */
export async function fetchLatestMarketData(): Promise<MarketData> {
  const response = await apiClient.get<MarketData>('/market/latest')
  return response.data
}

/** Fetch data collector stats */
export async function fetchCollectorStats(): Promise<{
  is_running: boolean
  last_collection: string | null
  total_records: number
}> {
  const response = await apiClient.get('/market/collector/stats')
  return response.data
}
