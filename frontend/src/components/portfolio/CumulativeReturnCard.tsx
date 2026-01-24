import { TrendingUp, TrendingDown } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface CumulativeReturnCardProps {
  totalDeposit: number
  currentValue: number
  cumulativeReturnPct: number
  isLoading?: boolean
  className?: string
}

export function CumulativeReturnCard({
  totalDeposit,
  currentValue,
  cumulativeReturnPct,
  isLoading,
  className,
}: CumulativeReturnCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="누적 수익률" className={className}>
        <div className="space-y-4">
          <Skeleton className="h-12 w-32" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </div>
      </CommonCard>
    )
  }

  const isPositive = cumulativeReturnPct >= 0
  const profitAmount = currentValue - totalDeposit

  return (
    <CommonCard title="누적 수익률" className={className}>
      <div className="space-y-4">
        {/* Main Return Percentage */}
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex items-center justify-center rounded-full p-2',
              isPositive ? 'bg-up/10' : 'bg-down/10'
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-6 w-6 text-up" />
            ) : (
              <TrendingDown className="h-6 w-6 text-down" />
            )}
          </div>
          <div>
            <p
              className={cn(
                'text-3xl font-bold',
                isPositive ? 'text-up' : 'text-down'
              )}
            >
              {formatPercent(cumulativeReturnPct, { showSign: true })}
            </p>
            <p
              className={cn(
                'text-sm',
                isPositive ? 'text-up/80' : 'text-down/80'
              )}
            >
              {formatCurrency(profitAmount, { showSign: true })}
            </p>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400">총 투자금</p>
            <p className="text-lg font-semibold text-white">
              {formatCurrency(totalDeposit)}
            </p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400">현재 평가금</p>
            <p className="text-lg font-semibold text-white">
              {formatCurrency(currentValue)}
            </p>
          </div>
        </div>
      </div>
    </CommonCard>
  )
}

export default CumulativeReturnCard
