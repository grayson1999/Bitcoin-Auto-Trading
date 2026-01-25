import { cn } from '@core/utils'
import { formatDateTime, formatPercent } from '@core/utils/formatters'
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
        'glass-card p-5 cursor-pointer transition-all duration-300',
        'hover:border-primary/30 hover:bg-zinc-900/60', // Subtle hover effect
        config.bgColor, // Very subtle tint
        className
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={cn('flex items-center gap-2.5', config.color)}>
          <div className={cn('p-2 rounded-lg bg-black/20 ring-1 ring-inset', config.borderColor)}>
            {icon}
          </div>
          <span className="font-heading font-semibold text-lg tracking-tight">{signal.signal_type}</span>
        </div>
        <div className={cn('flex items-center px-2.5 py-1 rounded-md bg-black/20 border', config.borderColor)}>
          <span className={cn('text-sm font-mono-num font-medium', config.color)}>
            {formatPercent(signal.confidence * CONFIDENCE_MULTIPLIER, { decimals: 0 })}
          </span>
        </div>
      </div>

      <p className="text-sm text-zinc-400 line-clamp-2 mb-4 leading-relaxed h-10">
        {signal.reasoning}
      </p>

      <div className="flex items-center justify-between pt-4 border-t border-white/5">
        <span className="text-xs text-zinc-500 font-mono-num">
          {formatDateTime(signal.created_at)}
        </span>
        <span className={cn('text-xs font-medium px-2 py-0.5 rounded-full bg-black/20', config.color)}>
          {config.label}
        </span>
      </div>
    </div>
  )
}

export default SignalCard
