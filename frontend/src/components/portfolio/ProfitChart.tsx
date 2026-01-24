import { useEffect, useRef, useCallback } from 'react'
import {
  createChart,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
} from 'lightweight-charts'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { ProfitDataPoint } from '@/core/types'
import { formatCurrency, formatDate } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface ProfitChartProps {
  data: ProfitDataPoint[]
  isLoading?: boolean
  className?: string
}

/** Transform profit data points to chart format */
function transformToChartData(data: ProfitDataPoint[]): LineData[] {
  return data.map((item) => ({
    time: item.date as Time,
    value: Number(item.value),
  }))
}

export function ProfitChart({ data, isLoading, className }: ProfitChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)

  // Cleanup chart
  const cleanupChart = useCallback(() => {
    if (resizeObserverRef.current) {
      resizeObserverRef.current.disconnect()
      resizeObserverRef.current = null
    }
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [])

  // Create chart when data is available
  useEffect(() => {
    // Don't create chart if no container or no data
    if (!chartContainerRef.current || data.length === 0) {
      return
    }

    // Clean up any existing chart first
    cleanupChart()

    // Create new chart
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
      timeScale: {
        borderColor: '#374151',
        timeVisible: false,
        tickMarkFormatter: (time: Time) => {
          const date = new Date(time as string)
          return `${date.getMonth() + 1}/${date.getDate()}`
        },
      },
      rightPriceScale: {
        borderColor: '#374151',
        scaleMargins: { top: 0.1, bottom: 0.1 },
        minimumWidth: 80,
      },
      handleScale: { axisPressedMouseMove: true },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
    })

    // Determine trend color
    const firstValue = Number(data[0].value)
    const lastValue = Number(data[data.length - 1].value)
    const isPositiveTrend = lastValue >= firstValue

    const lineSeries = chart.addSeries(LineSeries, {
      color: isPositiveTrend ? '#22c55e' : '#ef4444',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => formatCurrency(price),
        minMove: 1,
      },
    })

    // Set chart data
    const chartData = transformToChartData(data)
    lineSeries.setData(chartData)

    chartRef.current = chart
    seriesRef.current = lineSeries

    // Resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      if (width > 0 && height > 0) {
        chart.applyOptions({ width, height })
        chart.timeScale().fitContent()
      }
    })
    resizeObserver.observe(chartContainerRef.current)
    resizeObserverRef.current = resizeObserver

    // Initial fit
    requestAnimationFrame(() => {
      chart.timeScale().fitContent()
    })

    return cleanupChart
  }, [data, cleanupChart])

  if (isLoading) {
    return (
      <CommonCard title="수익 추이" className={className}>
        <Skeleton className="h-[300px] w-full" />
      </CommonCard>
    )
  }

  if (data.length === 0) {
    return (
      <CommonCard title="수익 추이" className={className}>
        <div className="flex h-[300px] items-center justify-center text-gray-400">
          수익 데이터가 없습니다
        </div>
      </CommonCard>
    )
  }

  // Calculate stats for header
  const startValue = Number(data[0].value)
  const endValue = Number(data[data.length - 1].value)
  const change = endValue - startValue
  const changePct = startValue > 0 ? ((change / startValue) * 100).toFixed(2) : '0.00'
  const isPositive = change >= 0

  return (
    <CommonCard
      title="수익 추이"
      headerAction={
        <div className="text-right">
          <p
            className={cn(
              'text-sm font-semibold',
              isPositive ? 'text-up' : 'text-down'
            )}
          >
            {isPositive ? '+' : ''}{changePct}%
          </p>
          <p className="text-xs text-gray-400">최근 {data.length}일</p>
        </div>
      }
      className={className}
    >
      <div className="relative">
        <div
          ref={chartContainerRef}
          className="h-[300px] w-full"
        />
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
        <span>{formatDate(data[0].date)}</span>
        <span>{formatDate(data[data.length - 1].date)}</span>
      </div>
    </CommonCard>
  )
}

export default ProfitChart
