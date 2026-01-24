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
  useMarketHistory,
  useRiskStatus,
  useHaltTrading,
  useResumeTrading,
  useConfig,
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
 * 차트용 시간 포맷 (HH:MM KST)
 */
function formatChartTime(isoTimestamp: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Seoul",
  }).format(new Date(isoTimestamp));
}

/**
 * Dashboard 컴포넌트
 */
const Dashboard: FC = () => {
  // T083: 5초 자동 새로고침
  const { data: summary, isLoading, error } = useDashboardSummary(REFRESH_INTERVAL_MS);
  // 24시간 동안 60분 간격 (시간당 1개) - 하루 전체 보기
  const { data: marketHistory } = useMarketHistory(24, 100, REFRESH_INTERVAL_MS, 60);
  const { data: riskStatus } = useRiskStatus();
  const { data: config } = useConfig();

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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white text-glow">대시보드</h2>
          <p className="text-dark-text-secondary mt-1 text-sm sm:text-base">
            거래 활동, 포지션, 성과 지표의 개요를 확인합니다.
          </p>
        </div>
        {/* 거래 상태 배지 */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {summary.is_trading_active ? (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-sm font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
              거래 중
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-rose-100 px-3 py-1 text-sm font-medium text-rose-800 ring-1 ring-inset ring-rose-600/20">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-rose-500"></span>
              거래 중단
            </span>
          )}
        </div>
      </div>

      {/* T084: 반응형 그리드 레이아웃 */}
      <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
        {/* 가격 차트 */}
        <PriceChart
          currentPrice={Number(summary.current_price)}
          change24h={summary.price_change_24h}
          symbol={summary.market}
          data={
            marketHistory?.items && marketHistory.items.length > 0
              ? marketHistory.items.map((item) => ({
                  time: formatChartTime(item.timestamp),
                  price: Number(item.price),
                }))
              : undefined
          }
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* 총 평가금액 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="text-sm font-medium text-dark-text-secondary">총 평가금액</h3>
          <p className="mt-2 text-xl sm:text-2xl font-bold text-white tracking-tight courier text-glow">
            {summary.balance ? formatKRW(summary.balance.total_krw) : "-"}
          </p>
        </div>

        {/* KRW 잔고 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="text-sm font-medium text-dark-text-secondary">KRW 보유량</h3>
          <p className="mt-2 text-xl sm:text-2xl font-bold text-white tracking-tight courier">
            {summary.balance ? formatKRW(summary.balance.krw) : "-"}
          </p>
        </div>

        {/* 일일 손익 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="text-sm font-medium text-dark-text-secondary">일일 손익</h3>
          <p
            className={`mt-2 text-xl sm:text-2xl font-bold tracking-tight courier text-glow ${Number(summary.daily_pnl) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
          >
            {formatKRW(summary.daily_pnl)}
            <span className="ml-2 text-sm font-medium text-dark-text-muted">
              ({summary.daily_pnl_pct >= 0 ? "+" : ""}
              {summary.daily_pnl_pct.toFixed(2)}%)
            </span>
          </p>
        </div>

        {/* 오늘 거래 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="text-sm font-medium text-dark-text-secondary">오늘의 거래</h3>
          <p className="mt-2 text-xl sm:text-2xl font-bold text-white tracking-tight courier">
            {summary.today_trade_count}
          </p>
        </div>
      </div>

      {/* 포지션 & 최신 신호 */}
      <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
        {/* 현재 포지션 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="mb-6 text-lg font-bold text-white flex items-center gap-2">
            현재 포지션
            <span className="relative group">
              <span className="inline-flex items-center justify-center w-4 h-4 text-xs text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                ?
              </span>
              <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 text-xs font-normal text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                현재 보유 중인 암호화폐 자산 현황
                <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
              </span>
            </span>
          </h3>
          {summary.position && Number(summary.position.quantity) > 0 ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-dark-text-secondary font-medium text-sm">보유량</span>
                <span className="font-bold text-white courier">
                  {Number(summary.position.quantity).toFixed(4)} {summary.position.symbol?.split("-")[1] || "COIN"}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-dark-text-secondary font-medium text-sm">평균 매수가</span>
                <span className="font-bold text-white courier">
                  {formatKRW(summary.position.avg_buy_price)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-dark-text-secondary font-medium text-sm">평가금액</span>
                <span className="font-bold text-white courier">
                  {formatKRW(summary.position.current_value)}
                </span>
              </div>
              <div className="flex justify-between items-center pt-4 border-t border-dark-border">
                <span className="text-dark-text-secondary font-medium">미실현 손익</span>
                <span
                  className={`font-bold courier text-lg ${Number(summary.position.unrealized_pnl) >= 0
                    ? "text-emerald-600"
                    : "text-rose-600"
                    }`}
                >
                  {formatKRW(summary.position.unrealized_pnl)}
                  <span className="ml-2 text-sm font-medium opacity-80">
                    ({summary.position.unrealized_pnl_pct >= 0 ? "+" : ""}
                    {summary.position.unrealized_pnl_pct.toFixed(2)}%)
                  </span>
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-dark-text-muted bg-white/5 rounded-xl border-2 border-dashed border-white/10">
              보유 포지션 없음
            </div>
          )}
        </div>

        {/* 최신 AI 신호 */}
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="mb-6 text-lg font-bold text-white">최신 AI 신호</h3>
          {summary.latest_signal ? (
            <SignalCard signal={summary.latest_signal} />
          ) : (
            <div className="text-center py-12 text-dark-text-muted bg-white/5 rounded-xl border-2 border-dashed border-white/10">
              생성된 신호가 없습니다
            </div>
          )}
        </div>
      </div>

      {/* 현재 설정 요약 */}
      {config && (
        <div className="rounded-2xl glass-panel p-4 sm:p-6">
          <h3 className="mb-4 text-lg font-bold text-white flex items-center gap-2">
            현재 설정
            <span className="text-xs font-normal text-dark-text-muted">
              (설정 페이지에서 수정 가능)
            </span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 포지션 사이징 */}
            <div className="p-4 bg-white/5 rounded-xl border border-white/5">
              <h4 className="text-sm font-semibold text-banana-400 mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                포지션 사이징
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">동적 범위</span>
                  <span className="text-white font-medium courier">
                    {config.position_size_min_pct}% ~ {config.position_size_max_pct}%
                  </span>
                </div>
                <p className="text-xs text-dark-text-muted mt-1">
                  AI 신뢰도에 따라 자동 조절
                </p>
              </div>
            </div>

            {/* 리스크 관리 */}
            <div className="p-4 bg-white/5 rounded-xl border border-white/5">
              <h4 className="text-sm font-semibold text-rose-400 mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                리스크 관리
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">손절</span>
                  <span className="text-white font-medium courier">{config.stop_loss_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">일일 한도</span>
                  <span className="text-white font-medium courier">{config.daily_loss_limit_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">변동성</span>
                  <span className="text-white font-medium courier">{config.volatility_threshold_pct}%</span>
                </div>
              </div>
            </div>

            {/* AI 설정 */}
            <div className="p-4 bg-white/5 rounded-xl border border-white/5">
              <h4 className="text-sm font-semibold text-purple-400 mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI 설정
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">모델</span>
                  <span className="text-white font-medium text-xs">{config.ai_model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-text-muted">신호 주기</span>
                  <span className="text-white font-medium courier">{config.signal_interval_hours}시간</span>
                </div>
              </div>
            </div>

            {/* 하이브리드 전략 */}
            {riskStatus && (
              <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                <h4 className="text-sm font-semibold text-cyan-400 mb-3 flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  하이브리드 전략
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">K값</span>
                    <span className="text-white font-medium courier">{riskStatus.volatility_k_value}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">하이브리드</span>
                    <span className={`font-medium ${riskStatus.hybrid_mode_enabled ? "text-emerald-400" : "text-dark-text-muted"}`}>
                      {riskStatus.hybrid_mode_enabled ? "활성" : "비활성"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">돌파 강도</span>
                    <span className="text-white font-medium courier">{riskStatus.breakout_min_strength}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 마지막 업데이트 시간 */}
      <div className="text-right text-xs text-gray-400">
        마지막 업데이트:{" "}
        {new Intl.DateTimeFormat("ko-KR", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZone: "Asia/Seoul",
        }).format(new Date(summary.updated_at))}{" "}
        KST
      </div>
    </div>
  );
};

export default Dashboard;
