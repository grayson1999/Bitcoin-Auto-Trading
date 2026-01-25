import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { fetchDashboardSummary } from '@/api/dashboard.api'
import { fetchRiskStatus } from '@/api/risk.api'
import { CommonButton } from '@/core/components/CommonButton'
import { CommonCard } from '@/core/components/CommonCard'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { IndicatorControls } from '@/components/dashboard/IndicatorControls'
import { MetricCards } from '@/components/dashboard/MetricCards'
import { PositionCard } from '@/components/dashboard/PositionCard'
import { BalanceCard } from '@/components/dashboard/BalanceCard'
import { LatestSignalCard } from '@/components/dashboard/LatestSignalCard'
import { RiskStatusCard } from '@/components/dashboard/RiskStatusCard'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'
import type { ChartSettings } from '@/core/types'

const DEFAULT_CHART_SETTINGS: ChartSettings = {
  interval: '5m',
  showMA20: true,
  showMA50: false,
  showMA200: false,
  showRSI: false,
  showMACD: false,
}

export function DashboardView() {
  const { currency } = useTradingConfig()
  const [chartSettings, setChartSettings] = useState<ChartSettings>(DEFAULT_CHART_SETTINGS)

  // Dashboard summary query with 5s auto-refresh
  const {
    data: dashboard,
    isLoading: isDashboardLoading,
    isError: isDashboardError,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: fetchDashboardSummary,
    refetchInterval: 5000,
    staleTime: 4000,
  })

  // Risk status query with 5s auto-refresh
  const {
    data: riskStatus,
    isLoading: isRiskLoading,
  } = useQuery({
    queryKey: ['riskStatus'],
    queryFn: fetchRiskStatus,
    refetchInterval: 5000,
    staleTime: 4000,
  })

  const handleRefresh = () => {
    refetchDashboard()
  }

  // Error state
  if (isDashboardError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">데이터를 불러올 수 없습니다</h2>
        <p className="text-gray-400 mb-4">
          {dashboardError instanceof Error ? dashboardError.message : '알 수 없는 오류가 발생했습니다'}
        </p>
        <CommonButton onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          다시 시도
        </CommonButton>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">대시보드</h1>
          <p className="text-sm text-gray-400">실시간 시세 및 포지션 모니터링</p>
        </div>
        <CommonButton
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          새로고침
        </CommonButton>
      </div>

      {/* Metric Cards */}
      <MetricCards
        currentPrice={dashboard?.current_price ?? 0}
        priceChange24h={dashboard?.price_change_24h ?? 0}
        dailyPnl={dashboard?.daily_pnl ?? 0}
        dailyPnlPct={dashboard?.daily_pnl_pct ?? 0}
        todayTradeCount={dashboard?.today_trade_count ?? 0}
        isLoading={isDashboardLoading}
      />

      {/* Chart Section */}
      <CommonCard title={`${currency}/KRW 차트`} className="overflow-hidden">
        <div className="space-y-4">
          <IndicatorControls
            settings={chartSettings}
            onSettingsChange={setChartSettings}
          />
          <PriceChart
            interval={chartSettings.interval}
            showMA20={chartSettings.showMA20}
            showMA50={chartSettings.showMA50}
            showMA200={chartSettings.showMA200}
            showRSI={chartSettings.showRSI}
            showMACD={chartSettings.showMACD}
            className=""
          />
        </div>
      </CommonCard>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Position Card */}
        <PositionCard
          position={dashboard?.position ?? null}
          isLoading={isDashboardLoading}
        />

        {/* Balance Card */}
        <BalanceCard
          balance={dashboard?.balance ?? null}
          isLoading={isDashboardLoading}
        />

        {/* Latest Signal Card */}
        <LatestSignalCard
          signal={dashboard?.latest_signal ?? null}
          isLoading={isDashboardLoading}
        />

        {/* Risk Status Card */}
        <RiskStatusCard
          riskStatus={riskStatus ?? null}
          isLoading={isRiskLoading}
        />
      </div>
    </div>
  )
}

export default DashboardView
