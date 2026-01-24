import { useState, type ComponentType, type FC, type SVGProps } from "react";
import { createPortal } from "react-dom";
import type { TradingSignal } from "../hooks/useApi";
import { ArrowTrendingUpIcon, HandRaisedIcon, ArrowTrendingDownIcon, CpuChipIcon } from "@heroicons/react/24/outline";
import { formatDate, getConfidencePercent, getBiasLabel } from "../utils/formatters";
import SignalDetailModal from "./SignalDetailModal";

// === 타입 정의 ===
/** Heroicons 아이콘 컴포넌트 타입 */
type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

interface SignalCardProps {
  /** AI 신호 데이터 */
  signal: TradingSignal;
  /** 컴팩트 모드 (분석 근거 숨김 - deprecated but kept for compatibility) */
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

const CARD_CLASSES = "group relative overflow-hidden rounded-2xl glass-panel p-6 transition-all duration-300 hover:shadow-[0_0_20px_rgba(250,204,21,0.15)] hover:border-banana-500/30 active:scale-[0.98] cursor-pointer";

/**
 * SignalCard 컴포넌트
 */
const SignalCard: FC<SignalCardProps> = ({ signal }) => {
  const style = SIGNAL_STYLES[signal.signal_type] || SIGNAL_STYLES.HOLD;
  const confidencePercent = getConfidencePercent(signal.confidence);
  const Icon = style.icon;
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <div className={CARD_CLASSES} onClick={() => setShowModal(true)}>
        {/* Decorative gradient background opacity */}
        <div className={`absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full opacity-10 blur-xl bg-gradient-to-br ${style.gradient}`} />

        {/* 헤더: 신호 타입 및 시간 */}
        <div className="flex items-center justify-between mb-4 relative z-10">
          <div className="flex items-center gap-3">
            {/* 신호 배지 */}
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold text-white shadow-lg bg-gradient-to-r ${style.gradient}`}
            >
              <Icon className="w-4 h-4" />
              {style.label}
            </span>
          </div>
          {/* 생성 시간 */}
          <span className="text-xs font-medium text-dark-text-muted">
            {formatDate(signal.created_at)}
          </span>
        </div>

        {/* 주요 정보 요약 */}
        <div className="grid grid-cols-2 gap-3 relative z-10">
          {/* 신뢰도 */}
          <div className="rounded-xl bg-white/5 p-3 border border-white/5">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-dark-text-secondary font-medium flex items-center gap-1">
                <CpuChipIcon className="w-3 h-3 text-banana-400" />
                신뢰도
              </span>
            </div>
            <div className="flex items-end gap-2">
              <span className="text-lg font-bold text-white text-glow">{confidencePercent}%</span>
              <div className="flex-1 pb-1.5 h-full">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r ${style.gradient}`}
                    style={{ width: `${confidencePercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 시장 바이어스 */}
          {signal.technical_snapshot && (
            <div className="rounded-xl bg-white/5 p-3 border border-white/5 flex flex-col justify-center">
              <span className="text-xs text-dark-text-secondary mb-1">시장 방향성</span>
              <p className={`text-base font-bold ${getBiasLabel(signal.technical_snapshot.overall_bias).color}`}>
                {getBiasLabel(signal.technical_snapshot.overall_bias).label}
              </p>
            </div>
          )}
        </div>

        {/* AI 분석 요약 (의사결정 섹션 우선 표시) */}
        <div className="mt-4 relative z-10">
          <p className="text-sm text-dark-text-muted line-clamp-2">
            {(() => {
              const sections = signal.reasoning.split('\n\n');
              // 의사결정/분석 섹션을 우선 찾음
              const decisionSection = sections.find(s => s.startsWith('💡'));
              if (decisionSection) {
                // "💡 의사결정\n내용" 형태에서 내용만 추출
                const lines = decisionSection.split('\n');
                return lines.slice(1).join(' ') || lines[0];
              }
              // 없으면 첫 번째 섹션 표시
              return sections[0];
            })()}
          </p>
          <p className="text-xs text-banana-400 mt-2 font-medium group-hover:underline underline-offset-4 decoration-banana-400/50">
            상세 정보 보기 →
          </p>
        </div>
      </div>

      {showModal && createPortal(
        <SignalDetailModal signal={signal} onClose={() => setShowModal(false)} />,
        document.body
      )}
    </>
  );
};

export default SignalCard;
