# Bitcoin-Auto-Trading 프로젝트 종합 분석 보고서

> 비트코인 자동 거래 시스템 전면 리팩토링 후 최종 검토
> 작성일: 2026-01-24

---

## 1. 프로젝트 개요

### 1.1 시스템 목적
- **Gemini AI 기반** 비트코인 매매 신호 생성
- **Upbit 거래소** 자동 주문 실행
- **실시간 리스크 관리** 및 손절/변동성 감시

### 1.2 기술 스택
| 구분 | 기술 |
|------|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async) |
| Database | PostgreSQL 15 |
| Scheduler | APScheduler (AsyncIOScheduler) |
| AI | Google Gemini 2.5 Pro, OpenAI GPT-4.1-mini (Fallback) |
| 거래소 | Upbit REST API |

### 1.3 프로젝트 규모
- **102개 Python 파일**
- **~4,900줄 코드**
- **10개 DB 테이블**
- **6개 스케줄러 작업**

---

## 2. 아키텍처 다이어그램

### 2.1 전체 시스템 구조

```mermaid
graph TB
    subgraph External["외부 서비스"]
        UPBIT["Upbit API"]
        GEMINI["Gemini AI"]
        OPENAI["OpenAI (Fallback)"]
        SLACK["Slack Webhook"]
        AUTH["Auth Server"]
    end

    subgraph Backend["FastAPI Backend"]
        APP["app.py<br/>진입점"]

        subgraph Config["설정 계층"]
            SETTINGS["settings.py<br/>환경변수"]
            CONSTANTS["constants.py<br/>불변 상수"]
            SYSCONFIG["SystemConfig<br/>DB 설정"]
        end

        subgraph API["API Router (/api/v1)"]
            HEALTH["/health"]
            MARKET["/market"]
            SIGNALS["/signals"]
            TRADING["/trading"]
            RISK["/risk"]
            DASHBOARD["/dashboard"]
            CONFIGAPI["/config"]
        end

        subgraph Scheduler["스케줄러"]
            SCH["APScheduler"]
            JOB1["시세 수집<br/>10초"]
            JOB2["신호 생성<br/>1시간"]
            JOB3["변동성 체크<br/>30초"]
            JOB4["성과 평가<br/>4시간"]
            JOB5["주문 동기화<br/>5분"]
            JOB6["데이터 정리<br/>24시간"]
        end

        subgraph Modules["도메인 모듈"]
            MOD_MARKET["Market<br/>시세 수집/분석"]
            MOD_SIGNAL["Signal<br/>AI 신호 생성"]
            MOD_TRADING["Trading<br/>주문 실행"]
            MOD_RISK["Risk<br/>리스크 관리"]
        end

        subgraph Clients["외부 클라이언트"]
            CLI_UPBIT_PUB["UpbitPublicAPI"]
            CLI_UPBIT_PRI["UpbitPrivateAPI"]
            CLI_AI["AIClient"]
            CLI_SLACK["SlackClient"]
        end

        subgraph Data["데이터 계층"]
            REPO["Repositories"]
            ENTITY["Entities"]
            DB[(PostgreSQL)]
        end
    end

    APP --> Config
    APP --> API
    APP --> Scheduler

    SCH --> JOB1 & JOB2 & JOB3 & JOB4 & JOB5 & JOB6

    JOB1 --> MOD_MARKET
    JOB2 --> MOD_SIGNAL --> MOD_TRADING
    JOB3 --> MOD_RISK
    JOB4 --> MOD_SIGNAL
    JOB5 --> MOD_TRADING

    MOD_MARKET --> CLI_UPBIT_PUB --> UPBIT
    MOD_SIGNAL --> CLI_AI --> GEMINI & OPENAI
    MOD_TRADING --> CLI_UPBIT_PRI --> UPBIT
    MOD_RISK --> CLI_SLACK --> SLACK

    Modules --> REPO --> ENTITY --> DB

    API --> Modules
    AUTH -.->|토큰 검증| API
```

### 2.2 데이터 흐름 (자동 거래 사이클)

```mermaid
sequenceDiagram
    participant SCH as 스케줄러
    participant DC as DataCollector
    participant UPUB as Upbit Public
    participant DB as PostgreSQL
    participant SS as SignalService
    participant AI as Gemini AI
    participant TS as TradingService
    participant OV as OrderValidator
    participant RS as RiskService
    participant UPRI as Upbit Private
    participant PM as PositionManager

    Note over SCH: 10초마다
    SCH->>DC: collect_market_data_job()
    DC->>UPUB: get_ticker()
    UPUB-->>DC: 현재가, 거래량
    DC->>DB: MarketData 저장

    Note over SCH: 1시간마다
    SCH->>SS: generate_trading_signal_job()
    SS->>DB: 최근 168시간 시세 조회
    SS->>SS: 기술적 지표 계산<br/>(RSI, MACD, BB, EMA, ATR)
    SS->>AI: 프롬프트 전송
    AI-->>SS: BUY/SELL/HOLD + 신뢰도
    SS->>DB: TradingSignal 저장

    alt BUY 또는 SELL 신호
        SS->>TS: execute_from_signal()
        TS->>OV: validate_signal()
        OV->>RS: check_daily_loss_limit()
        OV->>RS: check_volatility()
        RS-->>OV: PASS/BLOCKED

        alt PASS
            TS->>OV: validate_buy/sell_order()
            OV->>RS: check_position_size()
            RS-->>OV: PASS
            TS->>UPRI: place_order()
            UPRI-->>TS: order_uuid
            TS->>DB: Order 저장 (PENDING)

            loop 최대 30회
                TS->>UPRI: get_order_status()
                UPRI-->>TS: 체결 상태
            end

            TS->>DB: Order 업데이트 (DONE)
            TS->>PM: update_position()
            PM->>DB: Position 업데이트
            TS->>DB: DailyStats 업데이트
        else BLOCKED
            TS->>DB: RiskEvent 기록
        end
    end
```

### 2.3 설정 관리 계층

```mermaid
graph LR
    subgraph Layer1["1. 환경변수 (최우선)"]
        ENV[".env / 시스템 환경변수"]
        ENV --> DB_URL["DATABASE_URL"]
        ENV --> API_KEYS["UPBIT_*, GEMINI_*, OPENAI_*"]
        ENV --> TICKER["TRADING_TICKER"]
    end

    subgraph Layer2["2. DB 설정 (오버라이드 가능)"]
        SYSCONF["system_configs 테이블"]
        SYSCONF --> POS_SIZE["position_size_*_pct"]
        SYSCONF --> STOP["stop_loss_pct"]
        SYSCONF --> DAILY["daily_loss_limit_pct"]
        SYSCONF --> AI_MODEL["ai_model"]
        SYSCONF --> VOL["volatility_threshold_pct"]
    end

    subgraph Layer3["3. 불변 상수"]
        CONST["constants.py"]
        CONST --> FEE["UPBIT_FEE_RATE (0.05%)"]
        CONST --> MIN_ORDER["MIN_ORDER_KRW (5000원)"]
        CONST --> RATE_LIMIT["RATE_LIMIT_* (10/s, 30/s)"]
        CONST --> RETENTION["DATA_RETENTION_DAYS (365)"]
    end

    Layer1 --> Layer2 --> Layer3
```

### 2.4 모듈 의존성

```mermaid
graph TD
    subgraph Modules["도메인 모듈"]
        MARKET["market/"]
        SIGNAL["signal/"]
        TRADING["trading/"]
        RISK["risk/"]
        CONFIG["config/"]
        DASHBOARD["dashboard/"]
    end

    subgraph Clients["클라이언트"]
        UPBIT_PUB["upbit/public_api"]
        UPBIT_PRI["upbit/private_api"]
        AI_CLIENT["ai/client"]
        GEMINI["ai/gemini_client"]
        OPENAI["ai/openai_client"]
    end

    subgraph Repos["레포지토리"]
        MARKET_REPO["MarketRepository"]
        SIGNAL_REPO["SignalRepository"]
        ORDER_REPO["OrderRepository"]
        POS_REPO["PositionRepository"]
        CONFIG_REPO["ConfigRepository"]
    end

    MARKET --> UPBIT_PUB
    MARKET --> MARKET_REPO

    SIGNAL --> AI_CLIENT
    SIGNAL --> MARKET
    SIGNAL --> SIGNAL_REPO
    AI_CLIENT --> GEMINI --> OPENAI

    TRADING --> UPBIT_PRI
    TRADING --> RISK
    TRADING --> ORDER_REPO
    TRADING --> POS_REPO

    RISK --> CONFIG
    RISK --> MARKET_REPO

    DASHBOARD --> MARKET
    DASHBOARD --> TRADING
    DASHBOARD --> SIGNAL
```

### 2.5 DB ERD

```mermaid
erDiagram
    users ||--o{ trading_signals : "owns"
    users ||--o{ orders : "owns"
    users ||--o{ positions : "owns"
    users ||--o{ daily_stats : "owns"
    users ||--o{ risk_events : "owns"
    users ||--o{ user_configs : "has"

    trading_signals ||--o| market_data : "references"
    trading_signals ||--o{ orders : "triggers"
    orders ||--o{ risk_events : "triggers"

    users {
        bigint id PK
        string auth_user_id UK "Auth Server UUID"
        string email
        string name
        datetime created_at
        datetime updated_at
    }

    market_data {
        bigint id PK
        string symbol "KRW-BTC"
        datetime timestamp
        decimal price
        decimal volume
        decimal high_price
        decimal low_price
    }

    trading_signals {
        bigint id PK
        bigint user_id FK
        bigint market_data_id FK
        enum signal_type "BUY/HOLD/SELL"
        decimal confidence "0.0~1.0"
        text reasoning
        string model_name
        json technical_snapshot
        decimal price_at_signal
        boolean outcome_evaluated
        boolean outcome_correct
    }

    orders {
        bigint id PK
        bigint user_id FK
        bigint signal_id FK
        enum order_type "MARKET/LIMIT"
        enum side "BUY/SELL"
        string market
        decimal amount
        decimal price
        enum status "PENDING/EXECUTED/FAILED/CANCELLED"
        string upbit_uuid UK
        string idempotency_key UK
        decimal executed_price
        decimal fee
    }

    positions {
        bigint id PK
        bigint user_id FK
        string symbol UK
        decimal quantity
        decimal avg_buy_price
        decimal current_value
        decimal unrealized_pnl
    }

    daily_stats {
        bigint id PK
        bigint user_id FK
        date date UK
        decimal starting_balance
        decimal ending_balance
        decimal realized_pnl
        int trade_count
        int win_count
        boolean is_trading_halted
    }

    risk_events {
        bigint id PK
        bigint user_id FK
        bigint order_id FK
        enum event_type
        string trigger_value
        string action_taken
        boolean notified
    }

    system_configs {
        bigint id PK
        string key UK
        json value
    }

    user_configs {
        bigint id PK
        bigint user_id FK
        string key
        json value
    }
```

---

## 3. 스케줄러 작업 상세

| 작업 ID | 주기 | 기능 | 핵심 로직 |
|---------|------|------|---------|
| `collect_market_data` | 10초 | 시세 수집 | Upbit → MarketData 저장 |
| `generate_trading_signal` | 1시간 | AI 신호 생성 + 자동 매매 | 지표 분석 → Gemini → BUY/SELL 시 주문 |
| `check_volatility` | 30초 | 변동성 감시 | 5분 변동률 > 3% 시 거래 중단 |
| `evaluate_signal_performance` | 4시간 | 신호 성과 평가 | 24시간 후 가격 비교 |
| `sync_pending_orders` | 5분 | PENDING 주문 동기화 | Upbit 상태 확인 → DB 업데이트 |
| `cleanup_old_data` | 24시간 | 오래된 데이터 삭제 | 365일 이상 MarketData 삭제 |

---

## 4. 리스크 관리 체계

### 4.1 체크 시점 및 순서

```mermaid
graph TD
    START[신호 발생] --> CHK1{거래 활성화?}
    CHK1 -->|No| BLOCK1[BLOCKED: TRADING_DISABLED]
    CHK1 -->|Yes| CHK2{일일 손실 한도?}

    CHK2 -->|초과| BLOCK2[BLOCKED: DAILY_LIMIT_REACHED]
    CHK2 -->|OK| CHK3{변동성 체크?}

    CHK3 -->|초과| BLOCK3[BLOCKED: HIGH_VOLATILITY]
    CHK3 -->|OK| CHK4{포지션 크기?}

    CHK4 -->|초과| BLOCK4[BLOCKED: POSITION_SIZE_EXCEEDED]
    CHK4 -->|OK| CHK5{손절 체크?}

    CHK5 -->|발동| SELL[강제 매도 실행]
    CHK5 -->|OK| EXEC[주문 실행]
```

### 4.2 기본 설정값

| 설정 | 기본값 | 설명 |
|------|--------|------|
| position_size_min_pct | 1% | 최소 포지션 (신뢰도 0.5) |
| position_size_max_pct | 3% | 최대 포지션 (신뢰도 0.9+) |
| stop_loss_pct | 5% | 개별 손절 |
| daily_loss_limit_pct | 5% | 일일 손실 한도 |
| volatility_threshold_pct | 3% | 5분 변동성 임계값 |

---

## 5. 디렉토리 구조

```
backend/src/
├── app.py                      # FastAPI 진입점
├── config/
│   ├── settings.py             # Pydantic BaseSettings
│   ├── constants.py            # 불변 상수
│   └── logging.py              # loguru 설정
│
├── entities/                   # SQLAlchemy ORM (10개)
│   ├── base.py                 # Base, Mixins
│   ├── user.py
│   ├── market_data.py
│   ├── trading_signal.py
│   ├── order.py
│   ├── position.py
│   ├── daily_stats.py
│   ├── risk_event.py
│   ├── system_config.py
│   └── user_config.py
│
├── repositories/               # DB 접근 계층 (8개)
│   ├── base.py                 # Generic CRUD
│   ├── market_repository.py
│   ├── signal_repository.py
│   ├── order_repository.py
│   ├── position_repository.py
│   ├── config_repository.py
│   ├── user_repository.py
│   └── user_config_repository.py
│
├── modules/                    # 도메인별 모듈
│   ├── market/
│   │   ├── collector/          # DataCollector (싱글톤)
│   │   ├── analysis/           # TechnicalIndicatorCalculator
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── signal/
│   │   ├── prompt/             # SignalPromptBuilder
│   │   ├── parser/             # SignalResponseParser
│   │   ├── classifier/         # CoinClassifier
│   │   ├── tracker/            # SignalPerformanceTracker
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── trading/
│   │   ├── position/           # PositionManager
│   │   ├── monitor/            # OrderMonitor
│   │   ├── validator/          # OrderValidator
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── risk/
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── config/                 # 설정 API
│   ├── dashboard/              # 대시보드
│   ├── health/                 # 헬스체크
│   ├── auth/                   # 인증
│   └── notification/           # 알림
│
├── clients/                    # 외부 API
│   ├── upbit/
│   │   ├── public_api.py       # 시세 조회
│   │   ├── private_api.py      # 주문/잔고
│   │   └── common.py           # 데이터 모델
│   ├── ai/
│   │   ├── client.py           # AIClient (Fallback)
│   │   ├── gemini_client.py
│   │   ├── openai_client.py
│   │   └── base.py             # BaseAIClient
│   ├── slack_client.py
│   └── auth_client.py
│
├── scheduler/
│   ├── scheduler.py            # APScheduler 설정
│   └── jobs/                   # 6개 작업
│       ├── data_collection.py
│       ├── signal_generation.py
│       ├── check_volatility.py
│       ├── evaluate_signal_performance.py
│       ├── order_sync.py
│       └── cleanup.py
│
├── api/
│   └── router.py               # 라우터 통합
│
└── utils/
    ├── database.py             # 세션 관리
    ├── decorators.py
    └── exceptions.py
```

---

## 6. API 엔드포인트

| 모듈 | 메서드 | 경로 | 설명 |
|------|--------|------|------|
| Health | GET | `/health` | 서버 상태 |
| Market | GET | `/market` | 현재 시세 |
| | GET | `/market/history` | 과거 시세 |
| | GET | `/market/summary` | 통계 요약 |
| Dashboard | GET | `/dashboard/summary` | 종합 대시보드 |
| Signals | GET | `/signals` | 신호 내역 |
| | GET | `/signals/latest` | 최신 신호 |
| | POST | `/signals/generate` | 수동 신호 생성 |
| Trading | GET | `/trading/orders` | 주문 내역 |
| | GET | `/trading/position` | 현재 포지션 |
| | GET | `/trading/balance` | 계좌 잔고 |
| | POST | `/trading/orders/sync` | 주문 동기화 |
| Risk | GET | `/risk/events` | 리스크 이벤트 |
| | GET | `/risk/status` | 리스크 상태 |
| | POST | `/risk/halt` | 거래 중단 |
| | POST | `/risk/resume` | 거래 재개 |
| Config | GET | `/config` | 전체 설정 |
| | GET | `/config/{key}` | 단일 설정 |
| | PATCH | `/config/{key}` | 설정 수정 |

---

## 7. 코드 품질 평가

### 7.1 강점

| 항목 | 평가 |
|------|------|
| **아키텍처** | 계층화 잘 됨 (Entity → Repository → Service → Route) |
| **비동기 처리** | 전면 async/await, SQLAlchemy 2.0 async |
| **설정 관리** | 3계층 분리 (환경변수/DB/상수) |
| **리스크 관리** | 4단계 체크, 이벤트 기록 |
| **싱글톤 패턴** | 클라이언트/서비스 재사용 |
| **다중 사용자** | UserOwnedMixin으로 데이터 격리 |
| **AI Fallback** | Gemini 실패 시 OpenAI 자동 전환 |

### 7.2 개선 필요 사항

| 항목 | 현재 상태 | 권장 사항 |
|------|---------|---------|
| 수동 주문 API | 미구현 | `POST /trading/orders` 엔드포인트 추가 |
| 거래 자동 재개 | 없음 | 변동성 정상화 시 자동 재개 옵션 |
| 단위 테스트 | 부재 | pytest 테스트 추가 필요 |
| API 문서화 | 기본 | Swagger 설명 강화 |

---

## 8. 프론트엔드 개발 시 참고사항

### 8.1 필수 API 호출

```typescript
// 대시보드 메인
GET /api/v1/dashboard/summary
→ 현재가, 포지션, 잔고, 손익 한번에 조회

// 설정 관리
GET /api/v1/config
PATCH /api/v1/config/{key}

// 거래 내역
GET /api/v1/trading/orders?limit=50
GET /api/v1/signals?limit=20

// 리스크 제어
GET /api/v1/risk/status
POST /api/v1/risk/halt
POST /api/v1/risk/resume
```

### 8.2 WebSocket 미지원
- 현재 REST API만 제공
- 실시간 시세는 **폴링** 필요 (10초 권장)

### 8.3 인증 흐름
- Auth Server에서 JWT 발급
- `Authorization: Bearer {token}` 헤더로 전달
- 백엔드에서 토큰 검증

---

## 9. 운영 명령어

```bash
# 서비스 관리
sudo systemctl restart bitcoin-backend
sudo systemctl status bitcoin-backend
journalctl -u bitcoin-backend -f

# 개발 서버
make dev-backend
make test-backend
make lint-fix

# DB 마이그레이션
make db-migrate
```

---

## 10. 결론

리팩토링 후 프로젝트는 **엔터프라이즈급 아키텍처**를 갖추었으며:

1. **명확한 계층 분리**: Entity → Repository → Service → Route
2. **유연한 설정 관리**: 환경변수 + DB + 불변상수 3계층
3. **견고한 리스크 관리**: 4단계 검증 + 이벤트 로깅
4. **확장 가능한 구조**: 모듈별 독립성, 싱글톤 패턴

프론트엔드 개발 시 위 API 명세와 데이터 흐름을 참고하여 구현하면 됩니다.
