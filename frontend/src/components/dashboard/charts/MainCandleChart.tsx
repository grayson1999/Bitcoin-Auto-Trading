import { useEffect, useRef } from 'react'
import {
  createChart,
  CandlestickSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type Time,
} from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'
import {
  createMAIndicator,
  updateMAIndicator,
  removeMAIndicator,
} from '../indicators/MAIndicator'

interface MainCandleChartProps {
  data: OHLCVData[]
  showMA20?: boolean
  showMA50?: boolean
  showMA200?: boolean
  onChartReady?: (chart: IChartApi) => void
  onChartDestroy?: () => void
  style?: React.CSSProperties
}

interface IndicatorRefs {
  ma20: ISeriesApi<'Line'> | null
  ma50: ISeriesApi<'Line'> | null
  ma200: ISeriesApi<'Line'> | null
}

function transformToChartData(data: OHLCVData[]): CandlestickData[] {
  return data.map((item) => ({
    time: (typeof item.time === 'number'
      ? item.time
      : new Date(item.time).getTime() / 1000) as Time,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  }))
}

export function MainCandleChart({
  data,
  showMA20 = false,
  showMA50 = false,
  showMA200 = false,
  onChartReady,
  onChartDestroy,
  style,
}: MainCandleChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const indicatorRefs = useRef<IndicatorRefs>({
    ma20: null,
    ma50: null,
    ma200: null,
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
        scaleMargins: { top: 0.05, bottom: 0.05 },
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

    // Notify parent
    onChartReady?.(chart)

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
      onChartDestroy?.()
      chart.remove()
      chartRef.current = null
      candleSeriesRef.current = null
    }
  }, [onChartReady, onChartDestroy])

  // Update chart data
  useEffect(() => {
    if (!data?.length || !candleSeriesRef.current || !chartRef.current) return

    const chartData = transformToChartData(data)
    candleSeriesRef.current.setData(chartData)
    chartRef.current.timeScale().fitContent()
  }, [data])

  // Handle MA20
  useEffect(() => {
    if (!chartRef.current) return

    if (showMA20 && !indicatorRefs.current.ma20) {
      indicatorRefs.current.ma20 = createMAIndicator(chartRef.current, 'MA20')
    } else if (!showMA20 && indicatorRefs.current.ma20) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma20)
      indicatorRefs.current.ma20 = null
    }

    if (indicatorRefs.current.ma20 && data?.length) {
      updateMAIndicator(indicatorRefs.current.ma20, data, 'MA20')
    }
  }, [showMA20, data])

  // Handle MA50
  useEffect(() => {
    if (!chartRef.current) return

    if (showMA50 && !indicatorRefs.current.ma50) {
      indicatorRefs.current.ma50 = createMAIndicator(chartRef.current, 'MA50')
    } else if (!showMA50 && indicatorRefs.current.ma50) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma50)
      indicatorRefs.current.ma50 = null
    }

    if (indicatorRefs.current.ma50 && data?.length) {
      updateMAIndicator(indicatorRefs.current.ma50, data, 'MA50')
    }
  }, [showMA50, data])

  // Handle MA200
  useEffect(() => {
    if (!chartRef.current) return

    if (showMA200 && !indicatorRefs.current.ma200) {
      indicatorRefs.current.ma200 = createMAIndicator(chartRef.current, 'MA200')
    } else if (!showMA200 && indicatorRefs.current.ma200) {
      removeMAIndicator(chartRef.current, indicatorRefs.current.ma200)
      indicatorRefs.current.ma200 = null
    }

    if (indicatorRefs.current.ma200 && data?.length) {
      updateMAIndicator(indicatorRefs.current.ma200, data, 'MA200')
    }
  }, [showMA200, data])

  return (
    <div
      ref={chartContainerRef}
      style={style}
      className="w-full"
    />
  )
}
