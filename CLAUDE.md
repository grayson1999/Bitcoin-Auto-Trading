# Bitcoin-Auto-Trading 개발 가이드

> 비트코인 자동 거래 시스템 - Gemini AI 기반 매매 신호 생성 및 Upbit 자동 거래

마지막 업데이트: 2026-01-24

---

## 개요

이 프로젝트는 Google Gemini AI를 활용하여 비트코인 매매 신호를 생성하고,
Upbit 거래소 API를 통해 자동으로 거래를 실행하는 시스템입니다.

### 주요 기능
- **실시간 시세 수집**: Upbit API에서 주기적으로 시세 수집
- **AI 매매 신호**: Gemini 2.5 Pro 모델을 통한 매수/매도/홀드 신호 생성 (Fallback: GPT-4.1-mini)
- **자동 거래 실행**: 신호에 따른 자동 주문 실행
- **위험 관리**: 손절매, 일일 손실 한도 등 리스크 관리
- **대시보드**: 실시간 포지션, 수익률, 거래 내역 모니터링

---

## 기술 스택

### 백엔드 (Python)
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 런타임 |
| FastAPI | 0.100+ | 웹 프레임워크 |
| SQLAlchemy | 2.0+ | ORM (비동기) |
| asyncpg | - | PostgreSQL 드라이버 |
| APScheduler | 3.10+ | 백그라운드 작업 스케줄러 |
| httpx | - | 비동기 HTTP 클라이언트 |
| Pydantic | v2 | 데이터 검증 |
| loguru | - | 로깅 |
| PyJWT | - | Upbit API JWT 인증 |
| google-genai | - | Gemini AI SDK |

### 프론트엔드 (TypeScript)
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18+ | UI 프레임워크 |
| TypeScript | 5.0+ | 타입 안전성 |
| Vite | 5.0+ | 빌드 도구 |
| TanStack Query | v5 | 서버 상태 관리 |
| Tailwind CSS | 3.0+ | 스타일링 |

### 데이터베이스
- **PostgreSQL 15**: 개발/운영 동일 환경

---

## 프로젝트 구조

```text
Bitcoin-Auto-Trading/
├── backend/                          # 백엔드 (FastAPI)
│   ├── src/
│   │   ├── main.py                   # FastAPI 앱 진입점
│   │   ├── database.py               # SQLAlchemy 비동기 세션
│   │   │
│   │   ├── config/                   # 설정 중앙화
│   │   │   ├── settings.py           # Pydantic BaseSettings
│   │   │   ├── constants.py          # 불변 상수
│   │   │   └── logging.py            # 로깅 설정
│   │   │
│   │   ├── entities/                 # SQLAlchemy 모델
│   │   │   ├── base.py               # Base, TimestampMixin
│   │   │   ├── market_data.py        # 시세 데이터
│   │   │   ├── trading_signal.py     # AI 매매 신호
│   │   │   ├── order.py              # 주문
│   │   │   ├── position.py           # 포지션
│   │   │   ├── daily_stats.py        # 일일 통계
│   │   │   ├── risk_event.py         # 리스크 이벤트
│   │   │   └── system_config.py      # 시스템 설정
│   │   │
│   │   ├── repositories/             # DB 접근 계층
│   │   │   ├── base.py               # BaseRepository (Generic CRUD)
│   │   │   ├── market_repository.py
│   │   │   ├── signal_repository.py
│   │   │   ├── order_repository.py
│   │   │   ├── position_repository.py
│   │   │   └── config_repository.py
│   │   │
│   │   ├── modules/                  # 도메인별 모듈
│   │   │   ├── market/               # 시세 (수집, 분석, 지표)
│   │   │   ├── signal/               # AI 신호 (생성, 파싱, 프롬프트)
│   │   │   ├── trading/              # 거래 (주문, 포지션, 검증)
│   │   │   ├── risk/                 # 리스크 (체크, 이벤트)
│   │   │   ├── config/               # 설정 API
│   │   │   ├── dashboard/            # 대시보드
│   │   │   └── health/               # 헬스체크
│   │   │
│   │   ├── clients/                  # 외부 API 클라이언트
│   │   │   ├── upbit/                # Upbit (public_api, private_api)
│   │   │   ├── ai/                   # AI (gemini, openai)
│   │   │   └── slack_client.py       # Slack 알림
│   │   │
│   │   ├── scheduler/                # 스케줄러
│   │   │   └── jobs/                 # 작업 (data_collection, signal_generation 등)
│   │   │
│   │   ├── api/                      # API 라우터 통합
│   │   │   └── router.py             # /api/v1 라우터
│   │   │
│   │   └── utils/                    # 공통 유틸리티
│   │
│   ├── tests/                        # pytest 테스트
│   ├── alembic/                      # DB 마이그레이션
│   └── pyproject.toml                # Python 의존성
│
├── frontend/                         # 프론트엔드 (React)
│   ├── src/
│   │   ├── pages/                    # 페이지 컴포넌트
│   │   ├── components/               # 재사용 컴포넌트
│   │   └── api/                      # API 클라이언트
│   └── package.json
│
├── docker-compose.yml                # PostgreSQL 컨테이너
├── Makefile                          # 개발 명령어
└── CLAUDE.md                         # 이 파일
```

---

## 자주 사용하는 명령어

### systemctl (서비스 관리)
```bash
# 로그 확인
journalctl -u bitcoin-backend -f
journalctl -u bitcoin-frontend -f

# 서비스 재시작
sudo systemctl restart bitcoin-backend
sudo systemctl restart bitcoin-frontend

# 서비스 상태 확인
systemctl status bitcoin-backend bitcoin-frontend
```

### 개발 환경
```bash
# 개발 서버 실행
make dev-db          # PostgreSQL 컨테이너 시작
make dev-backend     # 백엔드 개발 서버 (uvicorn, 핫 리로드)
make dev-frontend    # 프론트엔드 개발 서버 (Vite)

# 테스트
make test-backend    # pytest 실행

# 코드 품질
make lint            # 린트 검사 (ruff)
make lint-fix        # 린트 자동 수정

# 데이터베이스
make db-migrate      # Alembic 마이그레이션 적용
```

---

## API 엔드포인트

모든 API는 `/api/v1` 접두사를 사용합니다.

### Health
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |

### Market
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/market` | 현재 시세 조회 (Upbit 실시간) |
| GET | `/market/history` | 과거 시세 조회 |
| GET | `/market/summary` | 시세 요약 통계 |
| GET | `/market/latest` | 최신 DB 레코드 조회 |
| GET | `/market/collector/stats` | 데이터 수집기 상태 |

### Dashboard
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/dashboard/summary` | 대시보드 요약 (시세, 포지션, 잔고, 손익) |

### Signals
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/signals` | AI 신호 내역 조회 |
| GET | `/signals/latest` | 최신 AI 신호 조회 |
| POST | `/signals/generate` | AI 신호 수동 생성 |

### Trading
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/trading/orders` | 주문 내역 조회 |
| GET | `/trading/orders/{id}` | 주문 상세 조회 |
| GET | `/trading/position` | 현재 포지션 조회 |
| GET | `/trading/balance` | 계좌 잔고 조회 |
| POST | `/trading/orders/sync` | 대기 주문 동기화 |

### Risk
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/risk/events` | 리스크 이벤트 조회 |
| GET | `/risk/status` | 리스크 상태 조회 |
| POST | `/risk/halt` | 거래 중단 |
| POST | `/risk/resume` | 거래 재개 |

### Config
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/config` | 모든 설정 조회 |
| GET | `/config/{key}` | 단일 설정 조회 |
| PATCH | `/config/{key}` | 단일 설정 수정 |
| PATCH | `/config` | 설정 일괄 수정 |

---

## 환경 변수

### 백엔드 (.env)
```bash
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bitcoin

# Upbit API
UPBIT_ACCESS_KEY=your-access-key
UPBIT_SECRET_KEY=your-secret-key

# AI API
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key  # Fallback

# 알림 (선택)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 프론트엔드 (.env)
```bash
VITE_API_URL=http://localhost:8000
```

---

## 주요 설정값

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `POSITION_SIZE_MIN_PCT` | 1% | 최소 포지션 크기 |
| `POSITION_SIZE_MAX_PCT` | 3% | 최대 포지션 크기 |
| `STOP_LOSS_PCT` | 5% | 개별 손절 비율 |
| `DAILY_LOSS_LIMIT_PCT` | 5% | 일일 손실 한도 |
| `SIGNAL_INTERVAL_HOURS` | 1 | AI 신호 생성 주기 |
| `DATA_COLLECTION_INTERVAL_SECONDS` | 10 | 시세 수집 간격 |

---

## 핵심 파일 설명

### 백엔드

| 경로 | 역할 |
|------|------|
| `main.py` | FastAPI 앱 초기화, 라이프사이클 관리 |
| `config/settings.py` | Pydantic BaseSettings로 환경 변수 로드 |
| `config/constants.py` | 불변 상수 (수수료율, Rate Limit 등) |
| `entities/` | SQLAlchemy ORM 모델 |
| `repositories/` | DB 접근 계층 (CRUD 추상화) |
| `modules/market/` | 시세 수집, 분석, 지표 계산 |
| `modules/signal/` | AI 신호 생성, 프롬프트 구성, 응답 파싱 |
| `modules/trading/` | 주문 실행, 포지션 관리, 잔고 검증 |
| `modules/risk/` | 리스크 체크, 손절매, 거래 중단/재개 |
| `clients/upbit/` | Upbit API 클라이언트 (public/private) |
| `clients/ai/` | Gemini/OpenAI 클라이언트 |
| `scheduler/jobs/` | 스케줄러 작업 (시세 수집, 신호 생성 등) |

---

## 외부 API

### Upbit 거래소
- **문서**: https://docs.upbit.com
- **Rate Limit**: 초당 10회 (주문), 초당 30회 (조회)

### Google Gemini AI
- **문서**: https://ai.google.dev
- **모델**: gemini-2.5-pro
- **Rate Limit 리셋**: Pacific Time 자정 (KST 17:00)

### OpenAI (Fallback)
- **문서**: https://platform.openai.com/docs
- **모델**: gpt-4.1-mini

---

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
