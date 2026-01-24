import { useEffect, useRef } from 'react'
import {
  createChart,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type LineData,
} from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'
import { calculateRSI, RSI_OVERBOUGHT, RSI_OVERSOLD } from '../indicators/RSIIndicator'

interface RSIChartProps {
  data: OHLCVData[]
  height?: number
  onChartReady?: (chart: IChartApi) => void
  onChartDestroy?: () => void
}

interface RSISeries {
  rsiLine: ISeriesApi<'Line'>
  overboughtLine: ISeriesApi<'Line'>
  oversoldLine: ISeriesApi<'Line'>
}

export function RSIChart({
  data,
  height = 80,
  onChartReady,
  onChartDestroy,
}: RSIChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<RSISeries | null>(null)

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
        autoScale: false,
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: false,
        visible: false,
      },
      handleScale: { axisPressedMouseMove: true },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
    })

    // RSI line (purple)
    const rsiLine = chart.addSeries(LineSeries, {
      color: '#8b5cf6',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => price.toFixed(1),
      },
    })

    // Overbought line (70) - dotted red
    const overboughtLine = chart.addSeries(LineSeries, {
      color: '#ef4444',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })

    // Oversold line (30) - dotted green
    const oversoldLine = chart.addSeries(LineSeries, {
      color: '#22c55e',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })

    // Set fixed price scale for RSI (0-100)
    chart.priceScale('right').applyOptions({
      autoScale: false,
      scaleMargins: { top: 0.05, bottom: 0.05 },
    })

    chartRef.current = chart
    seriesRef.current = { rsiLine, overboughtLine, oversoldLine }

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

    const rsiData = calculateRSI(data)
    seriesRef.current.rsiLine.setData(rsiData as LineData[])

    // Create horizontal lines for overbought/oversold
    if (rsiData.length > 0) {
      const firstTime = rsiData[0].time
      const lastTime = rsiData[rsiData.length - 1].time

      const overboughtData: LineData[] = [
        { time: firstTime, value: RSI_OVERBOUGHT },
        { time: lastTime, value: RSI_OVERBOUGHT },
      ]
      const oversoldData: LineData[] = [
        { time: firstTime, value: RSI_OVERSOLD },
        { time: lastTime, value: RSI_OVERSOLD },
      ]

      seriesRef.current.overboughtLine.setData(overboughtData)
      seriesRef.current.oversoldLine.setData(oversoldData)
    }
  }, [data])

  return (
    <div className="relative w-full border-t border-gray-800">
      <div className="absolute left-2 top-1 z-10 text-xs text-gray-500">RSI(14)</div>
      <div
        ref={chartContainerRef}
        style={{ height }}
        className="w-full"
      />
    </div>
  )
}
