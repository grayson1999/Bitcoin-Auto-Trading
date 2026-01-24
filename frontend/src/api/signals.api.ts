import { apiClient } from '@/core/api/client'
import type { TradingSignal, TradingSignalListResponse } from '@/core/types'

export interface FetchSignalsParams {
  limit?: number
  offset?: number
}

/** Fetch trading signals list */
export async function fetchSignals(params?: FetchSignalsParams): Promise<TradingSignalListResponse> {
  const response = await apiClient.get<TradingSignalListResponse>('/signals', {
    params: {
      limit: params?.limit ?? 50,
      offset: params?.offset ?? 0,
    },
  })
  return response.data
}

/** Fetch latest signal */
export async function fetchLatestSignal(): Promise<TradingSignal | null> {
  const response = await apiClient.get<TradingSignal | null>('/signals/latest')
  return response.data
}
