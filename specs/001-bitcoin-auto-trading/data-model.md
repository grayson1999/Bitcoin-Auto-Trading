# Data Model: Bitcoin Auto-Trading System

**Date**: 2026-01-11
**Branch**: `001-bitcoin-auto-trading`

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   MarketData    │       │  TradingSignal  │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ timestamp       │◄──────│ market_data_id  │
│ price           │       │ signal_type     │
│ volume          │       │ confidence      │
│ high_price      │       │ reasoning       │
│ low_price       │       │ created_at      │
│ trade_count     │       │ model_name      │
└─────────────────┘       │ input_tokens    │
                          │ output_tokens   │
                          └────────┬────────┘
                                   │
                                   ▼
┌─────────────────┐       ┌─────────────────┐
│     Order       │       │   RiskEvent     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ signal_id (FK)  │◄──────│ order_id (FK)   │
│ order_type      │       │ event_type      │
│ side            │       │ trigger_value   │
│ amount          │       │ action_taken    │
│ price           │       │ created_at      │
│ status          │       │ notified        │
│ executed_price  │       └─────────────────┘
│ executed_amount │
│ fee             │
│ upbit_uuid      │       ┌─────────────────┐
│ error_message   │       │ BacktestResult  │
│ created_at      │       ├─────────────────┤
│ executed_at     │       │ id (PK)         │
└─────────────────┘       │ start_date      │
                          │ end_date        │
┌─────────────────┐       │ total_return    │
│    Position     │       │ max_drawdown    │
├─────────────────┤       │ win_rate        │
│ id (PK)         │       │ profit_loss_ratio│
│ symbol          │       │ total_trades    │
│ quantity        │       │ created_at      │
│ avg_buy_price   │       │ config_snapshot │
│ current_value   │       └─────────────────┘
│ unrealized_pnl  │
│ updated_at      │       ┌─────────────────┐
└─────────────────┘       │   DailyStats    │
                          ├─────────────────┤
┌─────────────────┐       │ id (PK)         │
│  SystemConfig   │       │ date            │
├─────────────────┤       │ starting_balance│
│ id (PK)         │       │ ending_balance  │
│ key             │       │ realized_pnl    │
│ value           │       │ trade_count     │
│ updated_at      │       │ win_count       │
└─────────────────┘       │ loss_count      │
                          │ is_trading_halted│
                          │ halt_reason     │
                          └─────────────────┘
```

## Entity Definitions

### MarketData (시장 데이터)

실시간 수집되는 비트코인 시장 데이터. 1초 간격 저장, 1년 보존.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| timestamp | DATETIME | NOT NULL, INDEX | 데이터 수집 시간 (UTC) |
| price | DECIMAL(18,8) | NOT NULL | 현재가 (KRW) |
| volume | DECIMAL(18,8) | NOT NULL | 24시간 거래량 |
| high_price | DECIMAL(18,8) | NOT NULL | 24시간 최고가 |
| low_price | DECIMAL(18,8) | NOT NULL | 24시간 최저가 |
| trade_count | INTEGER | NOT NULL | 체결 건수 |

**Indexes**:
- `idx_market_data_timestamp` on (timestamp DESC)
- `idx_market_data_date` on (DATE(timestamp)) - 일별 집계용

**Retention**: 1년 초과 데이터 자동 삭제 (cron job)

---

### TradingSignal (매매 신호)

AI가 생성한 매매 신호. 1시간 주기 생성.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| market_data_id | BIGINT | FK → MarketData | 분석 기준 시장 데이터 |
| signal_type | ENUM | NOT NULL | 'BUY', 'HOLD', 'SELL' |
| confidence | DECIMAL(3,2) | NOT NULL, 0~1 | 신뢰도 점수 |
| reasoning | TEXT | NOT NULL | AI 분석 근거 |
| created_at | DATETIME | NOT NULL | 생성 시간 |
| model_name | VARCHAR(50) | NOT NULL | 사용된 AI 모델명 |
| input_tokens | INTEGER | NOT NULL | 입력 토큰 수 |
| output_tokens | INTEGER | NOT NULL | 출력 토큰 수 |

**Indexes**:
- `idx_signal_created` on (created_at DESC)
- `idx_signal_type_date` on (signal_type, DATE(created_at))

---

### Order (주문)

Upbit에 제출된 매매 주문 기록.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| signal_id | BIGINT | FK → TradingSignal, NULL | 연관 신호 (수동 주문 시 NULL) |
| order_type | ENUM | NOT NULL | 'MARKET', 'LIMIT' |
| side | ENUM | NOT NULL | 'BUY', 'SELL' |
| amount | DECIMAL(18,8) | NOT NULL | 주문 금액/수량 |
| price | DECIMAL(18,8) | NULL | 지정가 (시장가 시 NULL) |
| status | ENUM | NOT NULL | 'PENDING', 'EXECUTED', 'CANCELLED', 'FAILED' |
| executed_price | DECIMAL(18,8) | NULL | 체결 가격 |
| executed_amount | DECIMAL(18,8) | NULL | 체결 금액/수량 |
| fee | DECIMAL(18,8) | NULL | 수수료 |
| upbit_uuid | VARCHAR(100) | UNIQUE, NULL | Upbit 주문 UUID |
| error_message | TEXT | NULL | 실패 시 오류 메시지 |
| created_at | DATETIME | NOT NULL | 주문 생성 시간 |
| executed_at | DATETIME | NULL | 체결 시간 |

**Indexes**:
- `idx_order_status` on (status)
- `idx_order_created` on (created_at DESC)
- `idx_order_upbit_uuid` on (upbit_uuid)

**State Transitions**:
```
PENDING → EXECUTED (체결 완료)
PENDING → CANCELLED (사용자/시스템 취소)
PENDING → FAILED (API 오류, 잔고 부족 등)
```

---

### RiskEvent (리스크 이벤트)

리스크 관리 시스템이 발동한 이벤트 기록.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| order_id | BIGINT | FK → Order, NULL | 연관 주문 |
| event_type | ENUM | NOT NULL | 이벤트 유형 (아래 참조) |
| trigger_value | DECIMAL(10,4) | NOT NULL | 발동 기준값 (%) |
| action_taken | VARCHAR(100) | NOT NULL | 수행된 조치 |
| created_at | DATETIME | NOT NULL | 발생 시간 |
| notified | BOOLEAN | DEFAULT FALSE | 슬랙 알림 전송 여부 |

**Event Types**:
- `STOP_LOSS`: 개별 손절 발동
- `DAILY_LIMIT`: 일일 손실 한도 도달
- `POSITION_LIMIT`: 포지션 크기 초과 거부
- `VOLATILITY_HALT`: 변동성 감지 거래 중단
- `SYSTEM_ERROR`: 시스템 오류 감지

---

### Position (포지션)

현재 보유 포지션 상태. 단일 레코드 (BTC만 거래).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| symbol | VARCHAR(20) | NOT NULL, UNIQUE | 'BTC-KRW' |
| quantity | DECIMAL(18,8) | NOT NULL | 보유 수량 |
| avg_buy_price | DECIMAL(18,8) | NOT NULL | 평균 매수가 |
| current_value | DECIMAL(18,8) | NOT NULL | 현재 평가금액 |
| unrealized_pnl | DECIMAL(18,8) | NOT NULL | 미실현 손익 |
| updated_at | DATETIME | NOT NULL | 최종 업데이트 |

---

### DailyStats (일별 통계)

일별 거래 및 손익 통계. 리스크 관리에 활용.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| date | DATE | NOT NULL, UNIQUE | 거래일 |
| starting_balance | DECIMAL(18,2) | NOT NULL | 시작 잔고 (KRW) |
| ending_balance | DECIMAL(18,2) | NOT NULL | 종료 잔고 (KRW) |
| realized_pnl | DECIMAL(18,2) | NOT NULL | 실현 손익 |
| trade_count | INTEGER | NOT NULL | 거래 횟수 |
| win_count | INTEGER | NOT NULL | 수익 거래 수 |
| loss_count | INTEGER | NOT NULL | 손실 거래 수 |
| is_trading_halted | BOOLEAN | DEFAULT FALSE | 거래 중단 여부 |
| halt_reason | VARCHAR(100) | NULL | 중단 사유 |

---

### BacktestResult (백테스트 결과)

과거 데이터 기반 전략 시뮬레이션 결과.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| start_date | DATE | NOT NULL | 테스트 시작일 |
| end_date | DATE | NOT NULL | 테스트 종료일 |
| total_return | DECIMAL(10,4) | NOT NULL | 총 수익률 (%) |
| max_drawdown | DECIMAL(10,4) | NOT NULL | 최대 낙폭 (%) |
| win_rate | DECIMAL(5,4) | NOT NULL | 승률 (0~1) |
| profit_loss_ratio | DECIMAL(10,4) | NOT NULL | 손익비 |
| total_trades | INTEGER | NOT NULL | 총 거래 횟수 |
| created_at | DATETIME | NOT NULL | 실행 시간 |
| config_snapshot | JSON | NOT NULL | 테스트 시 설정값 |

---

### SystemConfig (시스템 설정)

런타임 설정값 저장.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, AUTO | 고유 식별자 |
| key | VARCHAR(50) | NOT NULL, UNIQUE | 설정 키 |
| value | TEXT | NOT NULL | 설정 값 (JSON) |
| updated_at | DATETIME | NOT NULL | 최종 수정 시간 |

**Default Configurations**:
```json
{
  "position_size_pct": 2.0,
  "stop_loss_pct": 5.0,
  "daily_loss_limit_pct": 5.0,
  "signal_interval_hours": 1,
  "ai_model": "gemini-2.5-flash",
  "volatility_threshold_pct": 3.0
}
```

---

## Validation Rules

### MarketData
- `price` > 0
- `volume` >= 0
- `high_price` >= `price` >= `low_price`

### TradingSignal
- `confidence` BETWEEN 0.0 AND 1.0
- `signal_type` IN ('BUY', 'HOLD', 'SELL')

### Order
- `amount` > 0
- `executed_price` > 0 (when status = 'EXECUTED')
- `upbit_uuid` required when status != 'FAILED'

### DailyStats
- `realized_pnl` = `ending_balance` - `starting_balance` (검증용)
- `trade_count` = `win_count` + `loss_count`

---

## Data Retention Policy

| Entity | Retention | Cleanup Method |
|--------|-----------|----------------|
| MarketData | 1년 | 일별 cron job |
| TradingSignal | 영구 | N/A |
| Order | 영구 | N/A |
| RiskEvent | 영구 | N/A |
| Position | 영구 | N/A |
| DailyStats | 영구 | N/A |
| BacktestResult | 영구 | N/A |
| SystemConfig | 영구 | N/A |
