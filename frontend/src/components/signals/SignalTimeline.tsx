import { cn } from '@core/utils'
import { formatDateTime, formatPercent, formatRelativeTime } from '@core/utils/formatters'
import { Badge } from '@core/components/ui/badge'
import type { TradingSignal } from '@/core/types'
import { TrendingUp, TrendingDown, Minus, Circle } from 'lucide-react'
import { SIGNAL_CONFIG_TIMELINE, CONFIDENCE_MULTIPLIER } from './signal-config'

interface SignalTimelineProps {
  signals: TradingSignal[]
  onSignalClick?: (signal: TradingSignal) => void
  className?: string
}

const SIGNAL_ICONS = {
  BUY: <TrendingUp className="h-4 w-4" />,
  SELL: <TrendingDown className="h-4 w-4" />,
  HOLD: <Minus className="h-4 w-4" />,
} as const

export function SignalTimeline({ signals, onSignalClick, className }: SignalTimelineProps) {
  if (signals.length === 0) {
    return null
  }

  return (
    <div className={cn('relative', className)}>
      <div className="absolute left-4 top-6 bottom-6 w-0.5 bg-border" />

      <div className="space-y-1">
        {signals.map((signal, index) => {
          const config = SIGNAL_CONFIG_TIMELINE[signal.signal_type]
          const icon = SIGNAL_ICONS[signal.signal_type]
          const isFirst = index === 0

          return (
            <div
              key={signal.id}
              onClick={() => onSignalClick?.(signal)}
              className={cn(
                'relative pl-10 pr-4 py-3 rounded-lg cursor-pointer',
                'hover:bg-surface/50 transition-colors',
                isFirst && 'bg-surface/30'
              )}
            >
              <div
                className={cn(
                  'absolute left-2 top-1/2 -translate-y-1/2',
                  'w-5 h-5 rounded-full flex items-center justify-center',
                  isFirst ? config.bgColor : 'bg-muted',
                  'ring-2 ring-background'
                )}
              >
                {isFirst ? (
                  <span className="text-white">{icon}</span>
                ) : (
                  <Circle className="h-2 w-2 text-muted-foreground" />
                )}
              </div>

              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge
                      variant="outline"
                      className={cn('text-xs font-bold', config.color, config.borderColor)}
                    >
                      {signal.signal_type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(signal.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {signal.reasoning}
                  </p>
                </div>

                <div className="flex flex-col items-end gap-1 shrink-0">
                  <Badge variant="secondary" className="text-xs font-mono">
                    {formatPercent(signal.confidence * CONFIDENCE_MULTIPLIER, { decimals: 0 })}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {formatDateTime(signal.created_at)}
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

export default SignalTimeline
