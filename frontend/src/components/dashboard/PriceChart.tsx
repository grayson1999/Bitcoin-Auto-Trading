import { useEffect, useRef, useState } from 'react'
import { createChart, CandlestickSeries, type IChartApi, type ISeriesApi, type CandlestickData, type Time } from 'lightweight-charts'
import { useQuery } from '@tanstack/react-query'
import { fetchMarketHistory } from '@/api/market.api'
import type { ChartInterval, OHLCVData } from '@/core/types'
import { cn } from '@/core/utils/cn'
import { Skeleton } from '@/core/components/ui/skeleton'
import {
  createMAIndicator,
  updateMAIndicator,
  removeMAIndicator,
} from './indicators/MAIndicator'
import {
  createRSIPane,
  updateRSIIndicator,
  removeRSIIndicator,
} from './indicators/RSIIndicator'
import {
  createMACDPane,
  updateMACDIndicator,
  removeMACDIndicator,
  type MACDSeries,
} from './indicators/MACDIndicator'

interface PriceChartProps {
  interval: ChartInterval
  showMA20?: boolean
  showMA50?: boolean
  showMA200?: boolean
  showRSI?: boolean
  showMACD?: boolean
  className?: string
}

interface IndicatorRefs {
  ma20: ISeriesApi<'Line'> | null
  ma50: ISeriesApi<'Line'> | null
  ma200: ISeriesApi<'Line'> | null
  rsi: ISeriesApi<'Line'> | null
  macd: MACDSeries | null
}

function transformToChartData(data: OHLCVData[]): CandlestickData[] {
  return data.map((item) => ({
    time: (typeof item.time === 'number' ? item.time : new Date(item.time).getTime() / 1000) as Time,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  }))
}

export function PriceChart({
  interval,
  showMA20 = false,
  showMA50 = false,
  showMA200 = false,
  showRSI = false,
  showMACD = false,
  className,
}: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const indicatorRefs = useRef<IndicatorRefs>({
    ma20: null,
    ma50: null,
    ma200: null,
    rsi: null,
    macd: null,
  })
  const [isChartReady, setIsChartReady] = useState(false)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['marketHistory', interval],
    queryFn: () => fetchMarketHistory({ interval, count: 200 }),
    refetchInterval: 5000,
    staleTime: 4000,
  })

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: '#6b7280', width: 1, style: 2 },
        horzLine: { color: '#6b7280', width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: '#374151',
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScale: { axisPressedMouseMove: true },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    chartRef.current = chart
    candleSeriesRef.current = candleSeries
    setIsChartReady(true)

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
      candleSeriesRef.current = null
      setIsChartReady(false)
    }
  }, [])

  // Update chart data
  useEffect(() => {
    if (!data?.items || !candleSeriesRef.current || !isChartReady) return

    const chartData = transformToChartData(data.items)
    candleSeriesRef.current.setData(chartData)

    // Fit content to view
    chartRef.current?.timeScale().fitContent()
  }, [data, isChartReady])

  // Handle MA20 indicator
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return

    if (showMA20 && !indicatorRefs.current.ma20) {
      indicatorRefs.current.ma20 = createMAIndicator(chartRef.current, 'MA20')
    } else if (!showMA20 && indicatorRefs.current.ma20) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma20)
      indicatorRefs.current.ma20 = null
    }

    if (indicatorRefs.current.ma20 && data?.items) {
      updateMAIndicator(indicatorRefs.current.ma20, data.items, 'MA20')
    }
  }, [showMA20, data, isChartReady])

  // Handle MA50 indicator
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return

    if (showMA50 && !indicatorRefs.current.ma50) {
      indicatorRefs.current.ma50 = createMAIndicator(chartRef.current, 'MA50')
    } else if (!showMA50 && indicatorRefs.current.ma50) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma50)
      indicatorRefs.current.ma50 = null
    }

    if (indicatorRefs.current.ma50 && data?.items) {
      updateMAIndicator(indicatorRefs.current.ma50, data.items, 'MA50')
    }
  }, [showMA50, data, isChartReady])

  // Handle MA200 indicator
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return

    if (showMA200 && !indicatorRefs.current.ma200) {
      indicatorRefs.current.ma200 = createMAIndicator(chartRef.current, 'MA200')
    } else if (!showMA200 && indicatorRefs.current.ma200) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma200)
      indicatorRefs.current.ma200 = null
    }

    if (indicatorRefs.current.ma200 && data?.items) {
      updateMAIndicator(indicatorRefs.current.ma200, data.items, 'MA200')
    }
  }, [showMA200, data, isChartReady])

  // Handle RSI indicator
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return

    if (showRSI && !indicatorRefs.current.rsi) {
      indicatorRefs.current.rsi = createRSIPane(chartRef.current)
    } else if (!showRSI && indicatorRefs.current.rsi) {
      removeRSIIndicator(chartRef.current, indicatorRefs.current.rsi)
      indicatorRefs.current.rsi = null
    }

    if (indicatorRefs.current.rsi && data?.items) {
      updateRSIIndicator(indicatorRefs.current.rsi, data.items)
    }
  }, [showRSI, data, isChartReady])

  // Handle MACD indicator
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return

    if (showMACD && !indicatorRefs.current.macd) {
      indicatorRefs.current.macd = createMACDPane(chartRef.current)
    } else if (!showMACD && indicatorRefs.current.macd) {
      removeMACDIndicator(chartRef.current, indicatorRefs.current.macd)
      indicatorRefs.current.macd = null
    }

    if (indicatorRefs.current.macd && data?.items) {
      updateMACDIndicator(indicatorRefs.current.macd, data.items)
    }
  }, [showMACD, data, isChartReady])

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

  return (
    <div
      ref={chartContainerRef}
      className={cn('h-[400px] w-full', className)}
    />
  )
}

export default PriceChart
