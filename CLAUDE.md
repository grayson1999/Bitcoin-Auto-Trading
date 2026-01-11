# Bitcoin-Auto-Trading 개발 가이드

> 비트코인 자동 거래 시스템 - Gemini AI 기반 매매 신호 생성 및 Upbit 자동 거래

마지막 업데이트: 2026-01-11

---

## 개요

이 프로젝트는 Google Gemini AI를 활용하여 비트코인 매매 신호를 생성하고,
Upbit 거래소 API를 통해 자동으로 거래를 실행하는 시스템입니다.

### 주요 기능
- **실시간 시세 수집**: Upbit API에서 1초 간격으로 비트코인 시세 수집
- **AI 매매 신호**: Gemini 2.5 Flash 모델을 통한 매수/매도/홀드 신호 생성
- **자동 거래 실행**: 신호에 따른 자동 주문 실행 (개발 예정)
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
| React Router | v6 | 라우팅 |
| TanStack Query | v5 | 서버 상태 관리 |
| Axios | - | HTTP 클라이언트 |
| Tailwind CSS | 3.0+ | 스타일링 |
| Recharts | - | 차트 시각화 |

### 데이터베이스
- **PostgreSQL 15**: 개발/운영 동일 환경

---

## 프로젝트 구조

```text
Bitcoin-Auto-Trading/
├── backend/                          # 백엔드 (FastAPI)
│   ├── src/
│   │   ├── main.py                   # FastAPI 앱 진입점, 라이프사이클 관리
│   │   ├── config.py                 # 환경 설정, 로깅 설정
│   │   ├── database.py               # SQLAlchemy 비동기 세션
│   │   │
│   │   ├── models/                   # SQLAlchemy 모델
│   │   │   ├── __init__.py           # Base 클래스, TimestampMixin
│   │   │   └── market_data.py        # MarketData 모델 (시세 데이터)
│   │   │
│   │   ├── services/                 # 비즈니스 로직 서비스
│   │   │   ├── __init__.py           # 서비스 모듈 익스포트
│   │   │   ├── upbit_client.py       # Upbit API 클라이언트 (시세, 주문, 잔고)
│   │   │   └── data_collector.py     # 시세 데이터 수집기
│   │   │
│   │   ├── api/                      # FastAPI 라우터
│   │   │   ├── __init__.py           # 라우터 통합 (/api/v1)
│   │   │   ├── health.py             # 헬스체크 (/health)
│   │   │   ├── dashboard.py          # 대시보드 API (/dashboard)
│   │   │   └── schemas/
│   │   │       └── market.py         # Pydantic 응답 스키마
│   │   │
│   │   └── scheduler/                # APScheduler 작업
│   │       ├── __init__.py           # 스케줄러 모듈 익스포트
│   │       └── jobs.py               # 스케줄러 작업 정의
│   │
│   ├── tests/                        # pytest 테스트
│   ├── alembic/                      # DB 마이그레이션
│   ├── pyproject.toml                # Python 의존성
│   └── Dockerfile
│
├── frontend/                         # 프론트엔드 (React)
│   ├── src/
│   │   ├── main.tsx                  # React 앱 진입점, React Query 설정
│   │   ├── App.tsx                   # 루트 레이아웃, 네비게이션
│   │   │
│   │   ├── api/
│   │   │   └── client.ts             # Axios API 클라이언트
│   │   │
│   │   ├── pages/                    # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx         # 대시보드 (메인)
│   │   │   ├── Orders.tsx            # 주문 내역
│   │   │   ├── Signals.tsx           # AI 거래 신호
│   │   │   └── Settings.tsx          # 설정
│   │   │
│   │   ├── components/               # 재사용 컴포넌트
│   │   └── hooks/                    # 커스텀 React 훅
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml                # PostgreSQL 컨테이너
├── Makefile                          # 개발 명령어
└── CLAUDE.md                         # 이 파일
```

---

## 개발 명령어

```bash
# === 개발 환경 실행 ===
make dev-db          # PostgreSQL 컨테이너 시작
make dev-backend     # 백엔드 개발 서버 (uvicorn, 핫 리로드)
make dev-frontend    # 프론트엔드 개발 서버 (Vite)
make dev-db-down     # DB 컨테이너 중지

# === 테스트 ===
make test-backend    # pytest 실행
make test-frontend   # vitest 실행

# === 코드 품질 ===
make lint            # 린트 검사 (ruff + eslint)
make lint-fix        # 린트 자동 수정

# === 데이터베이스 ===
make db-migrate      # Alembic 마이그레이션 적용
```

---

## API 엔드포인트

### 헬스체크
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/health` | 서버 상태 확인 |

### 대시보드
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/dashboard/current` | 현재 시세 조회 |
| GET | `/api/v1/dashboard/history` | 시세 히스토리 (1시간) |
| GET | `/api/v1/dashboard/summary` | 24시간 요약 통계 |
| GET | `/api/v1/dashboard/collector/stats` | 데이터 수집기 상태 |

---

## 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                        Bitcoin-Auto-Trading                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    1초 간격    ┌───────────────┐                  │
│  │ Upbit    │ ────────────▶ │ DataCollector │                  │
│  │ API      │    시세 수집   │ (서비스)       │                  │
│  └──────────┘               └───────┬───────┘                  │
│                                      │                          │
│                                      ▼                          │
│                             ┌───────────────┐                  │
│                             │ PostgreSQL    │                  │
│                             │ (MarketData)  │                  │
│                             └───────┬───────┘                  │
│                                      │                          │
│                                      ▼                          │
│  ┌──────────┐               ┌───────────────┐                  │
│  │ React    │ ◀──────────── │ Dashboard API │                  │
│  │ Frontend │   REST API    │ (FastAPI)     │                  │
│  └──────────┘               └───────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 상세 흐름
1. **시세 수집**: APScheduler가 1초마다 `DataCollector.collect()` 실행
2. **Upbit API 호출**: `UpbitClient.get_ticker("KRW-BTC")`로 현재가 조회
3. **DB 저장**: `MarketData` 모델로 PostgreSQL에 저장
4. **API 제공**: Dashboard API가 저장된 데이터 조회/집계
5. **프론트엔드 표시**: React Query로 폴링하여 UI 갱신

---

## 코드 스타일

### 백엔드 (Python)
- **PEP 8** 준수, **type hints** 필수
- **비동기**: `async/await` 패턴 사용
  - HTTP: `httpx.AsyncClient`
  - DB: `AsyncSession` (SQLAlchemy 2.0)
- **모델**: Pydantic v2 `BaseModel` 상속
- **로깅**: loguru 사용 (`from loguru import logger`)
- **주석**: 한국어 docstring, 복잡한 로직에 인라인 주석

### 프론트엔드 (TypeScript)
- **ESLint + Prettier** 적용
- **컴포넌트**: 함수형 + React Hooks
- **스타일**: Tailwind CSS utility classes
- **상태 관리**: TanStack Query (서버 상태)
- **주석**: 한국어 JSDoc, 컴포넌트 목적 설명

---

## 환경 변수

### 백엔드 (.env)
```bash
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bitcoin

# Upbit API (선택 - 시세 조회는 공개 API)
UPBIT_ACCESS_KEY=your-access-key
UPBIT_SECRET_KEY=your-secret-key

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key

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
| `POSITION_SIZE_PCT` | 2% | 주문당 자본 비율 |
| `STOP_LOSS_PCT` | 5% | 개별 손절 비율 |
| `DAILY_LOSS_LIMIT_PCT` | 5% | 일일 손실 한도 |
| `SIGNAL_INTERVAL_HOURS` | 1 | AI 신호 생성 주기 |
| `AI_MODEL` | gemini-2.5-flash | Gemini AI 모델 |
| `DATA_COLLECT_INTERVAL` | 1초 | 시세 수집 간격 |
| `DATA_RETENTION_DAYS` | 7일 | 시세 데이터 보관 기간 |

---

## 외부 API

### Upbit 거래소
- **용도**: 시세 조회, 주문 실행, 잔고 확인
- **인증**: JWT (HS256)
- **Rate Limit**: 초당 10회 (주문), 초당 30회 (조회)
- **문서**: https://docs.upbit.com

### Google Gemini AI
- **용도**: 매매 신호 생성, 시장 분석
- **모델**: gemini-2.5-flash
- **무료 티어**: 1,000회/일
- **문서**: https://ai.google.dev

### Slack Webhook (선택)
- **용도**: 거래 알림, 오류 알림
- **설정**: 워크스페이스에서 Incoming Webhook 생성

---

## 핵심 파일 설명

### 백엔드

| 파일 | 역할 |
|------|------|
| `main.py` | FastAPI 앱 초기화, CORS 설정, 라이프사이클 관리 (스케줄러 시작/종료) |
| `config.py` | Pydantic Settings로 환경 변수 로드, loguru 로깅 설정 |
| `database.py` | SQLAlchemy 비동기 엔진/세션 팩토리, 커넥션 풀 관리 |
| `models/market_data.py` | MarketData 모델 - 시세 데이터 저장 (Numeric(18,8) 정밀도) |
| `services/upbit_client.py` | Upbit API 래퍼 - 시세, 주문, 잔고 API 호출 + 재시도 로직 |
| `services/data_collector.py` | 시세 수집기 - 지수 백오프 재시도, 수집 통계 관리 |
| `api/dashboard.py` | 대시보드 엔드포인트 - 현재가, 히스토리, 요약 통계 |
| `scheduler/jobs.py` | APScheduler 작업 - 시세 수집 (1초), 데이터 정리 (24시간) |

### 프론트엔드

| 파일 | 역할 |
|------|------|
| `main.tsx` | React 앱 진입점, QueryClient 설정, BrowserRouter 설정 |
| `App.tsx` | 루트 레이아웃, 사이드바 네비게이션, 라우트 정의 |
| `api/client.ts` | Axios 인스턴스, 요청/응답 인터셉터, 공통 API 메서드 |
| `pages/Dashboard.tsx` | 대시보드 페이지 (실시간 시세, 차트, 통계) |
| `pages/Orders.tsx` | 주문 내역 페이지 (주문 조회, 필터링) |
| `pages/Signals.tsx` | AI 신호 페이지 (매매 신호, 신뢰도) |
| `pages/Settings.tsx` | 설정 페이지 (거래 파라미터, API 키) |

---

## 개발 이력

- **Phase 3**: 실시간 시장 데이터 수집 구현 (Upbit API, DataCollector)
- **Phase 2**: 백엔드/프론트엔드 기반 인프라 구축
- **Phase 1**: 모노레포 구조 및 프로젝트 초기화

---

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
