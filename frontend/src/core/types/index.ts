// ============================================================================
// Common Types
// ============================================================================

/** ISO 8601 timestamp string */
export type ISOTimestamp = string

/** API Response wrapper */
export interface ApiResponse<T> {
  data: T
  status: number
}

/** Pagination response */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page?: number
  limit?: number
}

// ============================================================================
// Enums
// ============================================================================

/** Order status */
export const OrderStatus = {
  PENDING: 'pending',
  EXECUTED: 'executed',
  CANCELLED: 'cancelled',
  FAILED: 'failed',
} as const
export type OrderStatus = (typeof OrderStatus)[keyof typeof OrderStatus]

/** Order side */
export const OrderSide = {
  BUY: 'BUY',
  SELL: 'SELL',
} as const
export type OrderSide = (typeof OrderSide)[keyof typeof OrderSide]

/** Signal type */
export const SignalType = {
  BUY: 'BUY',
  SELL: 'SELL',
  HOLD: 'HOLD',
} as const
export type SignalType = (typeof SignalType)[keyof typeof SignalType]

/** User role */
export const UserRole = {
  USER: 'user',
  ADMIN: 'admin',
} as const
export type UserRole = (typeof UserRole)[keyof typeof UserRole]

/** Chart interval */
export type ChartInterval = '1m' | '5m' | '15m' | '1h'

// ============================================================================
// Market Domain
// ============================================================================

/** Current market price information */
export interface MarketData {
  market: string
  price: number
  volume_24h: number
  high_24h: number
  low_24h: number
  timestamp: ISOTimestamp
  change_24h_pct: number
}

/** OHLCV candlestick data */
export interface OHLCVData {
  time: number | string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

/** Market history response */
export interface MarketHistoryResponse {
  items: OHLCVData[]
  total: number
}

/** Market summary statistics */
export interface MarketSummary {
  high: number
  low: number
  change_pct: number
  avg_price: number
  volume: number
}

// ============================================================================
// Trading Domain
// ============================================================================

/** Current holding position */
export interface Position {
  symbol: string
  quantity: number
  avg_buy_price: number
  current_value: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  updated_at: ISOTimestamp
}

/** Account balance */
export interface Balance {
  krw: number
  krw_locked: number
  coin: number
  coin_locked: number
  coin_avg_buy_price: number
  total_krw: number
}

/** Trading order */
export interface Order {
  id: string
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  status: OrderStatus
  created_at: ISOTimestamp
  executed_at?: ISOTimestamp
}

export interface OrderListResponse extends PaginatedResponse<Order> {}

// ============================================================================
// Signal Domain
// ============================================================================

/** AI trading signal (matches backend TradingSignalResponse) */
export interface TradingSignal {
  id: number
  signal_type: SignalType
  confidence: number // 0~1 range (multiply by 100 for percentage display)
  reasoning: string // AI analysis rationale
  created_at: ISOTimestamp
  model_name: string
  input_tokens: number
  output_tokens: number
  price_at_signal: number | null
  price_after_4h: number | null
  price_after_24h: number | null
  outcome_evaluated: boolean
  outcome_correct: boolean | null
  technical_snapshot: Record<string, unknown> | null
}

export interface TradingSignalListResponse extends PaginatedResponse<TradingSignal> {}

/** Signal detail - same as TradingSignal (backend includes all fields) */
export type TradingSignalDetail = TradingSignal

// ============================================================================
// Dashboard Domain
// ============================================================================

/** Dashboard aggregated data */
export interface DashboardSummary {
  market: string
  current_price: number
  price_change_24h: number
  position: Position | null
  balance: Balance | null
  daily_pnl: number
  daily_pnl_pct: number
  latest_signal: TradingSignal | null
  is_trading_active: boolean
  today_trade_count: number
  updated_at: ISOTimestamp
}

// ============================================================================
// Portfolio Domain
// ============================================================================

/** Profit chart data point */
export interface ProfitDataPoint {
  date: string
  value: number
}

/** Portfolio summary */
export interface PortfolioSummary {
  total_deposit: number
  current_value: number
  cumulative_return_pct: number
  today_return_pct: number
  today_realized_pnl: number
  total_trades: number
  win_count: number
  win_rate: number
  average_return_pct: number
  max_drawdown_pct: number
  profit_chart_data: ProfitDataPoint[]
}

/** Deposit record */
export interface Deposit {
  id: number
  amount: number
  deposited_at: ISOTimestamp
}

/** Deposit history response */
export interface DepositHistoryResponse {
  deposits: Deposit[]
  total: number
}

// ============================================================================
// Config Domain
// ============================================================================

/** System configuration */
export interface SystemConfig {
  key: string
  value: string | number | boolean
  source: 'db' | 'env'
  updated_at?: ISOTimestamp
}

/** Config list response */
export interface ConfigListResponse {
  configs: SystemConfig[]
  count: number
}

/** Known config keys */
export type ConfigKey =
  | 'POSITION_SIZE_MIN_PCT'
  | 'POSITION_SIZE_MAX_PCT'
  | 'STOP_LOSS_PCT'
  | 'DAILY_LOSS_LIMIT_PCT'
  | 'AI_MODEL'
  | 'SIGNAL_INTERVAL_HOURS'

// ============================================================================
// Risk Domain
// ============================================================================

/** Risk management status */
export interface RiskStatus {
  trading_enabled: boolean
  daily_loss_pct: number
  daily_loss_limit_pct: number
  position_size_pct: number
  stop_loss_pct: number
  volatility_threshold_pct: number
  current_volatility_pct: number
  is_halted: boolean
  halt_reason: string | null
  last_check_at: ISOTimestamp
  signal_stop_loss_pct: number
  signal_take_profit_pct: number
  signal_trailing_stop_pct: number
  signal_breakeven_pct: number
  volatility_k_value: number
  hybrid_mode_enabled: boolean
  breakout_min_strength: number
}

/** Risk event */
export interface RiskEvent {
  id: string
  event_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  created_at: ISOTimestamp
}

// ============================================================================
// Admin Domain
// ============================================================================

/** Scheduler job status */
export interface SchedulerJob {
  name: string
  status: 'running' | 'stopped' | 'error'
  last_run: ISOTimestamp | null
  next_run: ISOTimestamp | null
}

/** System metrics */
export interface SystemMetrics {
  cpu_percent: number
  memory_percent: number
  memory_used_mb: number
  memory_total_mb: number
  disk_percent: number
  disk_used_gb: number
  disk_total_gb: number
  scheduler_jobs: SchedulerJob[]
}

/** Component health status */
export interface ComponentHealth {
  status: 'healthy' | 'unhealthy'
  latency_ms?: number
  message?: string
}

/** Detailed system health */
export interface HealthDetail {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: ISOTimestamp
  version: string
  components: {
    database: ComponentHealth
    upbit_api: ComponentHealth
    gemini_api: ComponentHealth
    scheduler: ComponentHealth
    recent_signal: ComponentHealth
    recent_order: ComponentHealth
  }
}

// ============================================================================
// Auth Domain
// ============================================================================

/** User information */
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
}

/** Auth tokens */
export interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

/** Auth state */
export interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
}

// ============================================================================
// UI State Types
// ============================================================================

/** Loading/Error state */
export interface LoadingState {
  isLoading: boolean
  isError: boolean
  error: ApiErrorType | null
}

/** API Error type */
export interface ApiErrorType {
  status: number
  message: string
  retryable: boolean
}

/** Chart settings */
export interface ChartSettings {
  interval: ChartInterval
  showMA20: boolean
  showMA50: boolean
  showMA200: boolean
  showRSI: boolean
  showMACD: boolean
}

/** Order filter */
export interface OrderFilter {
  status: OrderStatus | 'all'
  page: number
  limit: number
}

/** Signal filter */
export interface SignalFilter {
  type: SignalType | 'all'
  page: number
  limit: number
}
