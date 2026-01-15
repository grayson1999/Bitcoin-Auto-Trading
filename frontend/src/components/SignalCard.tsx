/**
 * AI 신호 카드 컴포넌트 (T080)
 *
 * AI가 생성한 매매 신호를 카드 형태로 표시합니다.
 * - 신호 타입별 색상 (BUY/HOLD/SELL)
 * - 신뢰도 게이지
 * - AI 분석 근거
 */

import type { FC } from "react";
import type { TradingSignal } from "../hooks/useApi";
import { ArrowTrendingUpIcon, HandRaisedIcon, ArrowTrendingDownIcon, CpuChipIcon } from "@heroicons/react/24/outline";

// === 타입 정의 ===
interface SignalCardProps {
  /** AI 신호 데이터 */
  signal: TradingSignal;
  /** 컴팩트 모드 (분석 근거 숨김) */
  compact?: boolean;
}

// === 상수 ===
const SIGNAL_STYLES: Record<string, { bg: string; text: string; label: string; icon: any; gradient: string }> = {
  BUY: {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    label: "매수",
    icon: ArrowTrendingUpIcon,
    gradient: "from-emerald-500 to-teal-500"
  },
  HOLD: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    label: "관망",
    icon: HandRaisedIcon,
    gradient: "from-amber-400 to-orange-400"
  },
  SELL: {
    bg: "bg-rose-50",
    text: "text-rose-700",
    label: "매도",
    icon: ArrowTrendingDownIcon,
    gradient: "from-rose-500 to-pink-500"
  },
};

const CARD_CLASSES = "group relative overflow-hidden rounded-2xl glass-panel p-6 transition-all hover:shadow-[0_0_20px_rgba(250,204,21,0.15)] hover:border-banana-500/30";

/**
 * 날짜 포맷
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/**
 * 신뢰도 퍼센트 계산
 */
function getConfidencePercent(confidence: string): number {
  return Math.round(Number(confidence) * 100);
}

/**
 * SignalCard 컴포넌트
 */
const SignalCard: FC<SignalCardProps> = ({ signal, compact = false }) => {
  const style = SIGNAL_STYLES[signal.signal_type] || SIGNAL_STYLES.HOLD;
  const confidencePercent = getConfidencePercent(signal.confidence);
  const Icon = style.icon;

  return (
    <div className={CARD_CLASSES}>
      {/* Decorative gradient background opacity */}
      <div className={`absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full opacity-10 blur-xl bg-gradient-to-br ${style.gradient}`} />

      {/* 헤더: 신호 타입 및 시간 */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          {/* 신호 배지 */}
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold text-white shadow-lg bg-gradient-to-r ${style.gradient}`}
          >
            <Icon className="w-4 h-4" />
            {style.label}
          </span>
          <span className="text-xs font-medium text-dark-text-secondary bg-white/5 border border-white/5 rounded-md px-2 py-1">
            {signal.signal_type}
          </span>
        </div>
        {/* 생성 시간 */}
        <span className="text-xs font-medium text-dark-text-muted">
          {formatDate(signal.created_at)}
        </span>
      </div>

      {/* 신뢰도 게이지 */}
      <div className="rounded-xl bg-white/5 p-4 border border-white/5 relative z-10">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-dark-text-secondary font-medium flex items-center gap-2">
            <CpuChipIcon className="w-4 h-4 text-banana-400" />
            AI Confidence
          </span>
          <span className="font-bold text-white text-glow">{confidencePercent}%</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${style.gradient} transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(0,0,0,0.5)]`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* AI 분석 근거 (컴팩트 모드가 아닐 때) */}
      {!compact && (
        <div className="mt-5">
          <h4 className="text-sm font-semibold text-slate-900 mb-2">Analysis Reasoning</h4>
          <p className="text-sm leading-relaxed text-slate-600 bg-white rounded-lg border border-slate-100 p-3 shadow-sm">
            {signal.reasoning}
          </p>
        </div>
      )}

      {/* 메타 정보 */}
      <div className="mt-6 flex items-center justify-between border-t border-dark-border pt-4 text-xs relative z-10">
        <div className="flex items-center gap-2 text-dark-text-secondary">
          <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/5 font-medium">Model</span>
          {signal.model_name}
        </div>
        <div className="flex items-center gap-4 text-dark-text-muted">
          <span>In: {signal.input_tokens}</span>
          <span>Out: {signal.output_tokens}</span>
        </div>
      </div>
    </div>
  );
};

export default SignalCard;
