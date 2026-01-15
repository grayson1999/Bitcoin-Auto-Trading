/**
 * AI 거래 신호 페이지 컴포넌트 (T076)
 *
 * AI가 생성한 거래 신호와 신뢰도 점수를 표시합니다.
 * - 최신 AI 신호 목록
 * - 신호별 신뢰도 점수
 * - 수동 신호 생성
 */

import { useState, type FC } from "react";
import { useSignals, useGenerateSignal } from "../hooks/useApi";
import SignalCard from "../components/SignalCard";

// === 상수 ===
const SIGNAL_TYPES = [
  { value: "all", label: "전체" },
  { value: "BUY", label: "매수" },
  { value: "HOLD", label: "보유" },
  { value: "SELL", label: "매도" },
];

/**
 * Signals 컴포넌트
 */
const Signals: FC = () => {
  const [signalType, setSignalType] = useState("all");
  const { data, isLoading, error } = useSignals(50, signalType);
  const generateMutation = useGenerateSignal();

  // 신호 수동 생성
  const handleGenerate = () => {
    if (window.confirm("새로운 AI 신호를 생성하시겠습니까?")) {
      generateMutation.mutate();
    }
  };

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white text-glow">AI 거래 신호</h2>
          <p className="text-dark-text-secondary mt-1">
            AI가 생성한 거래 신호와 신뢰도 점수를 확인합니다.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* 필터 */}
          <select
            value={signalType}
            onChange={(e) => setSignalType(e.target.value)}
            className="rounded-xl border border-dark-border px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 bg-dark-surface text-white shadow-lg"
          >
            {SIGNAL_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {/* 수동 생성 버튼 */}
          <button
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-[0_0_15px_rgba(14,165,233,0.4)] transition-all hover:shadow-[0_0_20px_rgba(14,165,233,0.6)]"
          >
            {generateMutation.isPending ? "생성 중..." : "신호 생성"}
          </button>
        </div>
      </div>

      {/* 생성 에러 메시지 */}
      {generateMutation.isError && (
        <div className="rounded-lg bg-red-50 p-4 text-center text-red-600">
          신호 생성 실패: {generateMutation.error?.message || "알 수 없는 오류"}
        </div>
      )}

      {/* 생성 성공 메시지 */}
      {generateMutation.isSuccess && (
        <div className="rounded-lg bg-green-50 p-4 text-center text-green-600">
          신호가 성공적으로 생성되었습니다!
        </div>
      )}

      {/* 로딩 상태 */}
      {isLoading && (
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
            <p className="mt-3 text-gray-500">신호 로딩 중...</p>
          </div>
        </div>
      )}

      {/* 에러 메시지 */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-center text-red-600">
          신호를 불러올 수 없습니다. 백엔드 서버를 확인하세요.
        </div>
      )}

      {/* 신호 목록 */}
      {data && (
        <div className="space-y-4">
          {data.items.length === 0 ? (
            <div className="rounded-2xl glass-panel p-12 text-center text-dark-text-muted border-dashed border-2 border-white/10">
              생성된 신호가 없습니다. &quot;신호 생성&quot; 버튼을 눌러 AI 신호를 생성하세요.
            </div>
          ) : (
            <>
              {/* 신호 개수 표시 */}
              <p className="text-sm text-dark-text-secondary">총 {data.total}개의 신호</p>

              {/* 신호 카드 그리드 */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {data.items.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default Signals;
