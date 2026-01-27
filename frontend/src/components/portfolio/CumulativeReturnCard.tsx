import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface CumulativeReturnCardProps {
  cumulativeReturnPct: number
  totalRealizedPnl: number
  isLoading?: boolean
  className?: string
}

export function CumulativeReturnCard({
  cumulativeReturnPct,
  totalRealizedPnl,
  isLoading,
  className,
}: CumulativeReturnCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="누적 실현 수익률" className={className}>
        <div className="space-y-3">
          <Skeleton className="h-10 w-28" />
          <Skeleton className="h-6 w-40" />
        </div>
      </CommonCard>
    )
  }

  const isPositive = totalRealizedPnl > 0
  const isNegative = totalRealizedPnl < 0
  const isNeutral = totalRealizedPnl === 0

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
    <CommonCard title="누적 실현 수익률" className={className}>
      <div className="space-y-3">
        {/* Return Percentage */}
        <div className="flex items-center gap-2">
          {getIcon()}
          <p className={cn('text-2xl font-bold', getColorClass())}>
            {formatPercent(cumulativeReturnPct, { showSign: true })}
          </p>
        </div>

        {/* Realized P&L */}
        <div className="rounded-lg bg-gray-800/50 p-3">
          <p className="text-xs text-gray-400">누적 실현 손익</p>
          <p className={cn('text-lg font-semibold', getColorClass())}>
            {formatCurrency(totalRealizedPnl, { showSign: true })}
          </p>
        </div>

        {/* Status Message */}
        <p className="text-xs text-gray-500">
          {isPositive && '누적 수익 중'}
          {isNegative && '누적 손실 중'}
          {isNeutral && '거래 기록 없음'}
        </p>
      </div>
    </CommonCard>
  )
}

export default CumulativeReturnCard
