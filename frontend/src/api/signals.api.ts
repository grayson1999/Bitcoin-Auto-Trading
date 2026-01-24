import { apiClient } from '@/core/api/client'
import type { TradingSignal, TradingSignalListResponse, SignalType, TradingSignalDetail } from '@/core/types'

export interface FetchSignalsParams {
  limit?: number
  offset?: number
  type?: SignalType | 'all'
}

/** Fetch trading signals list with optional type filter */
export async function fetchSignals(params?: FetchSignalsParams): Promise<TradingSignalListResponse> {
  const queryParams: Record<string, number | string> = {
    limit: params?.limit ?? 20,
    offset: params?.offset ?? 0,
  }

  // Add type filter if specified and not 'all'
  if (params?.type && params.type !== 'all') {
    queryParams.signal_type = params.type
  }

  const response = await apiClient.get<TradingSignalListResponse>('/signals', {
    params: queryParams,
  })
  return response.data
}

/** Fetch latest signal */
export async function fetchLatestSignal(): Promise<TradingSignal | null> {
  const response = await apiClient.get<TradingSignal | null>('/signals/latest')
  return response.data
}

/** Fetch signal detail by ID */
export async function fetchSignalDetail(id: string): Promise<TradingSignalDetail> {
  const response = await apiClient.get<TradingSignalDetail>(`/signals/${id}`)
  return response.data
}

/** Generate signal response */
export interface GenerateSignalResponse {
  signal: TradingSignal
  message: string
}

/** Generate a new AI signal manually */
export async function generateSignal(): Promise<GenerateSignalResponse> {
  const response = await apiClient.post<GenerateSignalResponse>('/signals/generate')
  return response.data
}
