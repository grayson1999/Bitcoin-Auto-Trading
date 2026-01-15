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
const CARD_CLASSES = "rounded-lg bg-white p-6 shadow";

/**
 * 게이지 색상 결정
 */
function getGaugeColor(value: number, limit: number): string {
  const ratio = Math.abs(value) / limit;
  if (ratio >= 0.8) return "bg-red-500";
  if (ratio >= 0.5) return "bg-yellow-500";
  return "bg-green-500";
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

  return (
    <div className={CARD_CLASSES}>
      {/* 헤더: 거래 상태 */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">리스크 상태</h3>
        <div className="flex items-center gap-2">
          {status.trading_enabled && !status.is_halted ? (
            <>
              <span className="inline-flex h-3 w-3 rounded-full bg-green-500"></span>
              <span className="text-sm font-medium text-green-600">거래 활성</span>
            </>
          ) : (
            <>
              <span className="inline-flex h-3 w-3 rounded-full bg-red-500"></span>
              <span className="text-sm font-medium text-red-600">거래 중단</span>
            </>
          )}
        </div>
      </div>

      {/* 중단 사유 */}
      {status.is_halted && status.halt_reason && (
        <div className="mt-3 rounded-md bg-red-50 p-3">
          <p className="text-sm text-red-700">
            <strong>중단 사유:</strong> {status.halt_reason}
          </p>
        </div>
      )}

      {/* 지표들 */}
      <div className="mt-6 space-y-4">
        {/* 일일 손실률 */}
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">일일 손실</span>
            <span className="font-medium text-gray-900">
              {status.daily_loss_pct.toFixed(2)}% / -{status.daily_loss_limit_pct}%
            </span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className={`h-full rounded-full ${dailyLossColor} transition-all duration-500`}
              style={{ width: `${Math.min(dailyLossRatio * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 현재 변동성 */}
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">변동성</span>
            <span className="font-medium text-gray-900">
              {status.current_volatility_pct.toFixed(2)}% /{" "}
              {status.volatility_threshold_pct}%
            </span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className={`h-full rounded-full ${volatilityColor} transition-all duration-500`}
              style={{ width: `${Math.min(volatilityRatio * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 설정값 요약 */}
        <div className="grid grid-cols-2 gap-4 border-t pt-4">
          <div>
            <span className="text-xs text-gray-500">포지션 크기</span>
            <p className="font-medium text-gray-900">
              {status.position_size_pct}%
            </p>
          </div>
          <div>
            <span className="text-xs text-gray-500">손절 임계값</span>
            <p className="font-medium text-gray-900">{status.stop_loss_pct}%</p>
          </div>
        </div>
      </div>

      {/* 액션 버튼 */}
      {(onHalt || onResume) && (
        <div className="mt-6 flex gap-2">
          {status.trading_enabled && !status.is_halted ? (
            onHalt && (
              <button
                onClick={onHalt}
                className="w-full rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                거래 중단
              </button>
            )
          ) : (
            onResume && (
              <button
                onClick={onResume}
                className="w-full rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              >
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
