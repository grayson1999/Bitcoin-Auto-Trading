import { LineSeries, type ISeriesApi, type IChartApi, type LineData, type Time } from 'lightweight-charts'
import type { OHLCVData } from '@/core/types'

interface MAConfig {
  period: number
  color: string
  lineWidth?: number
}

const MA_CONFIGS: Record<string, MAConfig> = {
  MA20: { period: 20, color: '#f59e0b', lineWidth: 1 },
  MA50: { period: 50, color: '#3b82f6', lineWidth: 1 },
  MA200: { period: 200, color: '#ef4444', lineWidth: 2 },
}

/** Calculate Simple Moving Average */
function calculateSMA(data: OHLCVData[], period: number): LineData[] {
  const result: LineData[] = []

  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({
      time: data[i].time as Time,
      value: sum / period,
    })
  }

  return result
}

/** Create MA indicator series */
export function createMAIndicator(
  chart: IChartApi,
  maType: 'MA20' | 'MA50' | 'MA200'
): ISeriesApi<'Line'> {
  const config = MA_CONFIGS[maType]

  const series = chart.addSeries(LineSeries, {
    color: config.color,
    lineWidth: (config.lineWidth || 1) as 1 | 2 | 3 | 4,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
  })

  return series
}

/** Update MA indicator data */
export function updateMAIndicator(
  series: ISeriesApi<'Line'>,
  data: OHLCVData[],
  maType: 'MA20' | 'MA50' | 'MA200'
): void {
  const config = MA_CONFIGS[maType]
  const maData = calculateSMA(data, config.period)
  series.setData(maData)
}

/** Remove MA indicator from chart */
export function removeMAIndicator(chart: IChartApi, series: ISeriesApi<'Line'>): void {
  chart.removeSeries(series)
}

export { MA_CONFIGS, calculateSMA }
