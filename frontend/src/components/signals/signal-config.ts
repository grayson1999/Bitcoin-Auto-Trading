import type { SignalType } from '@/core/types'

/** Signal display configuration for consistent styling across components */
export interface SignalConfig {
  color: string
  bgColor: string
  borderColor: string
  label: string
  description?: string
}

/** Base signal configuration - use with appropriate icon sizes per component */
export const SIGNAL_CONFIG: Record<SignalType, SignalConfig> = {
  BUY: {
    color: 'text-up',
    bgColor: 'bg-emerald-500/5',
    borderColor: 'border-emerald-500/20',
    label: '매수',
    description: 'AI가 매수를 권장합니다',
  },
  SELL: {
    color: 'text-down',
    bgColor: 'bg-rose-500/5',
    borderColor: 'border-rose-500/20',
    label: '매도',
    description: 'AI가 매도를 권장합니다',
  },
  HOLD: {
    color: 'text-neutral',
    bgColor: 'bg-zinc-500/5',
    borderColor: 'border-zinc-500/20',
    label: '홀드',
    description: 'AI가 관망을 권장합니다',
  },
}

/** Timeline-specific config with solid background colors */
export const SIGNAL_CONFIG_TIMELINE: Record<SignalType, SignalConfig> = {
  BUY: {
    ...SIGNAL_CONFIG.BUY,
    bgColor: 'bg-up',
    borderColor: 'border-up',
  },
  SELL: {
    ...SIGNAL_CONFIG.SELL,
    bgColor: 'bg-down',
    borderColor: 'border-down',
  },
  HOLD: {
    ...SIGNAL_CONFIG.HOLD,
    bgColor: 'bg-neutral',
    borderColor: 'border-neutral',
  },
}

/** Confidence display multiplier (backend returns 0~1, display as percentage) */
export const CONFIDENCE_MULTIPLIER = 100
