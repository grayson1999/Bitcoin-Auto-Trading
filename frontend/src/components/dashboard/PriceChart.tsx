import { useEffect, useRef, useState } from 'react'
import {
  createChart,
  CandlestickSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type Time,
  type MouseEventParams,
} from 'lightweight-charts'
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
} from './indicators/RSIIndicator'
import {
  createMACDPane,
  updateMACDIndicator,
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
  // Container Refs
  const mainChartContainerRef = useRef<HTMLDivElement>(null)
  const rsiChartContainerRef = useRef<HTMLDivElement>(null)
  const macdChartContainerRef = useRef<HTMLDivElement>(null)

  // Chart Instance Refs
  const mainChartRef = useRef<IChartApi | null>(null)
  const rsiChartRef = useRef<IChartApi | null>(null)
  const macdChartRef = useRef<IChartApi | null>(null)

  // Series Refs
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

  // Common chart options
  const getChartOptions = (options: any = {}) => ({
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
    timeScale: {
      borderColor: '#374151',
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: '#374151',
      scaleMargins: { top: 0.1, bottom: 0.1 },
      minimumWidth: 80,
    },
    handleScale: { axisPressedMouseMove: true },
    handleScroll: { mouseWheel: true, pressedMouseMove: true },
    ...options,
  })

  // Initialize Main Chart
  useEffect(() => {
    if (!mainChartContainerRef.current) return

    const chart = createChart(mainChartContainerRef.current, getChartOptions({
      // Override specific options if needed
    }))

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    mainChartRef.current = chart
    candleSeriesRef.current = candleSeries
    setIsChartReady(true)

    // Initial resize
    if (mainChartContainerRef.current) {
      chart.applyOptions({
        width: mainChartContainerRef.current.clientWidth,
        height: mainChartContainerRef.current.clientHeight,
      })
    }

    return () => {
      chart.remove()
      mainChartRef.current = null
      candleSeriesRef.current = null
      setIsChartReady(false)
    }
  }, [])

  // Initialize RSI Chart
  useEffect(() => {
    if (!showRSI || !rsiChartContainerRef.current) {
      if (rsiChartRef.current) {
        rsiChartRef.current.remove()
        rsiChartRef.current = null
        indicatorRefs.current.rsi = null
      }
      return
    }

    if (!rsiChartRef.current) {
      const chart = createChart(rsiChartContainerRef.current, getChartOptions({
        timeScale: {
          visible: true,
        },
      }))

      rsiChartRef.current = chart

      // Resize
      chart.applyOptions({
        width: rsiChartContainerRef.current.clientWidth,
        height: rsiChartContainerRef.current.clientHeight,
      })
    }
  }, [showRSI])

  // Initialize MACD Chart
  useEffect(() => {
    if (!showMACD || !macdChartContainerRef.current) {
      if (macdChartRef.current) {
        macdChartRef.current.remove()
        macdChartRef.current = null
        indicatorRefs.current.macd = null
      }
      return
    }

    if (!macdChartRef.current) {
      const chart = createChart(macdChartContainerRef.current, getChartOptions({
        // Default options work
      }))

      macdChartRef.current = chart

      // Resize
      chart.applyOptions({
        width: macdChartContainerRef.current.clientWidth,
        height: macdChartContainerRef.current.clientHeight,
      })
    }
  }, [showMACD])

  // Resize Handler for all charts
  useEffect(() => {
    const handleResize = () => {
      if (mainChartRef.current && mainChartContainerRef.current) {
        mainChartRef.current.applyOptions({
          width: mainChartContainerRef.current.clientWidth,
          height: mainChartContainerRef.current.clientHeight,
        })
      }
      if (rsiChartRef.current && rsiChartContainerRef.current) {
        rsiChartRef.current.applyOptions({
          width: rsiChartContainerRef.current.clientWidth,
          height: rsiChartContainerRef.current.clientHeight,
        })
      }
      if (macdChartRef.current && macdChartContainerRef.current) {
        macdChartRef.current.applyOptions({
          width: macdChartContainerRef.current.clientWidth,
          height: macdChartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [showRSI, showMACD])

  // Synchronization Logic
  useEffect(() => {
    const charts = [mainChartRef.current, rsiChartRef.current, macdChartRef.current].filter((c): c is IChartApi => c !== null)
    if (charts.length < 2) return

    // Sync Time Scale
    const mainTimeScale = mainChartRef.current?.timeScale()
    if (mainTimeScale) {
      const onVisibleLogicalRangeChanged = (range: any) => {
        if (!range) return
        charts.forEach(chart => {
          if (chart !== mainChartRef.current) {
            chart.timeScale().setVisibleLogicalRange(range)
          }
        })
      }
      mainTimeScale.subscribeVisibleLogicalRangeChange(onVisibleLogicalRangeChanged)
      return () => {
        mainTimeScale.unsubscribeVisibleLogicalRangeChange(onVisibleLogicalRangeChanged)
      }
    }
  }, [showRSI, showMACD, isChartReady]) // Re-run when charts change

  // Sync Crosshair
  useEffect(() => {
    const charts = [mainChartRef.current, rsiChartRef.current, macdChartRef.current].filter((c): c is IChartApi => c !== null)

    charts.forEach(chart => {
      chart.subscribeCrosshairMove((param: MouseEventParams) => {
        if (param.time) {
          charts.forEach(c => {
            if (c !== chart) {
              let series: ISeriesApi<any> | null = null

              if (c === mainChartRef.current) {
                series = candleSeriesRef.current
              } else if (c === rsiChartRef.current) {
                series = indicatorRefs.current.rsi
              } else if (c === macdChartRef.current && indicatorRefs.current.macd) {
                series = indicatorRefs.current.macd.macdLine
              }

              if (series) {
                c.setCrosshairPosition(0, param.time as Time, series)
              }
            }
          })
        }
      })
    })
  }, [showRSI, showMACD, isChartReady])


  // Data Updates - Main Chart
  useEffect(() => {
    if (!data?.items || !candleSeriesRef.current || !isChartReady) return
    const chartData = transformToChartData(data.items)
    candleSeriesRef.current.setData(chartData)
    // Only fit content on first load or manual trigger, not every update to avoid jumping
    // But for stream updates we might want strictly appending. For now full replace is fine.
  }, [data, isChartReady])

  // Data Updates - MA Indicators (on Main Chart)
  useEffect(() => {
    if (!mainChartRef.current || !isChartReady) return

    // MA20
    if (showMA20 && !indicatorRefs.current.ma20) {
      indicatorRefs.current.ma20 = createMAIndicator(mainChartRef.current, 'MA20')
    } else if (!showMA20 && indicatorRefs.current.ma20) {
      removeMAIndicator(mainChartRef.current, indicatorRefs.current.ma20)
      indicatorRefs.current.ma20 = null
    }
    if (indicatorRefs.current.ma20 && data?.items) updateMAIndicator(indicatorRefs.current.ma20, data.items, 'MA20')

    // MA50
    if (showMA50 && !indicatorRefs.current.ma50) {
      indicatorRefs.current.ma50 = createMAIndicator(mainChartRef.current, 'MA50')
    } else if (!showMA50 && indicatorRefs.current.ma50) {
      removeMAIndicator(mainChartRef.current, indicatorRefs.current.ma50)
      indicatorRefs.current.ma50 = null
    }
    if (indicatorRefs.current.ma50 && data?.items) updateMAIndicator(indicatorRefs.current.ma50, data.items, 'MA50')

    // MA200
    if (showMA200 && !indicatorRefs.current.ma200) {
      indicatorRefs.current.ma200 = createMAIndicator(mainChartRef.current, 'MA200')
    } else if (!showMA200 && indicatorRefs.current.ma200) {
      removeMAIndicator(mainChartRef.current, indicatorRefs.current.ma200)
      indicatorRefs.current.ma200 = null
    }
    if (indicatorRefs.current.ma200 && data?.items) updateMAIndicator(indicatorRefs.current.ma200, data.items, 'MA200')

  }, [showMA20, showMA50, showMA200, data, isChartReady])

  // Data Updates - RSI Chart
  useEffect(() => {
    if (!showRSI || !rsiChartRef.current || !data?.items) return

    if (!indicatorRefs.current.rsi) {
      indicatorRefs.current.rsi = createRSIPane(rsiChartRef.current)
    }

    if (indicatorRefs.current.rsi) {
      updateRSIIndicator(indicatorRefs.current.rsi, data.items)
    }
  }, [showRSI, data])

  // Data Updates - MACD Chart
  useEffect(() => {
    if (!showMACD || !macdChartRef.current || !data?.items) return

    if (!indicatorRefs.current.macd) {
      indicatorRefs.current.macd = createMACDPane(macdChartRef.current)
    }

    if (indicatorRefs.current.macd) {
      updateMACDIndicator(indicatorRefs.current.macd, data.items)
    }
  }, [showMACD, data])


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
    <div className={cn('flex flex-col w-full gap-1', className)}>
      <div
        ref={mainChartContainerRef}
        className={cn("w-full transition-all duration-300 h-[400px] sm:h-[500px]")}
      />

      {showRSI && (
        <div
          ref={rsiChartContainerRef}
          className="w-full h-[150px] shrink-0 border-t border-gray-800"
        />
      )}

      {showMACD && (
        <div
          ref={macdChartContainerRef}
          className="w-full h-[150px] shrink-0 border-t border-gray-800"
        />
      )}
    </div>
  )
}

export default PriceChart
