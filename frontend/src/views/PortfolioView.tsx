import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, AlertCircle, PieChart } from 'lucide-react'
import { fetchPortfolioSummary } from '@/api/portfolio.api'
import { CommonButton } from '@/core/components/CommonButton'
import { EmptyState } from '@/core/components/EmptyState'
import { CumulativeReturnCard } from '@/components/portfolio/CumulativeReturnCard'
import { TodayReturnCard } from '@/components/portfolio/TodayReturnCard'
import { TradeStatsCard } from '@/components/portfolio/TradeStatsCard'
import { ProfitChart } from '@/components/portfolio/ProfitChart'

export function PortfolioView() {
  const navigate = useNavigate()

  // Portfolio summary query
  const {
    data: portfolio,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['portfolioSummary'],
    queryFn: fetchPortfolioSummary,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute auto-refresh
  })

  const handleRefresh = () => {
    refetch()
  }

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">
          포트폴리오 데이터를 불러올 수 없습니다
        </h2>
        <p className="text-gray-400 mb-4">
          {error instanceof Error
            ? error.message
            : '알 수 없는 오류가 발생했습니다'}
        </p>
        <CommonButton onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          다시 시도
        </CommonButton>
      </div>
    )
  }

  // Empty state - No trades yet
  if (!isLoading && portfolio && portfolio.total_trades === 0) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">포트폴리오</h1>
            <p className="text-sm text-gray-400">투자 수익 현황</p>
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

        {/* Empty State */}
        <EmptyState
          icon={<PieChart className="h-8 w-8 text-muted-foreground" />}
          title="거래 기록이 없습니다"
          description="자동 거래가 시작되면 여기에서 수익 현황을 확인할 수 있습니다. 대시보드에서 시스템 상태를 확인하세요."
          action={
            <CommonButton variant="outline" onClick={() => navigate('/')}>
              대시보드로 이동
            </CommonButton>
          }
          className="py-20"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">포트폴리오</h1>
          <p className="text-sm text-gray-400">투자 수익 현황</p>
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

      {/* Summary Cards - 2 column grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CumulativeReturnCard
          totalDeposit={portfolio?.total_deposit ?? 0}
          currentValue={portfolio?.current_value ?? 0}
          cumulativeReturnPct={portfolio?.cumulative_return_pct ?? 0}
          isLoading={isLoading}
        />
        <TodayReturnCard
          todayReturnPct={portfolio?.today_return_pct ?? 0}
          todayRealizedPnl={portfolio?.today_realized_pnl ?? 0}
          isLoading={isLoading}
        />
      </div>

      {/* Profit Chart - Full width */}
      <ProfitChart
        data={portfolio?.profit_chart_data ?? []}
        isLoading={isLoading}
      />

      {/* Trade Stats - Full width */}
      <TradeStatsCard
        totalTrades={portfolio?.total_trades ?? 0}
        winCount={portfolio?.win_count ?? 0}
        winRate={portfolio?.win_rate ?? 0}
        averageReturnPct={portfolio?.average_return_pct ?? 0}
        maxDrawdownPct={portfolio?.max_drawdown_pct ?? 0}
        isLoading={isLoading}
      />
    </div>
  )
}

export default PortfolioView
