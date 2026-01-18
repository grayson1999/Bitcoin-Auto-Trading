# XRP → 동적 코인 설정 마이그레이션 진행 상황

**작업 일시**: 2026-01-18
**목적**: XRP 하드코딩 제거 → 환경변수 기반 동적 코인 설정 (기본값: SOL)

---

## 완료된 작업

### Phase 1: 인프라 (100% 완료)

#### 1. `backend/src/config.py` - 새 환경변수 추가
```python
# 추가된 설정
trading_ticker: str = "KRW-SOL"  # 거래 마켓 코드
trading_currency: str = "SOL"    # 거래 코인 심볼
signal_stop_loss_pct: float = 0.015   # 손절 1.5%
signal_take_profit_pct: float = 0.025 # 익절 2.5%
signal_trailing_stop_pct: float = 0.02
signal_breakeven_pct: float = 0.01
```

#### 2. `backend/src/services/coin_classifier.py` - 신규 생성
- CoinType enum (MAJOR, MEMECOIN, ALTCOIN)
- COIN_TYPE_MAP 정적 매핑
- get_coin_type() 함수

#### 3. `backend/src/services/prompt_templates.py` - 신규 생성
- PromptConfig 데이터클래스
- PROMPT_CONFIGS (코인 유형별 기본 설정)
- MAJOR_COIN_SYSTEM_INSTRUCTION
- MEMECOIN_SYSTEM_INSTRUCTION
- ALTCOIN_SYSTEM_INSTRUCTION
- ANALYSIS_PROMPT_TEMPLATE
- get_system_instruction(), get_analysis_prompt() 함수

---

### Phase 2: 핵심 서비스 (100% 완료)

#### 4. `backend/src/services/signal_generator.py` - 전면 리팩토링
- 하드코딩된 SYSTEM_INSTRUCTION, ANALYSIS_PROMPT_TEMPLATE 제거
- prompt_templates.py에서 동적 생성
- `__init__`: ticker, currency, coin_type, prompt_config 초기화
- `_get_balance_info()`: XRP → self.currency 동적화
- `_format_asset_status()`: 동적 코인 심볼 표시
- `_format_risk_check()`: 동적 손절 비율 사용

#### 5. `backend/src/services/data_collector.py` - 수정
- `DEFAULT_MARKET = "KRW-XRP"` 제거
- `__init__`: `market = market or settings.trading_ticker`

#### 6. `backend/src/services/multi_timeframe_analyzer.py` - 수정
- `from src.config import settings` 추가
- `fetch_candle_data()`: `market: str | None = None` → `settings.trading_ticker`
- `analyze()`: 동일하게 수정

---

### Phase 3: 부가 서비스 (100% 완료)

#### 7. `backend/src/services/order_executor.py` - 수정 완료
- `DEFAULT_MARKET` → `settings.trading_ticker` (전체 교체)
- `BalanceInfo` 필드 일반화:
  - `xrp_available` → `coin_available`
  - `xrp_locked` → `coin_locked`
  - `xrp_avg_price` → `coin_avg_price`
- `acc.currency == "XRP"` → `acc.currency == settings.trading_currency`
- 로그 메시지 동적화

#### 8. `backend/src/services/signal_performance_tracker.py` - 수정 완료
- `from src.config import settings` 추가
- `evaluate_pending_signals()`: `market: str | None = None` → `market or settings.trading_ticker`

#### 9. `backend/src/services/upbit_client.py` - 수정 완료
- `get_ticker()`, `get_orderbook()`: `market: str | None = None` → `market or settings.trading_ticker`
- `get_minute_candles()`, `get_day_candles()`, `get_week_candles()`: 동일하게 수정

#### 10. `backend/src/services/notifier.py` - 수정 완료
- `send_trade_notification()`: `symbol: str | None = None` → `symbol or settings.trading_ticker`

#### 11. `backend/src/services/backtest_runner.py` - 수정 완료
- `from src.config import settings` 추가
- `get_minute_candles(market=...)` → `market=settings.trading_ticker`

---

### Phase 4: API 파일 (100% 완료)

#### 12. `backend/src/api/dashboard.py` - 수정 완료
- `DEFAULT_MARKET = "KRW-XRP"` 제거
- `from src.config import settings` 추가
- 모든 DEFAULT_MARKET 참조 → `settings.trading_ticker`
- 잔고 필드 일반화 (xrp → coin)

#### 13. `backend/src/api/trading.py` - 수정 완료
- `DEFAULT_MARKET = "KRW-XRP"` 제거
- `from src.config import settings` 추가
- 모든 DEFAULT_MARKET 참조 → `settings.trading_ticker`
- 잔고 필드 일반화 (xrp → coin)

#### 14. `backend/src/api/schemas/market.py` - 수정 완료
- `CurrentMarketResponse.market` 기본값 제거

#### 15. `backend/src/api/schemas/order.py` - 수정 완료
- `BalanceResponse` 필드 일반화:
  - `xrp` → `coin`
  - `xrp_locked` → `coin_locked`
  - `xrp_avg_buy_price` → `coin_avg_buy_price`
- `PositionResponse` docstring 업데이트

#### 16. `backend/src/models/order.py` - 수정 완료
- `from src.config import settings` 추가
- `market` 필드 기본값: `"KRW-XRP"` → `settings.trading_ticker`

---

### Phase 5: 프론트엔드 (100% 완료)

#### 17. `frontend/src/pages/Dashboard.tsx` - 수정 완료
- "XRP" 문자열 → `position.symbol.split("-")[1]` 동적 추출
- `PriceChart`에 `symbol` prop 전달

#### 18. `frontend/src/components/PriceChart.tsx` - 수정 완료
- `symbol` prop 추가
- `formatMarketName()` 함수로 동적 표시 (예: "KRW-SOL" → "SOL/KRW")

---

### Phase 6: 설정 및 테스트 (100% 완료)

#### 19. `backend/.env.example` - 수정 완료
추가된 환경변수:
```bash
# === Trading Target ===
TRADING_TICKER=KRW-SOL
TRADING_CURRENCY=SOL

# === Signal Risk Management ===
SIGNAL_STOP_LOSS_PCT=0.015
SIGNAL_TAKE_PROFIT_PCT=0.025
SIGNAL_TRAILING_STOP_PCT=0.02
SIGNAL_BREAKEVEN_PCT=0.01
```

---

## 미완료 작업

### 주석/Docstring 업데이트 (선택적)

일부 주석/docstring에 XRP 참조가 남아있으나, 런타임에 영향 없음:
- `models/market_data.py` - 주석
- `models/position.py` - 주석
- `services/upbit_client.py` - 예시 코드 주석
- `services/ai_client.py` - 예시 코드 주석

---

## 검증 명령어

```bash
# 남은 XRP 하드코딩 확인 (주석 제외)
grep -rn "XRP\|KRW-XRP" backend/src/ --include="*.py" | grep -v "coin_classifier.py" | grep -v "__pycache__"

# 린트 검사
cd backend && python3 -m ruff check src/

# 테스트 실행
cd backend && pytest tests/
```

---

## 환경변수 요약

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `TRADING_TICKER` | `KRW-SOL` | 거래 마켓 코드 |
| `TRADING_CURRENCY` | `SOL` | 거래 코인 심볼 |
| `SIGNAL_STOP_LOSS_PCT` | `0.015` | 손절 비율 (1.5%) |
| `SIGNAL_TAKE_PROFIT_PCT` | `0.025` | 익절 비율 (2.5%) |
| `SIGNAL_TRAILING_STOP_PCT` | `0.02` | 트레일링 스탑 활성화 (2%) |
| `SIGNAL_BREAKEVEN_PCT` | `0.01` | 본전 손절 활성화 (1%) |

---

## 신규 생성 파일

1. `backend/src/services/coin_classifier.py`
2. `backend/src/services/prompt_templates.py`

## 수정된 파일 (전체)

### 백엔드 (16개)
1. `backend/src/config.py`
2. `backend/src/services/signal_generator.py`
3. `backend/src/services/data_collector.py`
4. `backend/src/services/multi_timeframe_analyzer.py`
5. `backend/src/services/order_executor.py`
6. `backend/src/services/signal_performance_tracker.py`
7. `backend/src/services/upbit_client.py`
8. `backend/src/services/notifier.py`
9. `backend/src/services/backtest_runner.py`
10. `backend/src/api/dashboard.py`
11. `backend/src/api/trading.py`
12. `backend/src/api/schemas/market.py`
13. `backend/src/api/schemas/order.py`
14. `backend/src/models/order.py`
15. `backend/.env.example`

### 프론트엔드 (2개)
16. `frontend/src/pages/Dashboard.tsx`
17. `frontend/src/components/PriceChart.tsx`
