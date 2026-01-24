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
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    label: '매수',
  },
  SELL: {
    icon: ArrowDownCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    label: '매도',
  },
  HOLD: {
    icon: MinusCircle,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
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
        <div className="flex flex-col items-center justify-center py-6 text-gray-500">
          <MinusCircle className="h-10 w-10 mb-2" />
          <p className="text-lg">신호 없음</p>
          <p className="text-sm">아직 생성된 AI 신호가 없습니다</p>
        </div>
      </CommonCard>
    )
  }

  const config = SIGNAL_CONFIG[signal.signal_type]
  const Icon = config.icon

  return (
    <CommonCard title="최신 AI 신호" className={className}>
      <div className="space-y-4">
        {/* Signal Type & Confidence */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-full',
                config.bgColor
              )}
            >
              <Icon className={cn('h-6 w-6', config.color)} />
            </div>
            <div>
              <Badge
                className={cn(
                  'text-sm font-semibold',
                  config.bgColor,
                  config.color,
                  config.borderColor,
                  'border'
                )}
              >
                {config.label}
              </Badge>
              <p className="mt-1 text-sm text-gray-400">
                신뢰도: {signal.confidence}%
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              {formatDateTime(signal.created_at)}
            </div>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">신뢰도</span>
            <span className={config.color}>{signal.confidence}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-gray-700">
            <div
              className={cn('h-full rounded-full transition-all', {
                'bg-green-500': signal.signal_type === 'BUY',
                'bg-red-500': signal.signal_type === 'SELL',
                'bg-yellow-500': signal.signal_type === 'HOLD',
              })}
              style={{ width: `${signal.confidence}%` }}
            />
          </div>
        </div>

        {/* Rationale */}
        {signal.rationale && (
          <div className="rounded-lg bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400 mb-1">분석 근거</p>
            <p className="text-sm text-gray-300 line-clamp-3">{signal.rationale}</p>
          </div>
        )}
      </div>
    </CommonCard>
  )
}

export default LatestSignalCard
