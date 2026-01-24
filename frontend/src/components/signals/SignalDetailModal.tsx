import { CommonModal } from '@core/components/CommonModal'
import { Badge } from '@core/components/ui/badge'
import { cn } from '@core/utils'
import { formatDateTime, formatPercent, formatCurrency } from '@core/utils/formatters'
import type { TradingSignal } from '@/core/types'
import { TrendingUp, TrendingDown, Minus, Brain, BarChart3, Clock, Cpu } from 'lucide-react'
import { SIGNAL_CONFIG, CONFIDENCE_MULTIPLIER } from './signal-config'

interface SignalDetailModalProps {
  signal: TradingSignal | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const SIGNAL_ICONS = {
  BUY: <TrendingUp className="h-6 w-6" />,
  SELL: <TrendingDown className="h-6 w-6" />,
  HOLD: <Minus className="h-6 w-6" />,
} as const

export function SignalDetailModal({ signal, open, onOpenChange }: SignalDetailModalProps) {
  if (!signal) return null

  const config = SIGNAL_CONFIG[signal.signal_type]
  const icon = SIGNAL_ICONS[signal.signal_type]

  return (
    <CommonModal
      open={open}
      onOpenChange={onOpenChange}
      title="AI 신호 상세"
      size="lg"
    >
      <div className="space-y-6">
        {/* Signal Type Header */}
        <div className={cn('p-4 rounded-lg border', config.bgColor, config.borderColor)}>
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-full', config.bgColor, config.color)}>
              {icon}
            </div>
            <div>
              <h3 className={cn('text-xl font-bold', config.color)}>
                {config.label} ({signal.signal_type})
              </h3>
              <p className="text-sm text-muted-foreground">
                {config.description}
              </p>
            </div>
            <Badge
              variant="outline"
              className={cn('ml-auto text-lg font-mono', config.color, config.borderColor)}
            >
              {formatPercent(signal.confidence * CONFIDENCE_MULTIPLIER, { decimals: 0 })}
            </Badge>
          </div>
        </div>

        {/* Reasoning */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <h4 className="font-medium">AI 분석 근거</h4>
          </div>
          <div className="p-4 bg-surface rounded-lg border border-border">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {signal.reasoning}
            </p>
          </div>
        </div>

        {/* Price at Signal */}
        {signal.price_at_signal != null && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium">신호 생성 시 가격</h4>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-surface rounded-lg border border-border">
                <p className="text-xs text-muted-foreground mb-1">당시 가격</p>
                <p className="text-sm font-mono font-medium">
                  {formatCurrency(signal.price_at_signal)}
                </p>
              </div>

              {signal.price_after_4h != null && (
                <div className="p-3 bg-surface rounded-lg border border-border">
                  <p className="text-xs text-muted-foreground mb-1">4시간 후 가격</p>
                  <p className="text-sm font-mono font-medium">
                    {formatCurrency(signal.price_after_4h)}
                  </p>
                </div>
              )}

              {signal.price_after_24h != null && (
                <div className="p-3 bg-surface rounded-lg border border-border">
                  <p className="text-xs text-muted-foreground mb-1">24시간 후 가격</p>
                  <p className="text-sm font-mono font-medium">
                    {formatCurrency(signal.price_after_24h)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Model Info */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <h4 className="font-medium">모델 정보</h4>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-surface rounded-lg border border-border">
              <p className="text-xs text-muted-foreground mb-1">모델</p>
              <p className="text-sm font-mono font-medium truncate">
                {signal.model_name}
              </p>
            </div>
            <div className="p-3 bg-surface rounded-lg border border-border">
              <p className="text-xs text-muted-foreground mb-1">입력 토큰</p>
              <p className="text-sm font-mono font-medium">
                {signal.input_tokens.toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-surface rounded-lg border border-border">
              <p className="text-xs text-muted-foreground mb-1">출력 토큰</p>
              <p className="text-sm font-mono font-medium">
                {signal.output_tokens.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Outcome Evaluation */}
        {signal.outcome_evaluated && (
          <div className="p-3 bg-surface rounded-lg border border-border">
            <p className="text-xs text-muted-foreground mb-1">신호 정확성</p>
            <p className={cn(
              'text-sm font-medium',
              signal.outcome_correct ? 'text-up' : 'text-down'
            )}>
              {signal.outcome_correct ? '정확함' : '부정확'}
            </p>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground pt-4 border-t border-border">
          <Clock className="h-4 w-4" />
          <span>생성 시각: {formatDateTime(signal.created_at)}</span>
        </div>
      </div>
    </CommonModal>
  )
}

export default SignalDetailModal
