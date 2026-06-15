import { TrendingUp, TrendingDown, Info } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Skeleton } from '@/core/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils'

interface NetProfitHeroProps {
  /** 매매 실현손익 (KRW) - 진짜 거래 성적 */
  realizedPnl: number
  /** 누적 수익률 (%, 실현손익 기준) */
  cumulativeReturnPct: number
  /** 누적 입금액 (KRW) */
  totalDeposit: number
  /** 현재 평가금 (KRW) */
  currentValue: number
  /** 누적 지불 수수료 (KRW) */
  totalFeesPaid: number
  isLoading?: boolean
}

/**
 * 정직한 손익 히어로.
 * 메인 = 매매 실현손익(입금 제외, 진짜 거래 성적).
 * 보조 = 총자산 변화(입금 포함)를 중립색으로 명확히 분리 → 거짓 수익 착시 방지.
 */
export function NetProfitHero({
  realizedPnl,
  cumulativeReturnPct,
  totalDeposit,
  currentValue,
  totalFeesPaid,
  isLoading,
}: NetProfitHeroProps) {
  if (isLoading) {
    return (
      <CommonCard title="매매 실현손익">
        <Skeleton className="h-24 w-full" />
      </CommonCard>
    )
  }

  const isProfit = realizedPnl >= 0
  // 입금이 포함된 자산 증감 (수익이 아님 - 중립색으로만 표시)
  const assetChange = currentValue - totalDeposit

  return (
    <CommonCard
      title="매매 실현손익"
      description="실제 거래로 번/잃은 금액 (입금 제외)"
    >
      <div className="space-y-4">
        {/* 메인: 진짜 매매 성적 */}
        <div className="flex items-end justify-between">
          <div>
            <div
              className={cn(
                'text-3xl font-bold font-mono-num',
                isProfit ? 'text-emerald-400' : 'text-rose-400'
              )}
            >
              {formatCurrency(realizedPnl, { showSign: true })}
            </div>
            <div
              className={cn(
                'text-sm font-mono-num mt-1',
                isProfit ? 'text-emerald-400/80' : 'text-rose-400/80'
              )}
            >
              {formatPercent(cumulativeReturnPct, { showSign: true })}
            </div>
          </div>
          {isProfit ? (
            <TrendingUp className="h-8 w-8 text-emerald-400/60" />
          ) : (
            <TrendingDown className="h-8 w-8 text-rose-400/60" />
          )}
        </div>

        {/* 보조: 총자산 변화 (입금 포함) - 중립색, 매매 성적과 구분 */}
        <div className="pt-3 border-t border-white/5">
          <div className="flex items-center gap-1 text-xs text-zinc-500 mb-2">
            <Info className="h-3 w-3" />
            총자산 변화 (입금 포함)
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div>
              <div className="text-zinc-500 text-xs mb-0.5">입금 누계</div>
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
              <div className="text-zinc-500 text-xs mb-0.5">자산 증감</div>
              {/* 입금 포함이라 수익 아님 → 항상 중립색 zinc */}
              <div className="font-mono-num text-zinc-300">
                {formatCurrency(assetChange, { showSign: true })}
              </div>
            </div>
          </div>
          <p className="text-[11px] text-zinc-600 mt-2">
            입금이 포함되어 실제 매매 성적과 다릅니다. 누적 수수료{' '}
            <span className="text-amber-400/80">{formatCurrency(totalFeesPaid)}</span>
          </p>
        </div>
      </div>
    </CommonCard>
  )
}

export default NetProfitHero
