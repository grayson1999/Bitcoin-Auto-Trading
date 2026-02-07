import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldAlert, ShieldCheck, AlertTriangle, Loader2, Play, Square } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Button } from '@/core/components/ui/button'
import { Skeleton } from '@/core/components/ui/skeleton'
import { Progress } from '@/core/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/core/components/ui/dialog'
import { haltTrading, resumeTrading } from '@/api/risk.api'
import type { RiskStatus } from '@/core/types'
import { formatPercent } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'

type ConfirmAction = 'halt' | 'resume' | null

interface RiskStatusCardProps {
  riskStatus: RiskStatus | null
  isLoading?: boolean
  className?: string
}

export function RiskStatusCard({ riskStatus, isLoading, className }: RiskStatusCardProps) {
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null)
  const queryClient = useQueryClient()

  const haltMutation = useMutation({
    mutationFn: () => haltTrading('수동 거래 중단'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskStatus'] })
      setConfirmAction(null)
    },
  })

  const resumeMutation = useMutation({
    mutationFn: resumeTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskStatus'] })
      setConfirmAction(null)
    },
  })

  const handleConfirm = () => {
    if (confirmAction === 'halt') {
      haltMutation.mutate()
    } else if (confirmAction === 'resume') {
      resumeMutation.mutate()
    }
  }

  const isPending = haltMutation.isPending || resumeMutation.isPending

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
          <div className="flex items-center gap-2">
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
            {isActive ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                onClick={() => setConfirmAction('halt')}
                disabled={isPending}
              >
                {haltMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Square className="h-3.5 w-3.5" />
                )}
                <span className="text-xs">중단</span>
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                onClick={() => setConfirmAction('resume')}
                disabled={isPending}
              >
                {resumeMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5" />
                )}
                <span className="text-xs">재개</span>
              </Button>
            )}
          </div>
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

      {/* Confirmation Dialog */}
      <Dialog open={confirmAction !== null} onOpenChange={(open) => !open && setConfirmAction(null)}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>
              {confirmAction === 'halt' ? '거래 중단' : '거래 재개'}
            </DialogTitle>
            <DialogDescription>
              {confirmAction === 'halt'
                ? '거래를 중단하시겠습니까? 모든 자동 매매가 일시 중지됩니다.'
                : '거래를 재개하시겠습니까? 자동 매매가 다시 시작됩니다.'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="ghost"
              onClick={() => setConfirmAction(null)}
              disabled={isPending}
            >
              취소
            </Button>
            <Button
              variant={confirmAction === 'halt' ? 'destructive' : 'default'}
              onClick={handleConfirm}
              disabled={isPending}
              className={confirmAction === 'resume' ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
            >
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {confirmAction === 'halt' ? '중단' : '재개'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </CommonCard>
  )
}

export default RiskStatusCard
