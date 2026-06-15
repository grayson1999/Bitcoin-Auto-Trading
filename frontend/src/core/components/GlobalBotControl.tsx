import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Square, Play, Loader2 } from 'lucide-react'
import { fetchRiskStatus, haltTrading, resumeTrading } from '@/api/risk.api'
import { useAuth } from '@stores/auth.store'
import { Button } from '@core/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@core/components/ui/dialog'
import { cn } from '@core/utils'

type ConfirmAction = 'halt' | 'resume' | null

/**
 * 전역 봇 중단/재개 컨트롤 — 어느 화면에서나 헤더에서 접근.
 * 매도는 하지 않고 자동매매 루프만 중단/재개한다(기존 risk halt/resume API 재사용).
 */
export function GlobalBotControl({ compact = false }: { compact?: boolean }) {
  const { isAdmin } = useAuth()
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null)
  const queryClient = useQueryClient()

  const { data: riskStatus } = useQuery({
    queryKey: ['riskStatus'],
    queryFn: fetchRiskStatus,
    refetchInterval: 5000,
    enabled: isAdmin,
  })

  const haltMutation = useMutation({
    mutationFn: () => haltTrading('수동 거래 중단 (전역)'),
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

  const isPending = haltMutation.isPending || resumeMutation.isPending

  // admin이 아니거나 상태 미로딩 시 렌더 안 함
  if (!isAdmin || !riskStatus) return null

  const isActive = riskStatus.trading_enabled && !riskStatus.is_halted

  const handleConfirm = () => {
    if (confirmAction === 'halt') haltMutation.mutate()
    else if (confirmAction === 'resume') resumeMutation.mutate()
  }

  return (
    <>
      <div className="flex items-center gap-2">
        {/* 봇 상태 배지 */}
        <span
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
            isActive
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          )}
        >
          <span
            className={cn(
              'w-1.5 h-1.5 rounded-full',
              isActive ? 'bg-emerald-400' : 'bg-rose-400'
            )}
          />
          {isActive ? '가동중' : '중단됨'}
        </span>

        {/* 중단/재개 버튼 */}
        {isActive ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
            onClick={() => setConfirmAction('halt')}
            disabled={isPending}
          >
            <Square className="h-3.5 w-3.5" />
            {!compact && <span className="text-xs ml-1">중단</span>}
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
            onClick={() => setConfirmAction('resume')}
            disabled={isPending}
          >
            <Play className="h-3.5 w-3.5" />
            {!compact && <span className="text-xs ml-1">재개</span>}
          </Button>
        )}
      </div>

      {/* 확인 다이얼로그 */}
      <Dialog
        open={confirmAction !== null}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>
              {confirmAction === 'halt' ? '거래 중단' : '거래 재개'}
            </DialogTitle>
            <DialogDescription>
              {confirmAction === 'halt'
                ? '자동 매매를 중단하시겠습니까? 보유 포지션은 매도하지 않으며, 신규 자동 매수/매도만 멈춥니다.'
                : '자동 매매를 재개하시겠습니까? 봇이 다시 신호에 따라 거래합니다.'}
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
            >
              {isPending && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
              {confirmAction === 'halt' ? '중단' : '재개'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default GlobalBotControl
