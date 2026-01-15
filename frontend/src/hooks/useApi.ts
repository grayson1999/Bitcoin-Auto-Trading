/**
 * API 데이터 페칭 훅 모듈
 *
 * React Query를 사용한 데이터 페칭 및 상태 관리를 제공합니다.
 * - 대시보드 요약 조회
 * - AI 신호 조회
 * - 주문 내역 조회
 * - 설정 조회/수정
 * - 리스크 상태 조회
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

// === API 응답 타입 정의 ===

/** 잔고 정보 */
export interface Balance {
  krw: string;
  krw_locked: string;
  xrp: string;
  xrp_locked: string;
  xrp_avg_buy_price: string;
  total_krw: string;
}

/** 포지션 정보 */
export interface Position {
  symbol: string;
  quantity: string;
  avg_buy_price: string;
  current_value: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: number;
  updated_at: string;
}

/** AI 신호 */
export interface TradingSignal {
  id: number;
  signal_type: "BUY" | "HOLD" | "SELL";
  confidence: string;
  reasoning: string;
  created_at: string;
  model_name: string;
  input_tokens: number;
  output_tokens: number;
}

/** 대시보드 요약 */
export interface DashboardSummary {
  current_price: string;
  price_change_24h: number | null;
  position: Position | null;
  balance: Balance | null;
  daily_pnl: string;
  daily_pnl_pct: number;
  latest_signal: TradingSignal | null;
  is_trading_active: boolean;
  today_trade_count: number;
  updated_at: string;
}

/** 주문 */
export interface Order {
  id: number;
  signal_id: number | null;
  order_type: "MARKET" | "LIMIT";
  side: "BUY" | "SELL";
  market: string;
  amount: string;
  price: string | null;
  status: "PENDING" | "EXECUTED" | "CANCELLED" | "FAILED";
  executed_price: string | null;
  executed_amount: string | null;
  fee: string | null;
  upbit_uuid: string | null;
  error_message: string | null;
  created_at: string;
  executed_at: string | null;
}

/** 주문 목록 응답 */
export interface OrderListResponse {
  items: Order[];
  total: number;
  limit: number;
  offset: number;
}

/** AI 신호 목록 응답 */
export interface SignalListResponse {
  items: TradingSignal[];
  total: number;
}

/** 시스템 설정 */
export interface SystemConfig {
  position_size_pct: number;
  stop_loss_pct: number;
  daily_loss_limit_pct: number;
  signal_interval_hours: number;
  ai_model: string;
  volatility_threshold_pct: number;
  trading_enabled: boolean;
}

/** 설정 수정 요청 */
export interface SystemConfigUpdate {
  position_size_pct?: number;
  stop_loss_pct?: number;
  daily_loss_limit_pct?: number;
  signal_interval_hours?: number;
  ai_model?: string;
  volatility_threshold_pct?: number;
}

/** 리스크 상태 */
export interface RiskStatus {
  trading_enabled: boolean;
  daily_loss_pct: number;
  daily_loss_limit_pct: number;
  position_size_pct: number;
  stop_loss_pct: number;
  volatility_threshold_pct: number;
  current_volatility_pct: number;
  is_halted: boolean;
  halt_reason: string | null;
  last_check_at: string;
}

// === 쿼리 키 상수 ===
export const QUERY_KEYS = {
  DASHBOARD_SUMMARY: "dashboard-summary",
  SIGNALS: "signals",
  ORDERS: "orders",
  CONFIG: "config",
  RISK_STATUS: "risk-status",
} as const;

// === 훅 정의 ===

/**
 * 대시보드 요약 조회 훅
 *
 * @param refetchInterval 자동 새로고침 주기 (ms), 0이면 비활성화
 * @returns UseQueryResult<DashboardSummary>
 */
export function useDashboardSummary(refetchInterval = 0) {
  return useQuery<DashboardSummary>({
    queryKey: [QUERY_KEYS.DASHBOARD_SUMMARY],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
    refetchInterval: refetchInterval > 0 ? refetchInterval : false,
    staleTime: 5000, // 5초
  });
}

/**
 * AI 신호 목록 조회 훅
 *
 * @param limit 조회 개수
 * @param signalType 신호 타입 필터
 * @returns UseQueryResult<SignalListResponse>
 */
export function useSignals(limit = 50, signalType?: string) {
  const params = new URLSearchParams();
  params.append("limit", String(limit));
  if (signalType && signalType !== "all") {
    params.append("signal_type", signalType);
  }

  return useQuery<SignalListResponse>({
    queryKey: [QUERY_KEYS.SIGNALS, limit, signalType],
    queryFn: () => api.get<SignalListResponse>(`/signals?${params.toString()}`),
    staleTime: 30000, // 30초
  });
}

/**
 * 신호 수동 생성 훅
 *
 * @returns UseMutationResult
 */
export function useGenerateSignal() {
  const queryClient = useQueryClient();

  return useMutation<TradingSignal, Error>({
    mutationFn: () => api.post<TradingSignal>("/signals/generate"),
    onSuccess: () => {
      // 신호 목록 및 대시보드 갱신
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SIGNALS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD_SUMMARY] });
    },
  });
}

/**
 * 주문 목록 조회 훅
 *
 * @param status 상태 필터
 * @param limit 조회 개수
 * @param offset 시작 위치
 * @returns UseQueryResult<OrderListResponse>
 */
export function useOrders(status = "all", limit = 50, offset = 0) {
  const params = new URLSearchParams();
  params.append("status", status);
  params.append("limit", String(limit));
  params.append("offset", String(offset));

  return useQuery<OrderListResponse>({
    queryKey: [QUERY_KEYS.ORDERS, status, limit, offset],
    queryFn: () =>
      api.get<OrderListResponse>(`/trading/orders?${params.toString()}`),
    staleTime: 10000, // 10초
  });
}

/**
 * 시스템 설정 조회 훅
 *
 * @returns UseQueryResult<SystemConfig>
 */
export function useConfig() {
  return useQuery<SystemConfig>({
    queryKey: [QUERY_KEYS.CONFIG],
    queryFn: () => api.get<SystemConfig>("/config"),
    staleTime: 60000, // 1분
  });
}

/**
 * 시스템 설정 수정 훅
 *
 * @returns UseMutationResult
 */
export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation<SystemConfig, Error, SystemConfigUpdate>({
    mutationFn: (data) => api.patch<SystemConfig>("/config", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CONFIG] });
    },
  });
}

/**
 * 리스크 상태 조회 훅
 *
 * @returns UseQueryResult<RiskStatus>
 */
export function useRiskStatus() {
  return useQuery<RiskStatus>({
    queryKey: [QUERY_KEYS.RISK_STATUS],
    queryFn: () => api.get<RiskStatus>("/risk/status"),
    staleTime: 10000, // 10초
  });
}

/**
 * 거래 중단 훅
 */
export function useHaltTrading() {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error, { reason: string }>({
    mutationFn: (data) => api.post("/risk/halt", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.RISK_STATUS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD_SUMMARY] });
    },
  });
}

/**
 * 거래 재개 훅
 */
export function useResumeTrading() {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error>({
    mutationFn: () => api.post("/risk/resume"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.RISK_STATUS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD_SUMMARY] });
    },
  });
}
