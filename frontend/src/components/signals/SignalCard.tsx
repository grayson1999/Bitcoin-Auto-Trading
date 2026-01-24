import { cn } from '@core/utils'
import { formatDateTime, formatPercent } from '@core/utils/formatters'
import { Badge } from '@core/components/ui/badge'
import type { TradingSignal } from '@/core/types'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { SIGNAL_CONFIG, CONFIDENCE_MULTIPLIER } from './signal-config'

interface SignalCardProps {
  signal: TradingSignal
  onClick?: () => void
  className?: string
}

const SIGNAL_ICONS = {
  BUY: <TrendingUp className="h-5 w-5" />,
  SELL: <TrendingDown className="h-5 w-5" />,
  HOLD: <Minus className="h-5 w-5" />,
} as const

export function SignalCard({ signal, onClick, className }: SignalCardProps) {
  const config = SIGNAL_CONFIG[signal.signal_type]
  const icon = SIGNAL_ICONS[signal.signal_type]

  return (
    <div
      onClick={onClick}
      className={cn(
        'p-4 rounded-lg border cursor-pointer transition-all',
        'hover:shadow-lg hover:scale-[1.02]',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={cn('flex items-center gap-2', config.color)}>
          {icon}
          <span className="font-bold text-lg">{signal.signal_type}</span>
        </div>
        <Badge variant="outline" className={cn('font-mono', config.color, config.borderColor)}>
          {formatPercent(signal.confidence * CONFIDENCE_MULTIPLIER, { decimals: 0 })}
        </Badge>
      </div>

      <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
        {signal.reasoning}
      </p>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{formatDateTime(signal.created_at)}</span>
        <span className={cn('font-medium', config.color)}>{config.label}</span>
      </div>
    </div>
  )
}

export default SignalCard
