import { TrendingUp, TrendingDown, Wallet } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface NetProfitHeroProps {
  /** 누적 입금액 (KRW) */
  totalDeposit: number
  /** 현재 평가금 (KRW) */
  currentValue: number
  /** 누적 지불 수수료 (KRW) */
  totalFeesPaid: number
  isLoading?: boolean
}

/**
 * "입금 X → 현재 Y → 순손익 Z" 한눈에 보이는 정직한 손익 요약.
 * 소유자가 '결국 얼마 벌었나'를 즉시 확인하도록.
 */
export function NetProfitHero({
  totalDeposit,
  currentValue,
  totalFeesPaid,
  isLoading,
}: NetProfitHeroProps) {
  if (isLoading) {
    return (
      <CommonCard title="순손익">
        <Skeleton className="h-24 w-full" />
      </CommonCard>
    )
  }

  const netProfit = currentValue - totalDeposit
  const netProfitPct = totalDeposit > 0 ? (netProfit / totalDeposit) * 100 : 0
  const isProfit = netProfit >= 0

  return (
    <CommonCard title="순손익" description="입금액 대비 현재 평가 기준">
      <div className="space-y-4">
        {/* 메인 순손익 */}
        <div className="flex items-end justify-between">
          <div>
            <div
              className={cn(
                'text-3xl font-bold font-mono-num',
                isProfit ? 'text-emerald-400' : 'text-rose-400'
              )}
            >
              {isProfit ? '+' : ''}
              {formatCurrency(netProfit)}
            </div>
            <div
              className={cn(
                'text-sm font-mono-num mt-1',
                isProfit ? 'text-emerald-400/80' : 'text-rose-400/80'
              )}
            >
              {formatPercent(netProfitPct, { showSign: true })}
            </div>
          </div>
          {isProfit ? (
            <TrendingUp className="h-8 w-8 text-emerald-400/60" />
          ) : (
            <TrendingDown className="h-8 w-8 text-rose-400/60" />
          )}
        </div>

        {/* 입금 → 현재 → 수수료 분해 */}
        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-white/5 text-sm">
          <div>
            <div className="flex items-center gap-1 text-zinc-500 text-xs mb-0.5">
              <Wallet className="h-3 w-3" /> 입금
            </div>
            <div className="font-mono-num text-foreground">
              {formatCurrency(totalDeposit)}
            </div>
          </div>
          <div>
            <div className="text-zinc-500 text-xs mb-0.5">현재 평가</div>
            <div className="font-mono-num text-foreground">
              {formatCurrency(currentValue)}
            </div>
          </div>
          <div>
            <div className="text-zinc-500 text-xs mb-0.5">누적 수수료</div>
            <div className="font-mono-num text-amber-400/90">
              {formatCurrency(totalFeesPaid)}
            </div>
          </div>
        </div>
      </div>
    </CommonCard>
  )
}

export default NetProfitHero
