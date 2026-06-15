import { cn } from '@core/utils'
import { formatDateTime, formatRelativeTime } from '@core/utils/formatters'
import { Badge } from '@core/components/ui/badge'
import { Skeleton } from '@core/components/ui/skeleton'
import type { RiskEvent } from '@/core/types'
import {
  TrendingDown,
  AlertTriangle,
  Activity,
  AlertCircle,
  Info,
  type LucideIcon,
} from 'lucide-react'

interface EventTypeConfig {
  label: string
  /** text color */
  color: string
  /** circle background tint */
  bgColor: string
  Icon: LucideIcon
}

const EVENT_TYPE_CONFIG: Record<string, EventTypeConfig> = {
  STOP_LOSS: {
    label: '손절',
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/15 border-rose-500/30',
    Icon: TrendingDown,
  },
  DAILY_LIMIT: {
    label: '일일한도',
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/15 border-rose-500/30',
    Icon: AlertTriangle,
  },
  VOLATILITY_HALT: {
    label: '변동성중단',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/15 border-amber-500/30',
    Icon: Activity,
  },
  POSITION_LIMIT: {
    label: '포지션한도',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/15 border-amber-500/30',
    Icon: AlertTriangle,
  },
  SYSTEM_ERROR: {
    label: '시스템오류',
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/15 border-rose-500/30',
    Icon: AlertCircle,
  },
}

const DEFAULT_CONFIG: EventTypeConfig = {
  label: '기타',
  color: 'text-zinc-400',
  bgColor: 'bg-zinc-500/15 border-zinc-500/30',
  Icon: Info,
}

interface RiskEventTimelineProps {
  events: RiskEvent[]
  isLoading?: boolean
  className?: string
}

export function RiskEventTimeline({ events, isLoading, className }: RiskEventTimelineProps) {
  if (isLoading) {
    return (
      <div className={cn('space-y-1', className)}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-3">
            <Skeleton className="h-8 w-8 rounded-full shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-56" />
            </div>
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Info className="h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground">
          리스크 이벤트가 없습니다 (안정적으로 운영 중)
        </p>
      </div>
    )
  }

  return (
    <div className={cn('relative', className)}>
      {/* vertical connector line */}
      <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-border" />

      <div className="space-y-1">
        {events.map((event) => {
          const config = EVENT_TYPE_CONFIG[event.event_type] ?? DEFAULT_CONFIG
          const Icon = config.Icon

          return (
            <div
              key={event.id}
              className="relative pl-14 pr-4 py-3 rounded-lg hover:bg-white/5 transition-colors"
            >
              {/* icon node */}
              <div
                className={cn(
                  'absolute left-2 top-1/2 -translate-y-1/2',
                  'w-8 h-8 rounded-full flex items-center justify-center border',
                  'ring-2 ring-background',
                  config.bgColor
                )}
              >
                <Icon className={cn('h-4 w-4', config.color)} />
              </div>

              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <Badge
                      variant="outline"
                      className={cn('text-xs font-bold border-current/30', config.color)}
                    >
                      {config.label}
                    </Badge>
                    <span className="text-xs font-mono text-muted-foreground">
                      발동값 {event.trigger_value}%
                    </span>
                    {event.notified && (
                      <span className="text-[10px] text-muted-foreground/70">
                        Telegram 전송됨
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {event.action_taken}
                  </p>
                </div>

                <div className="flex flex-col items-end gap-1 shrink-0">
                  <span
                    className="text-xs text-muted-foreground"
                    title={formatDateTime(event.created_at)}
                  >
                    {formatRelativeTime(event.created_at)}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default RiskEventTimeline
