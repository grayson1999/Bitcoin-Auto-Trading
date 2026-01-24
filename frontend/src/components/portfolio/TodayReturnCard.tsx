import { Calendar, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface TodayReturnCardProps {
  todayReturnPct: number
  todayRealizedPnl: number
  isLoading?: boolean
  className?: string
}

export function TodayReturnCard({
  todayReturnPct,
  todayRealizedPnl,
  isLoading,
  className,
}: TodayReturnCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="오늘 수익률" className={className}>
        <div className="space-y-3">
          <Skeleton className="h-10 w-28" />
          <Skeleton className="h-6 w-40" />
        </div>
      </CommonCard>
    )
  }

  const isPositive = todayReturnPct > 0
  const isNegative = todayReturnPct < 0
  const isNeutral = todayReturnPct === 0

  const getIcon = () => {
    if (isPositive) return <TrendingUp className="h-5 w-5 text-up" />
    if (isNegative) return <TrendingDown className="h-5 w-5 text-down" />
    return <Minus className="h-5 w-5 text-gray-400" />
  }

  const getColorClass = () => {
    if (isPositive) return 'text-up'
    if (isNegative) return 'text-down'
    return 'text-gray-400'
  }

  return (
    <CommonCard
      title="오늘 수익률"
      headerAction={
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Calendar className="h-3 w-3" />
          <span>{new Date().toLocaleDateString('ko-KR')}</span>
        </div>
      }
      className={className}
    >
      <div className="space-y-3">
        {/* Return Percentage */}
        <div className="flex items-center gap-2">
          {getIcon()}
          <p className={cn('text-2xl font-bold', getColorClass())}>
            {formatPercent(todayReturnPct, { showSign: true })}
          </p>
        </div>

        {/* Realized P&L */}
        <div className="rounded-lg bg-gray-800/50 p-3">
          <p className="text-xs text-gray-400">실현 손익</p>
          <p className={cn('text-lg font-semibold', getColorClass())}>
            {formatCurrency(todayRealizedPnl, { showSign: true })}
          </p>
        </div>

        {/* Status Message */}
        <p className="text-xs text-gray-500">
          {isPositive && '오늘 수익이 발생했습니다'}
          {isNegative && '오늘 손실이 발생했습니다'}
          {isNeutral && '오늘 변동이 없습니다'}
        </p>
      </div>
    </CommonCard>
  )
}

export default TodayReturnCard
