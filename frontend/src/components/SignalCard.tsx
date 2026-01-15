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

// === 타입 정의 ===
interface SignalCardProps {
  /** AI 신호 데이터 */
  signal: TradingSignal;
  /** 컴팩트 모드 (분석 근거 숨김) */
  compact?: boolean;
}

// === 상수 ===
const SIGNAL_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  BUY: { bg: "bg-green-500", text: "text-green-600", label: "매수" },
  HOLD: { bg: "bg-yellow-500", text: "text-yellow-600", label: "보유" },
  SELL: { bg: "bg-red-500", text: "text-red-600", label: "매도" },
};

const CARD_CLASSES = "rounded-lg bg-white p-6 shadow";

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

  return (
    <div className={CARD_CLASSES}>
      {/* 헤더: 신호 타입 및 시간 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* 신호 배지 */}
          <span
            className={`inline-flex items-center rounded-lg px-4 py-2 text-lg font-bold text-white ${style.bg}`}
          >
            {style.label}
          </span>
          {/* 신호 타입 */}
          <span className={`text-sm font-medium ${style.text}`}>
            {signal.signal_type}
          </span>
        </div>
        {/* 생성 시간 */}
        <span className="text-sm text-gray-500">
          {formatDate(signal.created_at)}
        </span>
      </div>

      {/* 신뢰도 게이지 */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">신뢰도</span>
          <span className="font-semibold text-gray-900">{confidencePercent}%</span>
        </div>
        <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className={`h-full rounded-full ${style.bg} transition-all duration-500`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* AI 분석 근거 (컴팩트 모드가 아닐 때) */}
      {!compact && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700">AI 분석</h4>
          <p className="mt-1 text-sm leading-relaxed text-gray-600">
            {signal.reasoning}
          </p>
        </div>
      )}

      {/* 메타 정보 */}
      <div className="mt-4 flex items-center justify-between border-t pt-4 text-xs text-gray-400">
        <span>모델: {signal.model_name}</span>
        <span>
          토큰: {signal.input_tokens} / {signal.output_tokens}
        </span>
      </div>
    </div>
  );
};

export default SignalCard;
