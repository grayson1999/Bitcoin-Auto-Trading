import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'

interface MetricCardsProps {
  currentPrice: number
  priceChange24h: number
  dailyPnl: number
  dailyPnlPct: number
  todayTradeCount: number
  isLoading?: boolean
  className?: string
}

interface MetricCardItemProps {
  title: string
  value: string
  subValue?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  isLoading?: boolean
}

function MetricCardItem({
  title,
  value,
  subValue,
  icon,
  trend = 'neutral',
  isLoading,
}: MetricCardItemProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="mt-2 h-7 w-32" />
        <Skeleton className="mt-1 h-4 w-16" />
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
      <div className="flex items-center gap-2 text-gray-400">
        {icon}
        <span className="text-sm">{title}</span>
      </div>
      <p
        className={cn(
          'mt-2 text-xl font-bold',
          trend === 'up' && 'text-green-400',
          trend === 'down' && 'text-red-400',
          trend === 'neutral' && 'text-white'
        )}
      >
        {value}
      </p>
      {subValue && (
        <p
          className={cn(
            'text-sm',
            trend === 'up' && 'text-green-400/80',
            trend === 'down' && 'text-red-400/80',
            trend === 'neutral' && 'text-gray-400'
          )}
        >
          {subValue}
        </p>
      )}
    </div>
  )
}

export function MetricCards({
  currentPrice,
  priceChange24h,
  dailyPnl,
  dailyPnlPct,
  todayTradeCount,
  isLoading,
  className,
}: MetricCardsProps) {
  const priceTrend = priceChange24h >= 0 ? 'up' : 'down'
  const pnlTrend = dailyPnl >= 0 ? 'up' : dailyPnl < 0 ? 'down' : 'neutral'

  return (
    <div className={cn('grid grid-cols-2 gap-4 lg:grid-cols-4', className)}>
      <MetricCardItem
        title="BTC 현재가"
        value={formatCurrency(currentPrice)}
        subValue={`${priceChange24h >= 0 ? '+' : ''}${formatPercent(priceChange24h)} (24h)`}
        icon={<Activity className="h-4 w-4" />}
        trend={priceTrend}
        isLoading={isLoading}
      />

      <MetricCardItem
        title="24시간 변동"
        value={`${priceChange24h >= 0 ? '+' : ''}${formatPercent(priceChange24h)}`}
        icon={
          priceChange24h >= 0 ? (
            <TrendingUp className="h-4 w-4" />
          ) : (
            <TrendingDown className="h-4 w-4" />
          )
        }
        trend={priceTrend}
        isLoading={isLoading}
      />

      <MetricCardItem
        title="오늘 손익"
        value={`${dailyPnl >= 0 ? '+' : ''}${formatCurrency(dailyPnl)}`}
        subValue={`${dailyPnl >= 0 ? '+' : ''}${formatPercent(dailyPnlPct)}`}
        icon={
          dailyPnl >= 0 ? (
            <TrendingUp className="h-4 w-4" />
          ) : (
            <TrendingDown className="h-4 w-4" />
          )
        }
        trend={pnlTrend}
        isLoading={isLoading}
      />

      <MetricCardItem
        title="오늘 거래 수"
        value={String(todayTradeCount)}
        subValue="회"
        icon={<BarChart3 className="h-4 w-4" />}
        trend="neutral"
        isLoading={isLoading}
      />
    </div>
  )
}

export default MetricCards
