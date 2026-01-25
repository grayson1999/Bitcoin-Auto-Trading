import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Skeleton } from '@/core/components/ui/skeleton'
import { Progress } from '@/core/components/ui/progress'
import type { RiskStatus } from '@/core/types'
import { formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'

interface RiskStatusCardProps {
  riskStatus: RiskStatus | null
  isLoading?: boolean
  className?: string
}

export function RiskStatusCard({ riskStatus, isLoading, className }: RiskStatusCardProps) {
  if (isLoading) {
    return (
      <CommonCard title="리스크 상태" className={className}>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </CommonCard>
    )
  }

  if (!riskStatus) {
    return (
      <CommonCard title="리스크 상태" className={className}>
        <div className="flex items-center justify-center py-6 text-gray-500">
          <p>리스크 정보를 불러올 수 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  const isActive = riskStatus.trading_enabled && !riskStatus.is_halted
  const dailyLossRatio = (riskStatus.daily_loss_pct / riskStatus.daily_loss_limit_pct) * 100
  const isWarning = dailyLossRatio >= 70
  const isCritical = dailyLossRatio >= 90

  return (
    <CommonCard title="리스크 상태" className={className}>
      <div className="space-y-4">
        {/* Trading Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isActive ? (
              <ShieldCheck className="h-6 w-6 text-emerald-400" />
            ) : (
              <ShieldAlert className="h-6 w-6 text-rose-500" />
            )}
            <span className="font-medium text-foreground">거래 상태</span>
          </div>
          <Badge
            className={cn(
              'font-semibold backdrop-blur-md',
              isActive
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-500 border-rose-500/20',
              'border'
            )}
          >
            {isActive ? '활성' : '중단'}
          </Badge>
        </div>

        {/* Halt Reason */}
        {riskStatus.is_halted && riskStatus.halt_reason && (
          <div className="rounded-lg bg-rose-500/10 p-3 border border-rose-500/20">
            <div className="flex items-center gap-2 text-rose-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">중단 사유</span>
            </div>
            <p className="mt-1 text-sm text-rose-300">{riskStatus.halt_reason}</p>
          </div>
        )}

        {/* Daily Loss Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-400">일일 손실</span>
            <span
              className={cn('font-mono-num', {
                'text-emerald-400': !isWarning,
                'text-yellow-400': isWarning && !isCritical,
                'text-rose-400': isCritical,
              })}
            >
              {formatPercent(riskStatus.daily_loss_pct)} / {formatPercent(riskStatus.daily_loss_limit_pct)}
            </span>
          </div>
          <Progress
            value={Math.min(dailyLossRatio, 100)}
            className={cn('h-1.5 bg-zinc-800', {
              '[&>div]:bg-emerald-500': !isWarning,
              '[&>div]:bg-yellow-500': isWarning && !isCritical,
              '[&>div]:bg-rose-500': isCritical,
            })}
          />
        </div>

        {/* Risk Parameters */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg bg-black/20 p-2.5 border border-white/5">
            <p className="text-xs text-zinc-500">손절매</p>
            <p className="font-medium text-foreground font-mono-num">{formatPercent(riskStatus.stop_loss_pct)}</p>
          </div>
          <div className="rounded-lg bg-black/20 p-2.5 border border-white/5">
            <p className="text-xs text-zinc-500">포지션 크기</p>
            <p className="font-medium text-foreground font-mono-num">{formatPercent(riskStatus.position_size_pct)}</p>
          </div>
          <div className="rounded-lg bg-black/20 p-2.5 border border-white/5">
            <p className="text-xs text-zinc-500">변동성 한도</p>
            <p className="font-medium text-foreground font-mono-num">{formatPercent(riskStatus.volatility_threshold_pct)}</p>
          </div>
          <div className="rounded-lg bg-black/20 p-2.5 border border-white/5">
            <p className="text-xs text-zinc-500">현재 변동성</p>
            <p
              className={cn('font-medium font-mono-num', {
                'text-emerald-400':
                  riskStatus.current_volatility_pct < riskStatus.volatility_threshold_pct * 0.7,
                'text-yellow-400':
                  riskStatus.current_volatility_pct >= riskStatus.volatility_threshold_pct * 0.7 &&
                  riskStatus.current_volatility_pct < riskStatus.volatility_threshold_pct,
                'text-rose-400':
                  riskStatus.current_volatility_pct >= riskStatus.volatility_threshold_pct,
              })}
            >
              {formatPercent(riskStatus.current_volatility_pct)}
            </p>
          </div>
        </div>
      </div>
    </CommonCard>
  )
}

export default RiskStatusCard
