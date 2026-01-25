import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { Position } from '@/core/types'
import { formatCurrency, formatPercent, formatNumber } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'

interface PositionCardProps {
  position: Position | null
  isLoading?: boolean
  className?: string
}

export function PositionCard({ position, isLoading, className }: PositionCardProps) {
  const { currency } = useTradingConfig()

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
          <p className="text-sm">현재 보유중인 {currency}가 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  const isProfitable = position.unrealized_pnl >= 0

  return (
    <CommonCard title="현재 포지션" className={className}>
      <div className="space-y-5">
        {/* Position Info */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-zinc-400">보유 수량</p>
            <p className="text-2xl font-bold text-foreground font-heading mt-1">
              {formatNumber(position.quantity, 8)} <span className="text-lg font-normal text-zinc-500">{currency}</span>
            </p>
          </div>
          <Badge
            variant="outline"
            className={cn(
              'text-sm px-3 py-1 font-semibold backdrop-blur-md',
              isProfitable
                ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10'
                : 'border-rose-500/30 text-rose-500 bg-rose-500/10'
            )}
          >
            {isProfitable ? '수익' : '손실'}
          </Badge>
        </div>

        {/* Average Buy Price */}
        <div className="p-3 rounded-lg bg-black/20 border border-white/5 flex justify-between items-center">
          <p className="text-sm text-zinc-400">평균 매수가</p>
          <p className="text-lg text-foreground font-mono-num">{formatCurrency(position.avg_buy_price)}</p>
        </div>

        {/* Current Value & P&L */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-zinc-400 mb-1">평가금액</p>
            <p className="text-lg text-foreground font-mono-num font-medium">{formatCurrency(position.current_value)}</p>
          </div>
          <div>
            <p className="text-sm text-zinc-400 mb-1">미실현 손익</p>
            <p
              className={cn(
                'text-lg font-semibold font-mono-num',
                isProfitable ? 'text-emerald-400' : 'text-rose-500'
              )}
            >
              {isProfitable ? '+' : ''}
              {formatCurrency(position.unrealized_pnl)}
              <span className="ml-1.5 text-xs opacity-80 font-normal">
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
