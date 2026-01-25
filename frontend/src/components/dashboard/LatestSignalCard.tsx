import { ArrowUpCircle, ArrowDownCircle, MinusCircle, Clock } from 'lucide-react'
import { CommonCard } from '@/core/components/CommonCard'
import { Badge } from '@/core/components/ui/badge'
import { Skeleton } from '@/core/components/ui/skeleton'
import type { TradingSignal } from '@/core/types'
import { formatDateTime } from '@/core/utils/formatters'
import { cn } from '@/core/utils/cn'

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
  // confidence는 0~1 범위이므로 100을 곱해서 퍼센트로 표시
  const confidencePercent = Math.round(signal.confidence * 100)

  return (
    <CommonCard title="최신 AI 신호" className={className}>
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
              <p className="mt-1 text-sm text-zinc-400 font-mono-num">
                신뢰도: {confidencePercent}%
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono-num">
              <Clock className="h-3.5 w-3.5" />
              {formatDateTime(signal.created_at)}
            </div>
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
            <p className="text-xs text-zinc-500 mb-1.5 font-medium">분석 근거</p>
            <p className="text-sm text-zinc-300 line-clamp-3 leading-relaxed">{signal.reasoning}</p>
          </div>
        )}
      </div>
    </CommonCard>
  )
}

export default LatestSignalCard
