import { CommonModal } from '@core/components/CommonModal'
import { Badge } from '@core/components/ui/badge'
import { cn } from '@core/utils'
import { formatDateTime, formatPercent, formatCurrency } from '@core/utils/formatters'
import type { TradingSignal } from '@/core/types'
import { TrendingUp, TrendingDown, Minus, Brain, BarChart3, Clock, Cpu } from 'lucide-react'
import { SIGNAL_CONFIG, CONFIDENCE_MULTIPLIER, isRuleBasedSignal } from './signal-config'

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
  const isRuleBased = isRuleBasedSignal(signal.model_name)

  return (
    <CommonModal
      open={open}
      onOpenChange={onOpenChange}
      title={isRuleBased ? '자동 익절 신호 상세' : 'AI 신호 상세'}
      size="lg"
    >
      <div className="space-y-6">
        {/* Signal Type Header */}
        <div className={cn('p-5 rounded-xl border backdrop-blur-md', config.bgColor, config.borderColor)}>
          <div className="flex items-center gap-4">
            <div className={cn('p-3 rounded-lg ring-1 ring-inset', config.borderColor, 'bg-black/20')}>
              {icon}
            </div>
            <div>
              <h3 className={cn('text-xl font-bold font-heading tracking-tight', config.color)}>
                {config.label} <span className="text-zinc-500 text-lg font-normal">({signal.signal_type})</span>
              </h3>
              <p className="text-sm text-zinc-400 mt-0.5">
                {isRuleBased ? '시스템 자동 익절' : config.description}
              </p>
            </div>
            <Badge
              variant="outline"
              className={cn('ml-auto text-lg font-mono px-3 py-1 bg-black/20 backdrop-blur-md', config.color, config.borderColor)}
            >
              {formatPercent(signal.confidence * CONFIDENCE_MULTIPLIER, { decimals: 0 })}
            </Badge>
          </div>
        </div>

        {/* Reasoning */}
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Brain className="h-4 w-4 text-zinc-400" />
            <h4 className="font-medium text-foreground">{isRuleBased ? '실행 내역' : 'AI 분석 근거'}</h4>
          </div>
          <div className="p-4 bg-black/20 rounded-xl border border-white/5 leading-relaxed">
            <p className="text-sm text-zinc-300 whitespace-pre-wrap">
              {signal.reasoning}
            </p>
          </div>
        </div>

        {/* Price at Signal */}
        {signal.price_at_signal != null && (
          <div>
            <div className="flex items-center gap-2 mb-2.5">
              <BarChart3 className="h-4 w-4 text-zinc-400" />
              <h4 className="font-medium text-foreground">신호 생성 시 가격</h4>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                <p className="text-xs text-zinc-500 mb-1">당시 가격</p>
                <p className="text-sm font-mono-num font-medium text-foreground">
                  {formatCurrency(signal.price_at_signal)}
                </p>
              </div>

              {signal.price_after_4h != null && (
                <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                  <p className="text-xs text-zinc-500 mb-1">4시간 후 가격</p>
                  <p className="text-sm font-mono-num font-medium text-foreground">
                    {formatCurrency(signal.price_after_4h)}
                  </p>
                </div>
              )}

              {signal.price_after_24h != null && (
                <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                  <p className="text-xs text-zinc-500 mb-1">24시간 후 가격</p>
                  <p className="text-sm font-mono-num font-medium text-foreground">
                    {formatCurrency(signal.price_after_24h)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Model Info */}
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Cpu className="h-4 w-4 text-zinc-400" />
            <h4 className="font-medium text-foreground">{isRuleBased ? '실행 정보' : '모델 정보'}</h4>
          </div>
          <div className={cn('grid gap-3', isRuleBased ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-4')}>
            <div className="p-3 bg-black/20 rounded-xl border border-white/5">
              <p className="text-xs text-zinc-500 mb-1">{isRuleBased ? '실행 규칙' : '모델'}</p>
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-mono-num font-medium truncate text-foreground">
                  {signal.model_name}
                </p>
                {isRuleBased && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-amber-500/30 text-amber-400 bg-amber-500/10">
                    자동 익절
                  </Badge>
                )}
              </div>
            </div>
            <div className="p-3 bg-black/20 rounded-xl border border-white/5">
              <p className="text-xs text-zinc-500 mb-1">액션 스코어</p>
              <p className={cn(
                'text-sm font-mono-num font-medium',
                signal.action_score != null && signal.action_score > 0
                  ? 'text-emerald-400'
                  : signal.action_score != null && signal.action_score < 0
                    ? 'text-rose-500'
                    : 'text-zinc-400'
              )}>
                {signal.action_score != null
                  ? `${signal.action_score > 0 ? '+' : ''}${signal.action_score.toFixed(2)}`
                  : '-'}
              </p>
            </div>
            {!isRuleBased && (
              <>
                <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                  <p className="text-xs text-zinc-500 mb-1">입력 토큰</p>
                  <p className="text-sm font-mono-num font-medium text-foreground">
                    {signal.input_tokens.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 bg-black/20 rounded-xl border border-white/5">
                  <p className="text-xs text-zinc-500 mb-1">출력 토큰</p>
                  <p className="text-sm font-mono-num font-medium text-foreground">
                    {signal.output_tokens.toLocaleString()}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Outcome Evaluation */}
        {signal.outcome_evaluated && (
          <div className="p-3 bg-black/20 rounded-xl border border-white/5">
            <p className="text-xs text-zinc-500 mb-1">신호 정확성</p>
            <p className={cn(
              'text-sm font-medium',
              signal.outcome_correct ? 'text-emerald-400' : 'text-rose-500'
            )}>
              {signal.outcome_correct ? '정확함' : '부정확'}
            </p>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center gap-2 text-sm text-zinc-500 pt-4 border-t border-white/5 font-mono-num">
          <Clock className="h-4 w-4" />
          <span>생성 시각: {formatDateTime(signal.created_at)}</span>
        </div>
      </div>
    </CommonModal>
  )
}

export default SignalDetailModal
