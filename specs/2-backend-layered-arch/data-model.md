# Data Model: Backend Layered Architecture

**Date**: 2026-01-21
**Feature**: [spec.md](./spec.md)

## Overview

기존 DB 테이블 구조는 변경 없이 유지. ORM 모델 파일을 `models/` → `entities/`로 이동하고, 파일명을 DB 테이블명 기준으로 통일.

## Entities (ORM Models)

### 기존 → 신규 매핑

| DB 테이블 | 기존 파일 | 신규 파일 |
|----------|----------|----------|
| `market_data` | `models/market_data.py` | `entities/market_data.py` |
| `trading_signals` | `models/trading_signal.py` | `entities/trading_signal.py` |
| `orders` | `models/order.py` | `entities/order.py` |
| `positions` | `models/position.py` | `entities/position.py` |
| `daily_stats` | `models/daily_stats.py` | `entities/daily_stats.py` |
| `risk_events` | `models/risk_event.py` | `entities/risk_event.py` |
| `backtest_results` | `models/backtest_result.py` | `entities/backtest_result.py` |
| `system_configs` | `models/system_config.py` | `entities/system_config.py` |

### Entity 구조

```
entities/
├── __init__.py              # 모든 Entity export
├── base.py                  # Base, TimestampMixin
├── market_data.py           # MarketData
├── trading_signal.py        # TradingSignal, SignalType
├── order.py                 # Order, OrderType, OrderSide, OrderStatus
├── position.py              # Position
├── daily_stats.py           # DailyStats
├── risk_event.py            # RiskEvent, RiskEventType
├── backtest_result.py       # BacktestResult, BacktestStatus
└── system_config.py         # SystemConfig
```

### entities/__init__.py
```python
from entities.base import Base, TimestampMixin
from entities.market_data import MarketData
from entities.trading_signal import TradingSignal, SignalType
from entities.order import Order, OrderType, OrderSide, OrderStatus
from entities.position import Position
from entities.daily_stats import DailyStats
from entities.risk_event import RiskEvent, RiskEventType
from entities.backtest_result import BacktestResult, BacktestStatus
from entities.system_config import SystemConfig

__all__ = [
    "Base", "TimestampMixin",
    "MarketData",
    "TradingSignal", "SignalType",
    "Order", "OrderType", "OrderSide", "OrderStatus",
    "Position",
    "DailyStats",
    "RiskEvent", "RiskEventType",
    "BacktestResult", "BacktestStatus",
    "SystemConfig",
]
```

---

## Repositories

### Repository 구조

```
repositories/
├── __init__.py              # 모든 Repository export
├── base.py                  # BaseRepository[T]
├── market_repository.py     # MarketRepository
├── signal_repository.py     # SignalRepository
├── order_repository.py      # OrderRepository
├── position_repository.py   # PositionRepository
└── config_repository.py     # ConfigRepository
```

### BaseRepository 인터페이스

| 메서드 | 반환 타입 | 설명 |
|--------|----------|------|
| `get_by_id(id)` | `T \| None` | ID로 조회 |
| `get_all(limit)` | `list[T]` | 전체 조회 (limit 적용) |
| `create(**kwargs)` | `T` | 생성 |
| `update(id, **kwargs)` | `T \| None` | 수정 |
| `delete(id)` | `bool` | 삭제 |

### 도메인별 Repository 특수 메서드

| Repository | 특수 메서드 |
|------------|-----------|
| `MarketRepository` | `get_latest()`, `get_history(hours)`, `get_ohlcv(ticker, interval)` |
| `SignalRepository` | `get_latest()`, `get_by_date_range(start, end)`, `get_by_ticker(ticker)` |
| `OrderRepository` | `get_pending()`, `get_by_status(status)`, `update_status(id, status)` |
| `PositionRepository` | `get_open()`, `get_by_ticker(ticker)`, `close_position(id)` |
| `ConfigRepository` | `get_value(key)`, `set_value(key, value)`, `get_all_configs()` |

---

## Module Schemas

각 모듈의 schemas.py는 기존 api/schemas/에서 이동하여 도메인별로 정리.

### 기존 → 신규 매핑

| 기존 파일 | 신규 파일 |
|----------|----------|
| `api/schemas/market.py` | `modules/market/schemas.py` |
| `api/schemas/signal.py` | `modules/signal/schemas.py` |
| `api/schemas/order.py` | `modules/trading/schemas.py` |
| `api/schemas/risk.py` | `modules/risk/schemas.py` |
| `api/schemas/backtest.py` | `modules/backtest/schemas.py` |
| `api/schemas/config.py` | `modules/config/schemas.py` |
| `api/schemas/dashboard.py` | `modules/market/schemas.py` (통합) |

---

## Config 설정 분류

### config/settings.py (환경변수)

| 필드 | 타입 | DB 오버라이드 | 설명 |
|------|------|-------------|------|
| `database_url` | str | X | PostgreSQL 연결 URL |
| `upbit_access_key` | str \| None | X | Upbit API 키 |
| `upbit_secret_key` | str \| None | X | Upbit Secret 키 |
| `gemini_api_key` | str \| None | X | Gemini API 키 |
| `openai_api_key` | str \| None | X | OpenAI API 키 |
| `slack_webhook_url` | str \| None | X | Slack Webhook URL |
| `auth_server_url` | str | X | 인증 서버 URL |
| `position_size_min_pct` | float | O | 최소 포지션 % |
| `position_size_max_pct` | float | O | 최대 포지션 % |
| `stop_loss_pct` | float | O | 손절 % |
| `daily_loss_limit_pct` | float | O | 일일 손실 한도 % |
| `signal_interval_hours` | int | O | AI 신호 주기 |
| `ai_model` | str | O | Primary AI 모델 |
| `trading_ticker` | str | O | 거래 대상 |

### config/constants.py (불변 상수)

| 상수 | 값 | 설명 |
|------|-----|------|
| `APP_VERSION` | "0.1.0" | 앱 버전 |
| `UPBIT_FEE_RATE` | 0.0005 | 거래 수수료 (0.05%) |
| `UPBIT_MIN_ORDER_KRW` | 5000 | 최소 주문 금액 |
| `DEFAULT_MAX_RETRIES` | 3 | 기본 재시도 횟수 |
| `DEFAULT_TIMEOUT_SECONDS` | 30 | 기본 타임아웃 |
| `LOG_ROTATION_SIZE` | "10MB" | 로그 로테이션 크기 |
| `LOG_RETENTION_DAYS` | 7 | 로그 보관 일수 |

### DB system_configs (런타임)

| key | 타입 | 기본값 |
|-----|------|--------|
| `trading_enabled` | bool | true |
| `trading_ticker` | str | "KRW-BTC" |
| `position_size_min_pct` | float | 25.0 |
| `position_size_max_pct` | float | 50.0 |
| `stop_loss_pct` | float | 5.0 |
| `daily_loss_limit_pct` | float | 5.0 |
| `signal_interval_hours` | int | 1 |
| `ai_model` | str | "gemini-2.5-pro" |
| `volatility_threshold_pct` | float | 3.0 |
