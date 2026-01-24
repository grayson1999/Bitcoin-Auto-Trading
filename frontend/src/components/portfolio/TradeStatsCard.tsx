import { BarChart3, Target, TrendingDown, Activity } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatPercent, formatNumber } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface TradeStatsCardProps {
  totalTrades: number
  winCount: number
  winRate: number
  averageReturnPct: number
  maxDrawdownPct: number
  isLoading?: boolean
  className?: string
}

export function TradeStatsCard({
  totalTrades,
  winCount,
  winRate,
  averageReturnPct,
  maxDrawdownPct,
  isLoading,
  className,
}: TradeStatsCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="거래 통계" className={className}>
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      </CommonCard>
    )
  }

  const lossCount = totalTrades - winCount

  const stats = [
    {
      label: '승률',
      value: formatPercent(winRate, { decimals: 1 }),
      subValue: `${winCount}승 / ${lossCount}패`,
      icon: Target,
      iconColor: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      label: '총 거래 횟수',
      value: formatNumber(totalTrades),
      subValue: '전체 체결',
      icon: BarChart3,
      iconColor: 'text-blue-400',
      bgColor: 'bg-blue-400/10',
    },
    {
      label: '평균 수익률',
      value: formatPercent(averageReturnPct, { showSign: true }),
      subValue: '거래당',
      icon: Activity,
      iconColor: averageReturnPct >= 0 ? 'text-up' : 'text-down',
      bgColor: averageReturnPct >= 0 ? 'bg-up/10' : 'bg-down/10',
    },
    {
      label: 'MDD (최대 낙폭)',
      value: formatPercent(-maxDrawdownPct),
      subValue: '최대 손실폭',
      icon: TrendingDown,
      iconColor: 'text-down',
      bgColor: 'bg-down/10',
    },
  ]

  return (
    <CommonCard title="거래 통계" className={className}>
      <div className="grid grid-cols-2 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg bg-gray-800/50 p-3"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className={cn('rounded-md p-1.5', stat.bgColor)}>
                <stat.icon className={cn('h-4 w-4', stat.iconColor)} />
              </div>
              <p className="text-xs text-gray-400">{stat.label}</p>
            </div>
            <p className="text-xl font-bold text-white">{stat.value}</p>
            <p className="text-xs text-gray-500">{stat.subValue}</p>
          </div>
        ))}
      </div>
    </CommonCard>
  )
}

export default TradeStatsCard
