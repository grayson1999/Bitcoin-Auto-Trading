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
              <ShieldCheck className="h-6 w-6 text-green-400" />
            ) : (
              <ShieldAlert className="h-6 w-6 text-red-400" />
            )}
            <span className="font-medium text-white">거래 상태</span>
          </div>
          <Badge
            className={cn(
              'font-semibold',
              isActive
                ? 'bg-green-500/20 text-green-400 border-green-500/30'
                : 'bg-red-500/20 text-red-400 border-red-500/30',
              'border'
            )}
          >
            {isActive ? '활성' : '중단'}
          </Badge>
        </div>

        {/* Halt Reason */}
        {riskStatus.is_halted && riskStatus.halt_reason && (
          <div className="rounded-lg bg-red-500/10 p-3 border border-red-500/30">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">중단 사유</span>
            </div>
            <p className="mt-1 text-sm text-red-300">{riskStatus.halt_reason}</p>
          </div>
        )}

        {/* Daily Loss Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">일일 손실</span>
            <span
              className={cn({
                'text-green-400': !isWarning,
                'text-yellow-400': isWarning && !isCritical,
                'text-red-400': isCritical,
              })}
            >
              {formatPercent(riskStatus.daily_loss_pct)} / {formatPercent(riskStatus.daily_loss_limit_pct)}
            </span>
          </div>
          <Progress
            value={Math.min(dailyLossRatio, 100)}
            className={cn('h-2', {
              '[&>div]:bg-green-500': !isWarning,
              '[&>div]:bg-yellow-500': isWarning && !isCritical,
              '[&>div]:bg-red-500': isCritical,
            })}
          />
        </div>

        {/* Risk Parameters */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg bg-gray-800/50 p-2">
            <p className="text-xs text-gray-400">손절매</p>
            <p className="font-medium text-white">{formatPercent(riskStatus.stop_loss_pct)}</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-2">
            <p className="text-xs text-gray-400">포지션 크기</p>
            <p className="font-medium text-white">{formatPercent(riskStatus.position_size_pct)}</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-2">
            <p className="text-xs text-gray-400">변동성 한도</p>
            <p className="font-medium text-white">{formatPercent(riskStatus.volatility_threshold_pct)}</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-2">
            <p className="text-xs text-gray-400">현재 변동성</p>
            <p
              className={cn('font-medium', {
                'text-green-400':
                  riskStatus.current_volatility_pct < riskStatus.volatility_threshold_pct * 0.7,
                'text-yellow-400':
                  riskStatus.current_volatility_pct >= riskStatus.volatility_threshold_pct * 0.7 &&
                  riskStatus.current_volatility_pct < riskStatus.volatility_threshold_pct,
                'text-red-400':
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
