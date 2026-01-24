import type { PortfolioSummary, DepositHistoryResponse, ProfitDataPoint } from '@/core/types'

/** Generate mock profit chart data for the last 30 days */
function generateProfitChartData(): ProfitDataPoint[] {
  const data: ProfitDataPoint[] = []
  const today = new Date()
  let value = 10000000 // Starting value: 10,000,000 KRW

  for (let i = 29; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)

    // Simulate daily fluctuations between -2% and +3%
    const change = (Math.random() - 0.4) * 0.03
    value = value * (1 + change)

    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value),
    })
  }

  return data
}

/** Get mock portfolio summary */
export function getPortfolioSummaryMock(): PortfolioSummary {
  const profitChartData = generateProfitChartData()
  const currentValue = profitChartData[profitChartData.length - 1].value
  const totalDeposit = 10000000
  const cumulativeReturnPct = ((currentValue - totalDeposit) / totalDeposit) * 100

  // Calculate yesterday's value for today's return
  const yesterdayValue = profitChartData[profitChartData.length - 2].value
  const todayReturnPct = ((currentValue - yesterdayValue) / yesterdayValue) * 100
  const todayRealizedPnl = currentValue - yesterdayValue

  // Calculate MDD (Maximum Drawdown)
  let peak = profitChartData[0].value
  let maxDrawdown = 0
  for (const point of profitChartData) {
    if (point.value > peak) {
      peak = point.value
    }
    const drawdown = ((peak - point.value) / peak) * 100
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown
    }
  }

  return {
    total_deposit: totalDeposit,
    current_value: currentValue,
    cumulative_return_pct: cumulativeReturnPct,
    today_return_pct: todayReturnPct,
    today_realized_pnl: Math.round(todayRealizedPnl),
    total_trades: 47,
    win_count: 28,
    win_rate: 59.57,
    average_return_pct: 0.42,
    max_drawdown_pct: maxDrawdown,
    profit_chart_data: profitChartData,
  }
}

/** Get mock deposit history */
export function getDepositHistoryMock(): DepositHistoryResponse {
  const today = new Date()

  return {
    deposits: [
      {
        id: 1,
        amount: 5000000,
        deposited_at: new Date(today.getFullYear(), today.getMonth() - 2, 15).toISOString(),
      },
      {
        id: 2,
        amount: 3000000,
        deposited_at: new Date(today.getFullYear(), today.getMonth() - 1, 10).toISOString(),
      },
      {
        id: 3,
        amount: 2000000,
        deposited_at: new Date(today.getFullYear(), today.getMonth(), 5).toISOString(),
      },
    ],
    total: 10000000,
  }
}

/** Get empty portfolio summary for users without trades */
export function getEmptyPortfolioSummary(): PortfolioSummary {
  return {
    total_deposit: 0,
    current_value: 0,
    cumulative_return_pct: 0,
    today_return_pct: 0,
    today_realized_pnl: 0,
    total_trades: 0,
    win_count: 0,
    win_rate: 0,
    average_return_pct: 0,
    max_drawdown_pct: 0,
    profit_chart_data: [],
  }
}
