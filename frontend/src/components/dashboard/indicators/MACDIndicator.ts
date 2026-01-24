import { LineSeries, HistogramSeries, type ISeriesApi, type IChartApi, type LineData, type HistogramData, type Time } from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'

const MACD_FAST_PERIOD = 12
const MACD_SLOW_PERIOD = 26
const MACD_SIGNAL_PERIOD = 9

interface MACDResult {
  time: Time
  macd: number
  signal: number
  histogram: number
}

/** Calculate EMA */
function calculateEMA(data: number[], period: number): number[] {
  const multiplier = 2 / (period + 1)
  const ema: number[] = []

  // First value is SMA
  let sum = 0
  for (let i = 0; i < period; i++) {
    sum += data[i]
  }
  ema.push(sum / period)

  // Subsequent values use EMA formula
  for (let i = period; i < data.length; i++) {
    const value = (data[i] - ema[ema.length - 1]) * multiplier + ema[ema.length - 1]
    ema.push(value)
  }

  return ema
}

/** Calculate MACD values */
function calculateMACD(data: OHLCVData[]): MACDResult[] {
  if (data.length < MACD_SLOW_PERIOD + MACD_SIGNAL_PERIOD) return []

  const closePrices = data.map((d) => d.close)

  // Calculate EMAs
  const fastEMA = calculateEMA(closePrices, MACD_FAST_PERIOD)
  const slowEMA = calculateEMA(closePrices, MACD_SLOW_PERIOD)

  // Calculate MACD line (Fast EMA - Slow EMA)
  const macdLine: number[] = []
  const offset = MACD_SLOW_PERIOD - MACD_FAST_PERIOD

  for (let i = 0; i < slowEMA.length; i++) {
    macdLine.push(fastEMA[i + offset] - slowEMA[i])
  }

  // Calculate Signal line (EMA of MACD line)
  const signalLine = calculateEMA(macdLine, MACD_SIGNAL_PERIOD)

  // Build result
  const result: MACDResult[] = []
  const startIndex = MACD_SLOW_PERIOD - 1 + MACD_SIGNAL_PERIOD - 1

  for (let i = 0; i < signalLine.length; i++) {
    const macdIndex = i + MACD_SIGNAL_PERIOD - 1
    const dataIndex = startIndex + i

    if (dataIndex < data.length) {
      const macdValue = macdLine[macdIndex]
      const signalValue = signalLine[i]
      result.push({
        time: data[dataIndex].time as Time,
        macd: macdValue,
        signal: signalValue,
        histogram: macdValue - signalValue,
      })
    }
  }

  return result
}

export interface MACDSeries {
  macdLine: ISeriesApi<'Line'>
  signalLine: ISeriesApi<'Line'>
  histogram: ISeriesApi<'Histogram'>
}

/** Create MACD indicator pane */
export function createMACDPane(chart: IChartApi): MACDSeries {
  const macdLine = chart.addSeries(LineSeries, {
    color: '#3b82f6',
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: false,
    priceScaleId: 'macd',
  })

  const signalLine = chart.addSeries(LineSeries, {
    color: '#f59e0b',
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
    priceScaleId: 'macd',
  })

  const histogram = chart.addSeries(HistogramSeries, {
    priceLineVisible: false,
    lastValueVisible: false,
    priceScaleId: 'macd',
    priceFormat: {
      type: 'custom',
      formatter: (price: number) => price.toFixed(0),
    },
  })

  // Configure MACD price scale
  chart.priceScale('macd').applyOptions({
    borderVisible: false,
  })

  return { macdLine, signalLine, histogram }
}

/** Update MACD indicator data */
export function updateMACDIndicator(series: MACDSeries, data: OHLCVData[]): void {
  const macdData = calculateMACD(data)

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

  series.macdLine.setData(macdLineData)
  series.signalLine.setData(signalLineData)
  series.histogram.setData(histogramData)
}

/** Remove MACD indicator from chart */
export function removeMACDIndicator(chart: IChartApi, series: MACDSeries): void {
  chart.removeSeries(series.macdLine)
  chart.removeSeries(series.signalLine)
  chart.removeSeries(series.histogram)
}

export { MACD_FAST_PERIOD, MACD_SLOW_PERIOD, MACD_SIGNAL_PERIOD, calculateMACD }
