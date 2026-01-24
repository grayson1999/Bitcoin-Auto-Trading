import { useEffect, useRef } from 'react'
import {
  createChart,
  LineSeries,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type HistogramData,
} from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'
import { calculateMACD } from '../indicators/MACDIndicator'

interface MACDChartProps {
  data: OHLCVData[]
  height?: number
  onChartReady?: (chart: IChartApi) => void
  onChartDestroy?: () => void
}

interface MACDChartSeries {
  macdLine: ISeriesApi<'Line'>
  signalLine: ISeriesApi<'Line'>
  histogram: ISeriesApi<'Histogram'>
  zeroLine: ISeriesApi<'Line'>
}

export function MACDChart({
  data,
  height = 100,
  onChartReady,
  onChartDestroy,
}: MACDChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<MACDChartSeries | null>(null)

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
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScale: { axisPressedMouseMove: true },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
    })

    // Histogram (rendered first, behind lines)
    const histogram = chart.addSeries(HistogramSeries, {
      priceLineVisible: false,
      lastValueVisible: false,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => price.toFixed(0),
      },
    })

    // MACD line (blue)
    const macdLine = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => price.toFixed(0),
      },
    })

    // Signal line (orange)
    const signalLine = chart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    // Zero line (gray dotted)
    const zeroLine = chart.addSeries(LineSeries, {
      color: '#6b7280',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })

    chartRef.current = chart
    seriesRef.current = { macdLine, signalLine, histogram, zeroLine }

    onChartReady?.(chart)

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height,
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
      seriesRef.current = null
    }
  }, [height, onChartReady, onChartDestroy])

  // Update data
  useEffect(() => {
    if (!data?.length || !seriesRef.current || !chartRef.current) return

    const macdData = calculateMACD(data)
    if (macdData.length === 0) return

    const macdLineData: LineData[] = macdData.map((d) => ({
      time: d.time,
      value: d.macd,
    }))

    const signalLineData: LineData[] = macdData.map((d) => ({
      time: d.time,
      value: d.signal,
    }))

    const histogramData: HistogramData[] = macdData.map((d) => ({
      time: d.time,
      value: d.histogram,
      color: d.histogram >= 0 ? '#22c55e' : '#ef4444',
    }))

    // Zero line
    const firstTime = macdData[0].time
    const lastTime = macdData[macdData.length - 1].time
    const zeroLineData: LineData[] = [
      { time: firstTime, value: 0 },
      { time: lastTime, value: 0 },
    ]

    seriesRef.current.macdLine.setData(macdLineData)
    seriesRef.current.signalLine.setData(signalLineData)
    seriesRef.current.histogram.setData(histogramData)
    seriesRef.current.zeroLine.setData(zeroLineData)
  }, [data])

  return (
    <div className="relative w-full border-t border-gray-800">
      <div className="absolute left-2 top-1 z-10 text-xs text-gray-500">
        MACD(12,26,9)
      </div>
      <div
        ref={chartContainerRef}
        style={{ height }}
        className="w-full"
      />
    </div>
  )
}
