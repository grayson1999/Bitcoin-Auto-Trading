import { Wallet, Plus } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { Deposit } from '@/core/types'
import { formatCurrency, formatDate } from '@/core/utils/formatters'

interface DepositHistoryCardProps {
  deposits: Deposit[]
  totalDeposit: number
  isLoading?: boolean
  className?: string
}

export function DepositHistoryCard({
  deposits,
  totalDeposit,
  isLoading,
  className,
}: DepositHistoryCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="입금 내역" className={className}>
        <div className="space-y-3">
          <Skeleton className="h-8 w-32" />
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </CommonCard>
    )
  }

  if (deposits.length === 0) {
    return (
      <CommonCard title="입금 내역" className={className}>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="rounded-full bg-gray-800 p-3 mb-3">
            <Wallet className="h-6 w-6 text-gray-400" />
          </div>
          <p className="text-sm text-gray-400">입금 내역이 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  return (
    <CommonCard title="입금 내역" className={className}>
      <div className="space-y-4">
        {/* Total Deposit Summary */}
        <div className="flex items-center justify-between rounded-lg bg-accent/10 p-3">
          <div className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-accent" />
            <span className="text-sm text-gray-300">총 입금액</span>
          </div>
          <span className="text-lg font-bold text-white">
            {formatCurrency(totalDeposit)}
          </span>
        </div>

        {/* Deposit List */}
        <div className="space-y-2">
          {deposits.map((deposit) => (
            <div
              key={deposit.id}
              className="flex items-center justify-between rounded-lg bg-gray-800/50 p-3"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-up/10 p-1.5">
                  <Plus className="h-3 w-3 text-up" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">
                    {formatCurrency(deposit.amount)}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatDate(deposit.deposited_at)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Deposit Count */}
        <p className="text-xs text-gray-500 text-center">
          총 {deposits.length}건의 입금 기록
        </p>
      </div>
    </CommonCard>
  )
}

export default DepositHistoryCard
