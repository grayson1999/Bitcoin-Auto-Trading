import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowUpCircle, ArrowDownCircle, MinusCircle, Clock } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Skeleton } from '@/core/components/ui/skeleton'
import { SignalDetailModal } from '@/components/signals/SignalDetailModal'
import type { TradingSignal } from '@/core/types'
import { formatDateTime, formatRelativeTime } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'
import { isRuleBasedSignal, getOutcomeBadgeConfig } from '@/components/signals/signal-config'
import { fetchPortfolioSummary } from '@/api/portfolio.api'
import { fetchConfigs } from '@/api/config.api'

interface LatestSignalCardProps {
  signal: TradingSignal | null
  isLoading?: boolean
  className?: string
}

const SIGNAL_CONFIG = {
  BUY: {
    icon: ArrowUpCircle,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    label: '매수',
  },
  SELL: {
    icon: ArrowDownCircle,
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/10',
    borderColor: 'border-rose-500/20',
    label: '매도',
  },
  HOLD: {
    icon: MinusCircle,
    color: 'text-zinc-400',
    bgColor: 'bg-zinc-500/10',
    borderColor: 'border-zinc-500/20',
    label: '보류',
  },
} as const

export function LatestSignalCard({ signal, isLoading, className }: LatestSignalCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  // AI accuracy from portfolio summary (admin-only; hide on error)
  const { data: portfolio, isError: portfolioError } = useQuery({
    queryKey: ['portfolioSummary'],
    queryFn: fetchPortfolioSummary,
    staleTime: 60000,
  })

  // Config for next-signal countdown
  const { data: configData } = useQuery({
    queryKey: ['configs'],
    queryFn: fetchConfigs,
    staleTime: 60000,
  })

  if (isLoading) {
    return (
      <CommonCard title="최신 AI 신호" className={className}>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="mt-1 h-4 w-32" />
            </div>
          </div>
          <Skeleton className="h-16 w-full" />
        </div>
      </CommonCard>
    )
  }

  if (!signal) {
    return (
      <CommonCard title="최신 AI 신호" className={className}>
        <div className="flex flex-col items-center justify-center py-6 text-zinc-500">
          <MinusCircle className="h-10 w-10 mb-2 opacity-50" />
          <p className="text-lg font-medium">신호 없음</p>
          <p className="text-sm">아직 생성된 AI 신호가 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  const config = SIGNAL_CONFIG[signal.signal_type]
  const Icon = config.icon
  const isRuleBased = isRuleBasedSignal(signal.model_name)
  // confidence는 0~1 범위이므로 100을 곱해서 퍼센트로 표시
  const confidencePercent = Math.round(signal.confidence * 100)
  const outcome = getOutcomeBadgeConfig(signal.outcome_evaluated, signal.outcome_correct)

  // 매매 승률 (win/(win+loss)) - hidden on admin-only fetch error
  // 주의: AI 신호 정확도가 아니라 청산 거래 기준 승률임.
  const winRate = !portfolioError && portfolio ? portfolio.win_rate : null

  // Next-signal countdown from created_at + signal_interval_minutes
  const intervalRaw = configData?.configs?.signal_interval_minutes
  const intervalMinutes =
    typeof intervalRaw === 'number'
      ? intervalRaw
      : typeof intervalRaw === 'string'
        ? Number(intervalRaw)
        : NaN
  const nextSignalAt =
    Number.isFinite(intervalMinutes) && intervalMinutes > 0
      ? new Date(new Date(signal.created_at).getTime() + intervalMinutes * 60_000)
      : null
  const nextSignalText = nextSignalAt
    ? nextSignalAt.getTime() > Date.now()
      ? `다음 분석 ${formatRelativeTime(nextSignalAt)}`
      : '분석 대기 중'
    : null

  return (
    <CommonCard
      title={isRuleBased ? '최신 신호 (자동 익절)' : '최신 AI 신호'}
      headerAction={
        <div className="flex items-center gap-3">
          {winRate != null && (
            <span
              className={cn(
                'text-xs font-mono-num',
                winRate < 40 ? 'text-rose-400' : 'text-emerald-400'
              )}
            >
              매매 승률 {Math.round(winRate)}%
            </span>
          )}
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            자세히 보기 &rarr;
          </button>
        </div>
      }
      className={className}
    >
      <div className="space-y-5">
        {/* Signal Type & Confidence */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-xl ring-1 ring-inset',
                config.bgColor,
                config.borderColor
              )}
            >
              <Icon className={cn('h-6 w-6', config.color)} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Badge
                  className={cn(
                    'text-sm font-semibold backdrop-blur-md',
                    config.bgColor,
                    config.color,
                    config.borderColor,
                    'border'
                  )}
                >
                  {config.label}
                </Badge>
                <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0', outcome.className)}>
                  {outcome.label}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-zinc-400 font-mono-num">
                신뢰도: {confidencePercent}%
                {signal.action_score != null && (
                  <span className="ml-2 text-xs text-zinc-500">강도 {signal.action_score.toFixed(2)}</span>
                )}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center justify-end gap-1.5 text-xs text-zinc-500 font-mono-num">
              <Clock className="h-3.5 w-3.5" />
              {formatDateTime(signal.created_at)}
            </div>
            {nextSignalText && (
              <p className="mt-1 text-xs text-zinc-500">{nextSignalText}</p>
            )}
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-zinc-500">신뢰도</span>
            <span className={config.color}>{confidencePercent}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
            <div
              className={cn('h-full rounded-full transition-all', {
                'bg-emerald-500': signal.signal_type === 'BUY',
                'bg-rose-500': signal.signal_type === 'SELL',
                'bg-zinc-500': signal.signal_type === 'HOLD',
              })}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        {/* Reasoning */}
        {signal.reasoning && (
          <div className="rounded-lg bg-black/20 p-3.5 border border-white/5">
            <p className="text-xs text-zinc-500 mb-1.5 font-medium">{isRuleBased ? '실행 내역' : '분석 근거'}</p>
            <p className="text-sm text-zinc-300 line-clamp-3 leading-relaxed">{signal.reasoning}</p>
          </div>
        )}
      </div>

      {/* Signal Detail Modal */}
      <SignalDetailModal
        signal={signal}
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
      />
    </CommonCard>
  )
}

export default LatestSignalCard
