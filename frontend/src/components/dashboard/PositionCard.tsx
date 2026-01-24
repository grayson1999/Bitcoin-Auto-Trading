import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { Position } from '@/core/types'
import { formatCurrency, formatPercent, formatNumber } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'

interface PositionCardProps {
  position: Position | null
  isLoading?: boolean
  className?: string
}

export function PositionCard({ position, isLoading, className }: PositionCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="현재 포지션" className={className}>
        <div className="space-y-3">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-40" />
        </div>
      </CommonCard>
    )
  }

  if (!position || position.quantity === 0) {
    return (
      <CommonCard title="현재 포지션" className={className}>
        <div className="flex flex-col items-center justify-center py-6 text-gray-500">
          <p className="text-lg">포지션 없음</p>
          <p className="text-sm">현재 보유중인 BTC가 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  const isProfitable = position.unrealized_pnl >= 0

  return (
    <CommonCard title="현재 포지션" className={className}>
      <div className="space-y-4">
        {/* Position Info */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">보유 수량</p>
            <p className="text-xl font-semibold text-white">
              {formatNumber(position.quantity, 8)} BTC
            </p>
          </div>
          <Badge
            variant="outline"
            className={cn(
              'text-sm',
              isProfitable
                ? 'border-green-500 text-green-400'
                : 'border-red-500 text-red-400'
            )}
          >
            {isProfitable ? '수익' : '손실'}
          </Badge>
        </div>

        {/* Average Buy Price */}
        <div>
          <p className="text-sm text-gray-400">평균 매수가</p>
          <p className="text-lg text-white">{formatCurrency(position.avg_buy_price)}</p>
        </div>

        {/* Current Value & P&L */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">평가금액</p>
            <p className="text-lg text-white">{formatCurrency(position.current_value)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">미실현 손익</p>
            <p
              className={cn(
                'text-lg font-semibold',
                isProfitable ? 'text-green-400' : 'text-red-400'
              )}
            >
              {isProfitable ? '+' : ''}
              {formatCurrency(position.unrealized_pnl)}
              <span className="ml-1 text-sm">
                ({isProfitable ? '+' : ''}
                {formatPercent(position.unrealized_pnl_pct)})
              </span>
            </p>
          </div>
        </div>
      </div>
    </CommonCard>
  )
}

export default PositionCard
