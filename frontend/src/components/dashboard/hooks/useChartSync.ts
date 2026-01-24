import { useCallback, useRef } from 'react'
import type { IChartApi, LogicalRange } from 'lightweight-charts'

interface ChartEntry {
  chart: IChartApi
  unsubscribe: () => void
}

export interface UseChartSyncReturn {
  registerChart: (id: string, chart: IChartApi) => void
  unregisterChart: (id: string) => void
}

/**
 * Hook for synchronizing time scales across multiple TradingView Lightweight Charts
 * Handles scroll and zoom synchronization between charts
 */
export function useChartSync(): UseChartSyncReturn {
  const chartsRef = useRef<Map<string, ChartEntry>>(new Map())
  const isSyncingRef = useRef(false)

  const syncTimeRange = useCallback((sourceId: string, range: LogicalRange | null) => {
    if (isSyncingRef.current || !range) return

    isSyncingRef.current = true

    chartsRef.current.forEach((entry, id) => {
      if (id !== sourceId) {
        entry.chart.timeScale().setVisibleLogicalRange(range)
      }
    })

    // Use requestAnimationFrame to prevent infinite loops
    requestAnimationFrame(() => {
      isSyncingRef.current = false
    })
  }, [])

  const registerChart = useCallback((id: string, chart: IChartApi) => {
    // Unregister existing chart with same id if exists
    const existing = chartsRef.current.get(id)
    if (existing) {
      existing.unsubscribe()
    }

    // Subscribe to time range changes
    const handler = (range: LogicalRange | null) => {
      syncTimeRange(id, range)
    }
    chart.timeScale().subscribeVisibleLogicalRangeChange(handler)

    // Create unsubscribe wrapper
    const unsubscribe = () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handler)
    }

    chartsRef.current.set(id, { chart, unsubscribe })

    // Sync to first chart's range if not the first
    if (chartsRef.current.size > 1) {
      const firstEntry = chartsRef.current.entries().next().value
      if (firstEntry && firstEntry[0] !== id) {
        const range = firstEntry[1].chart.timeScale().getVisibleLogicalRange()
        if (range) {
          chart.timeScale().setVisibleLogicalRange(range)
        }
      }
    }
  }, [syncTimeRange])

  const unregisterChart = useCallback((id: string) => {
    const entry = chartsRef.current.get(id)
    if (entry) {
      entry.unsubscribe()
      chartsRef.current.delete(id)
    }
  }, [])

  return {
    registerChart,
    unregisterChart,
  }
}
