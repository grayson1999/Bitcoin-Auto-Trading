import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { Balance } from '@/core/types'
import { formatCurrency, formatNumber } from '@/core/utils/formatters'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'

interface BalanceCardProps {
  balance: Balance | null
  isLoading?: boolean
  className?: string
}

export function BalanceCard({ balance, isLoading, className }: BalanceCardProps) {
  const { currency } = useTradingConfig()

  if (isLoading) {
    return (
      <CommonCard title="계좌 잔고" className={className}>
        <div className="space-y-3">
          <Skeleton className="h-8 w-40" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </div>
      </CommonCard>
    )
  }

  if (!balance) {
    return (
      <CommonCard title="계좌 잔고" className={className}>
        <div className="flex items-center justify-center py-6 text-gray-500">
          <p>잔고 정보를 불러올 수 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  return (
    <CommonCard title="계좌 잔고" className={className}>
      <div className="space-y-4">
        {/* Total Value */}
        <div>
          <p className="text-sm text-gray-400">총 평가금액</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(balance.total_krw)}
          </p>
        </div>

        {/* Balance Details */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400">KRW 잔고</p>
            <p className="text-lg font-semibold text-white">
              {formatCurrency(balance.krw)}
            </p>
            {balance.krw_locked > 0 && (
              <p className="text-xs text-yellow-500">
                잠김: {formatCurrency(balance.krw_locked)}
              </p>
            )}
          </div>

          <div className="rounded-lg bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400">{currency} 잔고</p>
            <p className="text-lg font-semibold text-white">
              {formatNumber(balance.coin, 8)} {currency}
            </p>
            {balance.coin_locked > 0 && (
              <p className="text-xs text-yellow-500">
                잠김: {formatNumber(balance.coin_locked, 8)}
              </p>
            )}
          </div>
        </div>

        {/* Average Buy Price */}
        {balance.coin > 0 && balance.coin_avg_buy_price > 0 && (
          <div className="border-t border-gray-700 pt-3">
            <p className="text-xs text-gray-400">{currency} 평균 매수가</p>
            <p className="text-sm text-white">
              {formatCurrency(balance.coin_avg_buy_price)}
            </p>
          </div>
        )}
      </div>
    </CommonCard>
  )
}

export default BalanceCard
