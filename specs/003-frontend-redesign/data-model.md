# Data Model: Frontend Redesign

**Date**: 2026-01-24
**Feature**: Frontend Redesign - Bitcoin Auto Trading Dashboard

## Overview

This document defines the TypeScript types/interfaces used in the frontend application. Types are organized by domain and mirror the backend API response structures.

---

## 1. Common Types

### Base Types
```typescript
// ISO 8601 timestamp string
type ISOTimestamp = string;

// API Response wrapper
interface ApiResponse<T> {
  data: T;
  status: number;
}

// Pagination
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
}
```

### Enums
```typescript
// Order status
enum OrderStatus {
  PENDING = 'pending',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
  FAILED = 'failed',
}

// Order side
enum OrderSide {
  BUY = 'BUY',
  SELL = 'SELL',
}

// Signal type
enum SignalType {
  BUY = 'BUY',
  SELL = 'SELL',
  HOLD = 'HOLD',
}

// User role
enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
}

// Chart interval
type ChartInterval = '1m' | '5m' | '15m' | '1h';
```

---

## 2. Market Domain

### MarketData
Current market price information from Upbit API.

```typescript
interface MarketData {
  market: string;           // "KRW-BTC"
  price: number;            // Current price in KRW
  volume_24h: number;       // 24h trading volume
  high_24h: number;         // 24h high price
  low_24h: number;          // 24h low price
  timestamp: ISOTimestamp;  // Data timestamp
  change_24h_pct: number;   // 24h price change percentage
}
```

### OHLCV (Candlestick Data)
Historical price data for chart rendering.

```typescript
interface OHLCVData {
  time: number | string;    // Unix timestamp or ISO string
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface MarketHistoryResponse {
  items: OHLCVData[];
  total: number;
}
```

### MarketSummary
Aggregated market statistics.

```typescript
interface MarketSummary {
  high: number;
  low: number;
  change_pct: number;
  avg_price: number;
  volume: number;
}
```

---

## 3. Trading Domain

### Position
Current holding position information.

```typescript
interface Position {
  symbol: string;               // "KRW-BTC"
  quantity: number;             // Amount of BTC held
  avg_buy_price: number;        // Average purchase price
  current_value: number;        // Current value in KRW
  unrealized_pnl: number;       // Unrealized profit/loss in KRW
  unrealized_pnl_pct: number;   // Unrealized P&L percentage
  updated_at: ISOTimestamp;
}

// Empty position representation
interface EmptyPosition {
  symbol: string;
  quantity: 0;
  avg_buy_price: 0;
  current_value: 0;
  unrealized_pnl: 0;
  unrealized_pnl_pct: 0;
}
```

### Balance
Account balance information.

```typescript
interface Balance {
  krw: number;              // Available KRW
  krw_locked: number;       // Locked KRW (in pending orders)
  coin: number;             // BTC balance
  coin_locked: number;      // Locked BTC (in pending orders)
  coin_avg_buy_price: number; // Average buy price for BTC
  total_krw: number;        // Total value in KRW
}
```

### Order
Trading order record.

```typescript
interface Order {
  id: string;                   // Order UUID
  symbol: string;               // "KRW-BTC"
  side: OrderSide;              // BUY or SELL
  quantity: number;             // Order quantity
  price: number;                // Order price
  status: OrderStatus;          // Order status
  created_at: ISOTimestamp;     // Order creation time
  executed_at?: ISOTimestamp;   // Execution time (if executed)
}

interface OrderListResponse extends PaginatedResponse<Order> {}
```

---

## 4. Signal Domain

### TradingSignal
AI-generated trading signal.

```typescript
interface TradingSignal {
  id: string;                   // Signal UUID
  signal_type: SignalType;      // BUY, SELL, or HOLD
  confidence: number;           // Confidence score (0-100)
  rationale: string;            // Analysis reasoning (Korean)
  created_at: ISOTimestamp;     // Signal generation time
}

interface TradingSignalListResponse extends PaginatedResponse<TradingSignal> {}

// Signal detail (for modal)
interface TradingSignalDetail extends TradingSignal {
  technical_snapshot?: {
    price: number;
    rsi?: number;
    macd?: {
      line: number;
      signal: number;
      histogram: number;
    };
    ma_20?: number;
    ma_50?: number;
  };
}
```

---

## 5. Dashboard Domain

### DashboardSummary
Aggregated dashboard data.

```typescript
interface DashboardSummary {
  market: string;                       // "KRW-BTC"
  current_price: number;                // Current BTC price
  price_change_24h: number;             // 24h price change percentage
  position: Position | null;            // Current position (null if none)
  balance: Balance | null;              // Account balance
  daily_pnl: number;                    // Today's realized P&L
  daily_pnl_pct: number;                // Today's P&L percentage
  latest_signal: TradingSignal | null;  // Most recent AI signal
  is_trading_active: boolean;           // Trading enabled status
  today_trade_count: number;            // Number of trades today
  updated_at: ISOTimestamp;
}
```

---

## 6. Portfolio Domain

### PortfolioSummary
Investment performance summary.

```typescript
interface PortfolioSummary {
  total_deposit: number;            // Total deposited amount (KRW)
  current_value: number;            // Current total value (KRW)
  cumulative_return_pct: number;    // Cumulative return percentage
  today_return_pct: number;         // Today's return percentage
  today_realized_pnl: number;       // Today's realized P&L (KRW)
  total_trades: number;             // Total number of trades
  win_count: number;                // Number of winning trades
  win_rate: number;                 // Win rate percentage
  average_return_pct: number;       // Average return per trade
  max_drawdown_pct: number;         // Maximum drawdown percentage (MDD)
  profit_chart_data: ProfitDataPoint[];
}

interface ProfitDataPoint {
  date: string;       // "YYYY-MM-DD"
  value: number;      // Portfolio value at date
}
```

### DepositHistory
Deposit tracking for accurate return calculation.

```typescript
interface Deposit {
  id: number;
  amount: number;               // Deposit amount (KRW)
  deposited_at: ISOTimestamp;   // Deposit timestamp
}

interface DepositHistoryResponse {
  deposits: Deposit[];
  total: number;                // Total deposited amount
}
```

---

## 7. Config Domain

### SystemConfig
System configuration key-value pair.

```typescript
interface SystemConfig {
  key: string;
  value: string | number | boolean;
  source: 'db' | 'env';         // Config source
  updated_at?: ISOTimestamp;
}

interface ConfigListResponse {
  configs: SystemConfig[];
  count: number;
}

// Known config keys for type safety
type ConfigKey =
  | 'POSITION_SIZE_MIN_PCT'
  | 'POSITION_SIZE_MAX_PCT'
  | 'STOP_LOSS_PCT'
  | 'DAILY_LOSS_LIMIT_PCT'
  | 'AI_MODEL'
  | 'SIGNAL_INTERVAL_HOURS';
```

---

## 8. Risk Domain

### RiskStatus
Current risk management status.

```typescript
interface RiskStatus {
  trading_enabled: boolean;
  daily_loss_pct: number;
  daily_loss_limit_pct: number;
  position_size_pct: number;
  stop_loss_pct: number;
  volatility_threshold_pct: number;
  current_volatility_pct: number;
  is_halted: boolean;
  halt_reason: string | null;
  last_check_at: ISOTimestamp;
  // Additional params
  signal_stop_loss_pct: number;
  signal_take_profit_pct: number;
  signal_trailing_stop_pct: number;
  signal_breakeven_pct: number;
  volatility_k_value: number;
  hybrid_mode_enabled: boolean;
  breakout_min_strength: number;
}

interface RiskEvent {
  id: string;
  event_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  created_at: ISOTimestamp;
}
```

---

## 9. Admin Domain

### SystemMetrics
Server resource usage metrics.

```typescript
interface SystemMetrics {
  cpu_percent: number;          // CPU usage percentage
  memory_percent: number;       // Memory usage percentage
  memory_used_mb: number;       // Memory used in MB
  memory_total_mb: number;      // Total memory in MB
  disk_percent: number;         // Disk usage percentage
  disk_used_gb: number;         // Disk used in GB
  disk_total_gb: number;        // Total disk in GB
  scheduler_jobs: SchedulerJob[];
}

interface SchedulerJob {
  name: string;                 // Job identifier
  status: 'running' | 'stopped' | 'error';
  last_run: ISOTimestamp | null;
  next_run: ISOTimestamp | null;
}
```

### HealthDetail
Detailed system health status.

```typescript
interface HealthDetail {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: ISOTimestamp;
  version: string;
  components: {
    database: ComponentHealth;
    upbit_api: ComponentHealth;
    gemini_api: ComponentHealth;
    scheduler: ComponentHealth;
    recent_signal: ComponentHealth;
    recent_order: ComponentHealth;
  };
}

interface ComponentHealth {
  status: 'healthy' | 'unhealthy';
  latency_ms?: number;
  message?: string;
}
```

---

## 10. Auth Domain

### User
Authenticated user information.

```typescript
interface User {
  id: string;                   // User UUID
  email: string;
  name: string;
  role: UserRole;               // 'user' | 'admin'
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;           // Token expiry in seconds
}

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

---

## 11. UI State Types

### Loading/Error States
```typescript
interface LoadingState {
  isLoading: boolean;
  isError: boolean;
  error: ApiError | null;
}

interface ApiError {
  status: number;
  message: string;
  retryable: boolean;
}
```

### Chart Settings
```typescript
interface ChartSettings {
  interval: ChartInterval;
  showMA20: boolean;
  showMA50: boolean;
  showMA200: boolean;
  showRSI: boolean;
  showMACD: boolean;
}
```

### Filter States
```typescript
interface OrderFilter {
  status: OrderStatus | 'all';
  page: number;
  limit: number;
}

interface SignalFilter {
  type: SignalType | 'all';
  page: number;
  limit: number;
}
```

---

## Entity Relationships

```
User
 └── owns → Balance
 └── owns → Position
 └── has many → Order
 └── can view → TradingSignal
 └── can configure → SystemConfig

TradingSignal
 └── may trigger → Order (BUY/SELL)

Order
 └── updates → Position (when executed)
 └── updates → Balance (when executed)

DashboardSummary
 └── aggregates → MarketData
 └── aggregates → Position
 └── aggregates → Balance
 └── shows latest → TradingSignal

PortfolioSummary
 └── derives from → DepositHistory
 └── derives from → Balance
 └── calculates from → Order history
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| `confidence` | 0-100 |
| `quantity` | > 0 |
| `price` | > 0 |
| `percentage fields` | Can be negative (for losses) |
| `timestamps` | ISO 8601 format |
| `email` | Valid email format |

---

## State Transitions

### Order Status Flow
```
PENDING → EXECUTED (success)
PENDING → CANCELLED (user cancel)
PENDING → FAILED (error)
```

### Signal Type Flow
```
HOLD (default) → BUY (bullish signal)
HOLD (default) → SELL (bearish signal)
BUY/SELL → HOLD (neutral market)
```
