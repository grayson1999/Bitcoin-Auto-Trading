/**
 * 리스크 상태 컴포넌트 (T081)
 *
 * 현재 리스크 관리 상태를 표시합니다.
 * - 거래 활성화 상태
 * - 일일 손실률
 * - 현재 변동성
 * - 리스크 지표 바
 */

import type { FC } from "react";
import type { RiskStatus as RiskStatusType } from "../hooks/useApi";
import { ExclamationTriangleIcon, ShieldCheckIcon, HandRaisedIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

// === 타입 정의 ===
interface RiskStatusProps {
  /** 리스크 상태 데이터 */
  status: RiskStatusType;
  /** 거래 중단 핸들러 */
  onHalt?: () => void;
  /** 거래 재개 핸들러 */
  onResume?: () => void;
}

// === 상수 ===
const CARD_CLASSES = "rounded-2xl glass-panel p-6";

/**
 * 게이지 색상 결정
 */
function getGaugeColor(value: number, limit: number): string {
  const ratio = Math.abs(value) / limit;
  if (ratio >= 0.8) return "bg-rose-500";
  if (ratio >= 0.5) return "bg-amber-500";
  return "bg-emerald-500";
}

/**
 * RiskStatus 컴포넌트
 */
const RiskStatus: FC<RiskStatusProps> = ({ status, onHalt, onResume }) => {
  const dailyLossRatio = Math.abs(status.daily_loss_pct) / status.daily_loss_limit_pct;
  const volatilityRatio =
    status.current_volatility_pct / status.volatility_threshold_pct;

  const dailyLossColor = getGaugeColor(
    status.daily_loss_pct,
    status.daily_loss_limit_pct
  );
  const volatilityColor = getGaugeColor(
    status.current_volatility_pct,
    status.volatility_threshold_pct
  );

  const isSafe = status.trading_enabled && !status.is_halted;

  return (
    <div className={CARD_CLASSES}>
      {/* 헤더: 거래 상태 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <ShieldCheckIcon className="w-5 h-5 text-banana-400" />
          위험 관리
        </h3>
        <div className={`px-3 py-1 rounded-full flex items-center gap-2 text-sm font-semibold ${isSafe ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
          {isSafe ? (
            <>
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              활성
            </>
          ) : (
            <>
              <HandRaisedIcon className="w-4 h-4" />
              중단됨
            </>
          )}
        </div>
      </div>

      {/* 중단 사유 */}
      {status.is_halted && status.halt_reason && (
        <div className="mb-6 rounded-xl bg-rose-500/10 p-4 border border-rose-500/20">
          <div className="flex gap-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-500 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-rose-400">거래 중단 예외</h4>
              <p className="text-sm text-rose-300/80 mt-1">
                {status.halt_reason}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 지표들 */}
      <div className="space-y-6">
        {/* 일일 손실률 */}
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-dark-text-secondary font-medium">일일 손실</span>
            <span className="font-semibold text-white tabular-nums">
              {status.daily_loss_pct.toFixed(2)}% <span className="text-dark-text-muted font-normal">/ -{status.daily_loss_limit_pct}%</span>
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
            <div
              className={`h-full rounded-full ${dailyLossColor} transition-all duration-500 ease-out shadow-[0_0_10px_rgba(0,0,0,0.5)]`}
              style={{ width: `${Math.min(dailyLossRatio * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 현재 변동성 */}
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-dark-text-secondary font-medium">변동성</span>
            <span className="font-semibold text-white tabular-nums">
              {status.current_volatility_pct.toFixed(2)}% <span className="text-dark-text-muted font-normal">/ {status.volatility_threshold_pct}%</span>
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full ${volatilityColor} transition-all duration-500 ease-out`}
              style={{ width: `${Math.min(volatilityRatio * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 시스템 설정값 요약 */}
        <div className="grid grid-cols-2 gap-4 border-t border-dark-border pt-6">
          <div className="bg-white/5 p-3 rounded-xl text-center border border-white/5">
            <span className="text-xs font-medium text-dark-text-muted uppercase tracking-wider inline-flex items-center gap-1">
              포지션 크기
              <span className="relative group">
                <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[10px] text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                  ?
                </span>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 text-xs font-normal normal-case text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                  1회 주문 시 사용할 총 자산의 비율
                  <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
                </span>
              </span>
            </span>
            <p className="mt-1 text-lg font-bold text-white">
              {status.position_size_pct}%
            </p>
          </div>
          <div className="bg-white/5 p-3 rounded-xl text-center border border-white/5">
            <span className="text-xs font-medium text-dark-text-muted uppercase tracking-wider inline-flex items-center gap-1">
              손절매
              <span className="relative group">
                <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[10px] text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                  ?
                </span>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 text-xs font-normal normal-case text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                  시스템 레벨 강제 청산 임계값
                  <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
                </span>
              </span>
            </span>
            <p className="mt-1 text-lg font-bold text-rose-400">
              {status.stop_loss_pct}%
            </p>
          </div>
        </div>

        {/* AI 신호 설정 */}
        <div className="border-t border-dark-border pt-6">
          <h4 className="text-xs font-medium text-dark-text-muted uppercase tracking-wider mb-3 flex items-center gap-1">
            AI 신호 설정
            <span className="relative group">
              <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[10px] text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                ?
              </span>
              <span className="absolute left-0 bottom-full mb-2 px-3 py-2 text-xs font-normal normal-case text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                AI가 매매 신호를 생성할 때 사용하는 기준값
                <span className="absolute left-3 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
              </span>
            </span>
          </h4>
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-white/5 p-2 rounded-lg text-center border border-white/5">
              <span className="text-[10px] font-medium text-dark-text-muted uppercase">손절</span>
              <p className="mt-0.5 text-sm font-bold text-rose-400">
                {status.signal_stop_loss_pct}%
              </p>
            </div>
            <div className="bg-white/5 p-2 rounded-lg text-center border border-white/5">
              <span className="text-[10px] font-medium text-dark-text-muted uppercase">익절</span>
              <p className="mt-0.5 text-sm font-bold text-emerald-400">
                {status.signal_take_profit_pct}%
              </p>
            </div>
            <div className="bg-white/5 p-2 rounded-lg text-center border border-white/5">
              <span className="text-[10px] font-medium text-dark-text-muted uppercase">트레일</span>
              <p className="mt-0.5 text-sm font-bold text-banana-400">
                {status.signal_trailing_stop_pct}%
              </p>
            </div>
            <div className="bg-white/5 p-2 rounded-lg text-center border border-white/5">
              <span className="text-[10px] font-medium text-dark-text-muted uppercase">본전</span>
              <p className="mt-0.5 text-sm font-bold text-sky-400">
                {status.signal_breakeven_pct}%
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* 액션 버튼 */}
      {(onHalt || onResume) && (
        <div className="mt-8">
          {status.trading_enabled && !status.is_halted ? (
            onHalt && (
              <button
                onClick={onHalt}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-white border border-rose-200 px-4 py-3 text-sm font-semibold text-rose-600 shadow-sm hover:bg-rose-50 hover:border-rose-300 transition-all focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2"
              >
                <HandRaisedIcon className="w-4 h-4" />
                긴급 중단
              </button>
            )
          ) : (
            onResume && (
              <button
                onClick={onResume}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-900/20 hover:bg-emerald-500 hover:shadow-emerald-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
              >
                <ArrowPathIcon className="w-4 h-4" />
                거래 재개
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default RiskStatus;
