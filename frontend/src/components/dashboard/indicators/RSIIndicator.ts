import { LineSeries, type ISeriesApi, type IChartApi, type LineData, type Time } from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'

const RSI_PERIOD = 14
const RSI_OVERBOUGHT = 70
const RSI_OVERSOLD = 30

interface RSIResult {
  time: Time
  value: number
}

/** Calculate RSI values */
function calculateRSI(data: OHLCVData[], period: number = RSI_PERIOD): RSIResult[] {
  if (data.length < period + 1) return []

  const result: RSIResult[] = []
  const gains: number[] = []
  const losses: number[] = []

  // Calculate initial gains and losses
  for (let i = 1; i <= period; i++) {
    const change = data[i].close - data[i - 1].close
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? Math.abs(change) : 0)
  }

  let avgGain = gains.reduce((a, b) => a + b, 0) / period
  let avgLoss = losses.reduce((a, b) => a + b, 0) / period

  // First RSI value
  const firstRS = avgLoss === 0 ? 100 : avgGain / avgLoss
  const firstRSI = 100 - 100 / (1 + firstRS)
  result.push({
    time: data[period].time as Time,
    value: firstRSI,
  })

  // Calculate subsequent RSI values using Wilder's smoothing
  for (let i = period + 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    const currentGain = change > 0 ? change : 0
    const currentLoss = change < 0 ? Math.abs(change) : 0

    avgGain = (avgGain * (period - 1) + currentGain) / period
    avgLoss = (avgLoss * (period - 1) + currentLoss) / period

    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    const rsi = 100 - 100 / (1 + rs)

    result.push({
      time: data[i].time as Time,
      value: rsi,
    })
  }

  return result
}

/** Create RSI indicator pane */
export function createRSIPane(chart: IChartApi): ISeriesApi<'Line'> {
  const series = chart.addSeries(LineSeries, {
    color: '#8b5cf6',
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: true,
    priceScaleId: 'rsi',
    priceFormat: {
      type: 'custom',
      formatter: (price: number) => price.toFixed(1),
    },
  })

  // Configure RSI price scale
  chart.priceScale('rsi').applyOptions({
    borderVisible: false,
  })

  return series
}

/** Update RSI indicator data */
export function updateRSIIndicator(series: ISeriesApi<'Line'>, data: OHLCVData[]): void {
  const rsiData = calculateRSI(data)
  series.setData(rsiData as LineData[])
}

/** Remove RSI indicator from chart */
export function removeRSIIndicator(chart: IChartApi, series: ISeriesApi<'Line'>): void {
  chart.removeSeries(series)
}

export { RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, calculateRSI }
