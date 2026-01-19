/**
 * AI 신호 카드 컴포넌트 (T080)
 *
 * AI가 생성한 매매 신호를 카드 형태로 표시합니다.
 * - 신호 타입별 색상 (BUY/HOLD/SELL)
 * - 신뢰도 게이지
 * - AI 분석 근거
 */

import { useState, type ComponentType, type FC, type SVGProps } from "react";
import type { TradingSignal } from "../hooks/useApi";
import { ArrowTrendingUpIcon, HandRaisedIcon, ArrowTrendingDownIcon, CpuChipIcon, ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, XCircleIcon, ClockIcon } from "@heroicons/react/24/outline";

// === 타입 정의 ===
/** Heroicons 아이콘 컴포넌트 타입 */
type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

interface SignalCardProps {
  /** AI 신호 데이터 */
  signal: TradingSignal;
  /** 컴팩트 모드 (분석 근거 숨김) */
  compact?: boolean;
}

// === 상수 ===
const SIGNAL_STYLES: Record<string, { bg: string; text: string; label: string; icon: HeroIcon; gradient: string }> = {
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

const CARD_CLASSES = "group relative overflow-hidden rounded-2xl glass-panel p-6 transition-all duration-300 hover:shadow-[0_0_20px_rgba(250,204,21,0.15)] hover:border-banana-500/30 active:scale-[0.98]";

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
 * 가격 포맷
 */
function formatPrice(price: string | null | undefined): string {
  if (!price) return "-";
  return Number(price).toLocaleString("ko-KR", { maximumFractionDigits: 0 }) + "원";
}

/**
 * Bias 라벨 매핑
 */
function getBiasLabel(bias: string): { label: string; color: string } {
  const map: Record<string, { label: string; color: string }> = {
    strong_buy: { label: "강력 매수", color: "text-emerald-400" },
    buy: { label: "매수", color: "text-green-400" },
    neutral: { label: "중립", color: "text-gray-400" },
    sell: { label: "매도", color: "text-orange-400" },
    strong_sell: { label: "강력 매도", color: "text-rose-400" },
  };
  return map[bias] || { label: bias, color: "text-gray-400" };
}

/**
 * 추세 라벨 매핑
 */
function getTrendLabel(trend: string): { label: string; color: string } {
  const map: Record<string, { label: string; color: string }> = {
    bullish: { label: "상승", color: "text-emerald-400" },
    bearish: { label: "하락", color: "text-rose-400" },
    sideways: { label: "횡보", color: "text-amber-400" },
  };
  return map[trend] || { label: trend, color: "text-gray-400" };
}

/**
 * SignalCard 컴포넌트
 */
const SignalCard: FC<SignalCardProps> = ({ signal, compact = false }) => {
  const style = SIGNAL_STYLES[signal.signal_type] || SIGNAL_STYLES.HOLD;
  const confidencePercent = getConfidencePercent(signal.confidence);
  const Icon = style.icon;
  const [isExpanded, setIsExpanded] = useState(false);

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

      {/* 기술적 스냅샷 */}
      {signal.technical_snapshot && (
        <div className="mt-4 grid grid-cols-2 gap-2 relative z-10">
          {/* Confluence Score */}
          <div className="bg-white/5 rounded-lg p-2 border border-white/5">
            <span className="text-xs text-dark-text-muted">Confluence</span>
            <p className="text-sm font-bold text-banana-400">
              {(signal.technical_snapshot.confluence_score * 100).toFixed(0)}%
            </p>
          </div>
          {/* Overall Bias */}
          <div className="bg-white/5 rounded-lg p-2 border border-white/5">
            <span className="text-xs text-dark-text-muted">Bias</span>
            <p className={`text-sm font-bold ${getBiasLabel(signal.technical_snapshot.overall_bias).color}`}>
              {getBiasLabel(signal.technical_snapshot.overall_bias).label}
            </p>
          </div>
          {/* Timeframe Trends */}
          {signal.technical_snapshot.timeframes && (
            <>
              {Object.entries(signal.technical_snapshot.timeframes).map(([tf, data]) => (
                <div key={tf} className="bg-white/5 rounded-lg p-2 border border-white/5">
                  <span className="text-xs text-dark-text-muted">{tf.toUpperCase()}</span>
                  <div className="flex items-center gap-1">
                    <span className={`text-xs font-medium ${getTrendLabel(data.trend).color}`}>
                      {getTrendLabel(data.trend).label}
                    </span>
                    <span className="text-xs text-dark-text-muted">
                      ({(data.strength * 100).toFixed(0)}%)
                    </span>
                  </div>
                  {data.indicators && (
                    <span className="text-xs text-dark-text-muted">
                      RSI {data.indicators.rsi_14?.toFixed(0) ?? '-'}
                    </span>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* 성과 추적 */}
      {signal.price_at_signal && (
        <div className="mt-4 bg-white/5 rounded-lg p-3 border border-white/5 relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <ClockIcon className="w-4 h-4 text-dark-text-muted" />
            <span className="text-xs font-medium text-dark-text-secondary">성과 추적</span>
            {signal.outcome_evaluated && (
              signal.outcome_correct ? (
                <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
              ) : (
                <XCircleIcon className="w-4 h-4 text-rose-400" />
              )
            )}
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-dark-text-muted">신호 시</span>
              <p className="text-white font-medium">{formatPrice(signal.price_at_signal)}</p>
            </div>
            <div>
              <span className="text-dark-text-muted">4H 후</span>
              <p className="text-white font-medium">{formatPrice(signal.price_after_4h)}</p>
            </div>
            <div>
              <span className="text-dark-text-muted">24H 후</span>
              <p className="text-white font-medium">{formatPrice(signal.price_after_24h)}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI 분석 근거 (컴팩트 모드가 아닐 때) */}
      {!compact && (
        <div className="mt-5 relative z-10">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center justify-between w-full text-left group/btn"
          >
            <h4 className="text-sm font-semibold text-dark-text-secondary group-hover/btn:text-white transition-colors">
              AI Analysis Reasoning
            </h4>
            {isExpanded ? (
              <ChevronUpIcon className="w-4 h-4 text-dark-text-muted group-hover/btn:text-white transition-colors" />
            ) : (
              <ChevronDownIcon className="w-4 h-4 text-dark-text-muted group-hover/btn:text-white transition-colors" />
            )}
          </button>

          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${isExpanded ? "max-h-96 opacity-100 mt-2" : "max-h-0 opacity-0"
              }`}
          >
            <p className="text-sm leading-relaxed text-white bg-white/5 rounded-lg border border-white/10 p-3">
              {signal.reasoning}
            </p>
          </div>
          {!isExpanded && (
            <p className="text-xs text-dark-text-muted mt-1 truncate">
              {signal.reasoning}
            </p>
          )}
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
