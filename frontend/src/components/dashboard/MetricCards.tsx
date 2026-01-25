import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'

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
      <div className="glass-card p-5">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded bg-zinc-800" />
          <Skeleton className="h-4 w-20 bg-zinc-800" />
        </div>
        <Skeleton className="mt-3 h-8 w-32 bg-zinc-800" />
        <Skeleton className="mt-2 h-4 w-16 bg-zinc-800" />
      </div>
    )
  }

  return (
    <div className="glass-card p-5 transition-all duration-300 hover:bg-zinc-900/60">
      <div className="flex items-center gap-2 text-zinc-400 mb-2">
        <div className="p-1.5 rounded-md bg-white/5">
          {icon}
        </div>
        <span className="text-sm font-medium">{title}</span>
      </div>
      <p
        className={cn(
          'mt-1 text-2xl font-bold font-heading tracking-tight',
          trend === 'up' && 'text-emerald-400',
          trend === 'down' && 'text-rose-500',
          trend === 'neutral' && 'text-zinc-100'
        )}
      >
        {value}
      </p>
      {subValue && (
        <p
          className={cn(
            'text-sm font-mono-num mt-1 font-medium',
            trend === 'up' && 'text-emerald-400/90',
            trend === 'down' && 'text-rose-500/90',
            trend === 'neutral' && 'text-zinc-500'
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
  const { currency } = useTradingConfig()
  const priceTrend = priceChange24h >= 0 ? 'up' : 'down'
  const pnlTrend = dailyPnl >= 0 ? 'up' : dailyPnl < 0 ? 'down' : 'neutral'

  return (
    <div className={cn('grid grid-cols-2 gap-4 lg:grid-cols-4', className)}>
      <MetricCardItem
        title={`${currency} 현재가`}
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
