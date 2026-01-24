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

/** Backend API response format */
interface BackendMarketDataItem {
  id: number
  symbol: string
  timestamp: string
  price: number | string
  volume: number | string
  high_price: number | string
  low_price: number | string
  trade_count: number
}

interface BackendMarketHistoryResponse {
  items: BackendMarketDataItem[]
  total: number
}

/** Convert ChartInterval to minutes */
const INTERVAL_TO_MINUTES: Record<ChartInterval, number> = {
  '1m': 1,
  '5m': 5,
  '15m': 15,
  '1h': 60,
}

/** Transform backend market data to OHLCV format for charts */
function transformToOHLCV(
  items: BackendMarketDataItem[],
  intervalMinutes: number
): OHLCVData[] {
  if (items.length === 0) return []

  // Group data by time bucket
  const buckets: Map<number, BackendMarketDataItem[]> = new Map()

  for (const item of items) {
    const timestamp = new Date(item.timestamp).getTime()
    // Round down to interval bucket
    const bucketTime = Math.floor(timestamp / (intervalMinutes * 60 * 1000)) * (intervalMinutes * 60 * 1000)

    if (!buckets.has(bucketTime)) {
      buckets.set(bucketTime, [])
    }
    buckets.get(bucketTime)!.push(item)
  }

  // Convert each bucket to OHLCV candle
  const ohlcvData: OHLCVData[] = []

  const sortedBuckets = Array.from(buckets.entries()).sort((a, b) => a[0] - b[0])

  for (const [bucketTime, bucketItems] of sortedBuckets) {
    // Sort items by timestamp within bucket
    bucketItems.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    const prices = bucketItems.map(item => Number(item.price))
    const volumes = bucketItems.map(item => Number(item.volume))

    ohlcvData.push({
      time: bucketTime / 1000, // Convert to seconds for lightweight-charts
      open: prices[0],
      high: Math.max(...prices),
      low: Math.min(...prices),
      close: prices[prices.length - 1],
      volume: volumes.reduce((a, b) => a + b, 0) / volumes.length,
    })
  }

  return ohlcvData
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

  // Convert ChartInterval ('1m', '5m', etc.) to minutes
  const intervalMinutes = INTERVAL_TO_MINUTES[interval]

  // Calculate hours needed to get `count` candles
  // e.g., 200 candles at 5m interval = 1000 minutes = ~17 hours
  const hours = Math.min(Math.ceil((count * intervalMinutes) / 60), 168)

  const response = await apiClient.get<BackendMarketHistoryResponse>('/market/history', {
    params: {
      interval: intervalMinutes,
      limit: 1000, // Get more raw data points for OHLCV aggregation
      hours,
    },
  })

  // Transform backend data to OHLCV format
  const ohlcvItems = transformToOHLCV(response.data.items, intervalMinutes)

  // Return only the requested count (most recent)
  const limitedItems = ohlcvItems.slice(-count)

  return {
    items: limitedItems,
    total: limitedItems.length,
  }
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
