import { TrendingUp, TrendingDown } from 'lucide-react'
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
        <Skeleton className="h-12 w-32" />
      </CommonCard>
    )
  }

  const isPositive = cumulativeReturnPct >= 0

  return (
    <CommonCard title="누적 실현 수익률" className={className}>
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
            {formatCurrency(totalRealizedPnl, { showSign: true })}
          </p>
        </div>
      </div>
    </CommonCard>
  )
}

export default CumulativeReturnCard
