/**
 * 대시보드 페이지 컴포넌트 (T074)
 *
 * 거래 활동, 포지션, 성과 지표의 개요를 표시합니다.
 * - 실시간 시세 차트 (T083: 5초 자동 새로고침)
 * - 포지션 현황
 * - 최신 AI 신호
 * - 리스크 상태
 */

import type { FC } from "react";
import {
  useDashboardSummary,
  useRiskStatus,
  useHaltTrading,
  useResumeTrading,
} from "../hooks/useApi";
import PriceChart from "../components/PriceChart";
import SignalCard from "../components/SignalCard";
import RiskStatus from "../components/RiskStatus";

// === 상수 ===
const REFRESH_INTERVAL_MS = 5000; // T083: 5초 자동 새로고침

/**
 * 금액 포맷
 */
function formatKRW(amount: string | number): string {
  const num = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Dashboard 컴포넌트
 */
const Dashboard: FC = () => {
  // T083: 5초 자동 새로고침
  const { data: summary, isLoading, error } = useDashboardSummary(REFRESH_INTERVAL_MS);
  const { data: riskStatus } = useRiskStatus();

  const haltMutation = useHaltTrading();
  const resumeMutation = useResumeTrading();

  // 거래 중단 핸들러
  const handleHalt = () => {
    const reason = window.prompt("중단 사유를 입력하세요:");
    if (reason) {
      haltMutation.mutate({ reason });
    }
  };

  // 거래 재개 핸들러
  const handleResume = () => {
    if (window.confirm("거래를 재개하시겠습니까?")) {
      resumeMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-3 text-gray-500">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="rounded-lg bg-red-50 p-6 text-center">
        <p className="text-red-600">
          데이터를 불러올 수 없습니다. 백엔드 서버를 확인하세요.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">대시보드</h2>
          <p className="text-gray-600">
            거래 활동, 포지션, 성과 지표의 개요를 확인합니다.
          </p>
        </div>
        {/* 거래 상태 배지 */}
        <div className="flex items-center gap-2">
          {summary.is_trading_active ? (
            <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-green-500"></span>
              거래 활성
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-red-500"></span>
              거래 중단
            </span>
          )}
        </div>
      </div>

      {/* T084: 반응형 그리드 레이아웃 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 가격 차트 */}
        <PriceChart
          currentPrice={Number(summary.current_price)}
          change24h={summary.price_change_24h}
        />

        {/* 리스크 상태 */}
        {riskStatus && (
          <RiskStatus
            status={riskStatus}
            onHalt={handleHalt}
            onResume={handleResume}
          />
        )}
      </div>

      {/* 요약 카드들 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* 총 평가금액 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">총 평가금액</h3>
          <p className="mt-2 text-2xl font-semibold text-gray-900">
            {summary.balance ? formatKRW(summary.balance.total_krw) : "-"}
          </p>
        </div>

        {/* KRW 잔고 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">KRW 잔고</h3>
          <p className="mt-2 text-2xl font-semibold text-gray-900">
            {summary.balance ? formatKRW(summary.balance.krw) : "-"}
          </p>
        </div>

        {/* 일일 손익 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">일일 손익</h3>
          <p
            className={`mt-2 text-2xl font-semibold ${
              Number(summary.daily_pnl) >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {formatKRW(summary.daily_pnl)}
            <span className="ml-2 text-sm">
              ({summary.daily_pnl_pct >= 0 ? "+" : ""}
              {summary.daily_pnl_pct.toFixed(2)}%)
            </span>
          </p>
        </div>

        {/* 오늘 거래 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">오늘 거래</h3>
          <p className="mt-2 text-2xl font-semibold text-gray-900">
            {summary.today_trade_count}건
          </p>
        </div>
      </div>

      {/* 포지션 & 최신 신호 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 현재 포지션 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">현재 포지션</h3>
          {summary.position && Number(summary.position.quantity) > 0 ? (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">보유량</span>
                <span className="font-medium">
                  {Number(summary.position.quantity).toFixed(4)} XRP
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">평균 매수가</span>
                <span className="font-medium">
                  {formatKRW(summary.position.avg_buy_price)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">평가금액</span>
                <span className="font-medium">
                  {formatKRW(summary.position.current_value)}
                </span>
              </div>
              <div className="flex justify-between border-t pt-3">
                <span className="text-gray-600">미실현 손익</span>
                <span
                  className={`font-semibold ${
                    Number(summary.position.unrealized_pnl) >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {formatKRW(summary.position.unrealized_pnl)}
                  <span className="ml-1 text-sm">
                    ({summary.position.unrealized_pnl_pct >= 0 ? "+" : ""}
                    {summary.position.unrealized_pnl_pct.toFixed(2)}%)
                  </span>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-center text-gray-500">포지션 없음</p>
          )}
        </div>

        {/* 최신 AI 신호 */}
        <div>
          <h3 className="mb-4 text-lg font-semibold text-gray-900">최신 AI 신호</h3>
          {summary.latest_signal ? (
            <SignalCard signal={summary.latest_signal} />
          ) : (
            <div className="rounded-lg bg-white p-6 text-center text-gray-500 shadow">
              생성된 신호가 없습니다
            </div>
          )}
        </div>
      </div>

      {/* 마지막 업데이트 시간 */}
      <div className="text-right text-xs text-gray-400">
        마지막 업데이트: {new Date(summary.updated_at).toLocaleString("ko-KR")}
      </div>
    </div>
  );
};

export default Dashboard;
