import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface TradingStatusResponse {
  trading_enabled: boolean
  ticker: string // e.g., "KRW-SOL"
}

export interface SystemConfig {
  key: string
  value: string | number | boolean
  source: 'db' | 'env'
  updated_at?: string
}

export interface ConfigListResponse {
  configs: SystemConfig[]
  count: number
}

/**
 * 거래 상태 및 티커 조회
 * @returns trading_enabled, ticker (e.g., "KRW-SOL")
 */
export async function fetchTradingStatus(): Promise<TradingStatusResponse> {
  const response = await axios.get<TradingStatusResponse>(
    `${API_BASE}/api/v1/config/trading-status`
  )
  return response.data
}

/**
 * 티커에서 코인 심볼 추출
 * @param ticker "KRW-SOL" -> "SOL"
 */
export function extractCurrencyFromTicker(ticker: string): string {
  const parts = ticker.split('-')
  return parts.length > 1 ? parts[1] : ticker
}

/**
 * 모든 설정 조회
 */
export async function fetchAllConfigs(): Promise<ConfigListResponse> {
  const response = await axios.get<ConfigListResponse>(
    `${API_BASE}/api/v1/config`
  )
  return response.data
}
