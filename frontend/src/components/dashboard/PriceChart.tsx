import { useCallback, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { IChartApi } from 'lightweight-charts'
import { fetchMarketHistory } from '@/api/market.api'
import type { ChartInterval } from '@/core/types'
import { cn } from '@/core/utils/cn'
import { Skeleton } from '@/core/components/ui/skeleton'
import { MainCandleChart, RSIChart, MACDChart } from './charts'
import { useChartSync } from './hooks/useChartSync'

interface PriceChartProps {
  interval: ChartInterval
  showMA20?: boolean
  showMA50?: boolean
  showMA200?: boolean
  showRSI?: boolean
  showMACD?: boolean
  className?: string
}

const RSI_HEIGHT = 80
const MACD_HEIGHT = 100

export function PriceChart({
  interval,
  showMA20 = false,
  showMA50 = false,
  showMA200 = false,
  showRSI = false,
  showMACD = false,
  className,
}: PriceChartProps) {
  const { registerChart, unregisterChart } = useChartSync()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['marketHistory', interval],
    queryFn: () => fetchMarketHistory({ interval, count: 200 }),
    refetchInterval: 5000,
    staleTime: 4000,
  })

  // Calculate heights dynamically
  const heights = useMemo(() => {
    const rsiHeight = showRSI ? RSI_HEIGHT : 0
    const macdHeight = showMACD ? MACD_HEIGHT : 0
    const totalIndicatorHeight = rsiHeight + macdHeight
    return {
      main: `calc(100% - ${totalIndicatorHeight}px)`,
      rsi: rsiHeight,
      macd: macdHeight,
    }
  }, [showRSI, showMACD])

  // Chart callbacks for sync
  const handleMainChartReady = useCallback(
    (chart: IChartApi) => {
      registerChart('main', chart)
    },
    [registerChart]
  )

  const handleMainChartDestroy = useCallback(() => {
    unregisterChart('main')
  }, [unregisterChart])

  const handleRSIChartReady = useCallback(
    (chart: IChartApi) => {
      registerChart('rsi', chart)
    },
    [registerChart]
  )

  const handleRSIChartDestroy = useCallback(() => {
    unregisterChart('rsi')
  }, [unregisterChart])

  const handleMACDChartReady = useCallback(
    (chart: IChartApi) => {
      registerChart('macd', chart)
    },
    [registerChart]
  )

  const handleMACDChartDestroy = useCallback(() => {
    unregisterChart('macd')
  }, [unregisterChart])

  if (isLoading && !data) {
    return (
      <div className={cn('h-[400px] w-full', className)}>
        <Skeleton className="h-full w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className={cn('flex h-[400px] w-full items-center justify-center', className)}>
        <div className="text-center text-red-400">
          <p>차트 데이터를 불러올 수 없습니다</p>
          <p className="text-sm text-gray-500">{error?.message}</p>
        </div>
      </div>
    )
  }

  const chartData = data?.items ?? []

  return (
    <div className={cn('flex h-[400px] w-full flex-col', className)}>
      {/* Main Candle Chart */}
      <MainCandleChart
        data={chartData}
        showMA20={showMA20}
        showMA50={showMA50}
        showMA200={showMA200}
        onChartReady={handleMainChartReady}
        onChartDestroy={handleMainChartDestroy}
        style={{ height: heights.main }}
      />

      {/* RSI Panel */}
      {showRSI && (
        <RSIChart
          data={chartData}
          height={heights.rsi}
          onChartReady={handleRSIChartReady}
          onChartDestroy={handleRSIChartDestroy}
        />
      )}

      {/* MACD Panel */}
      {showMACD && (
        <MACDChart
          data={chartData}
          height={heights.macd}
          onChartReady={handleMACDChartReady}
          onChartDestroy={handleMACDChartDestroy}
        />
      )}
    </div>
  )
}

export default PriceChart
