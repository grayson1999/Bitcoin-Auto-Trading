# Implementation Plan: Bitcoin Auto-Trading System

**Branch**: `001-bitcoin-auto-trading` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bitcoin-auto-trading/spec.md`

## Summary

Upbit 거래소와 AI API를 연동하여 비트코인 자동 매매를 수행하는 시스템 구현. 1시간 주기로 AI 신호를 생성하고, 리스크 관리 규칙 하에 자동 주문을 실행하며, 웹 대시보드로 모니터링. 개인 프로젝트로서 **API 비용 최소화**가 핵심 목표.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript (Frontend)
**Primary Dependencies**: FastAPI, httpx, SQLAlchemy 2.0, APScheduler, google-generativeai, React, Vite
**Storage**: SQLite (개발) / PostgreSQL (운영)
**Testing**: pytest (Backend), Vitest (Frontend)
**Target Platform**: Linux Server (Docker)
**Project Type**: Monorepo (Backend + Frontend)
**Performance Goals**: 신호→주문 10초 이내, 가용성 99.5%
**Constraints**: AI API 호출 비용 월 $0 목표 (무료 티어), Upbit 수수료 0.05%
**Scale/Scope**: 단일 사용자, BTC/KRW 마켓 전용

---

## Research Summary

### AI 모델 선택: Gemini 2.5 Flash (주력)

| Provider | Model | Input $/1M | Output $/1M | 월 비용 (720회) | 선택 |
|----------|-------|------------|-------------|----------------|------|
| **Google** | **Gemini 2.5 Flash** | $0.15 | $0.60 | **$0.44** | **주력** |
| Google | Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.29 | 최저비용 대안 |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 | $0.44 | 백업 |
| Anthropic | Claude 3 Haiku | $0.25 | $1.25 | $0.81 | 분석력 우수 |

**결정 근거**:
- Google 무료 티어: **일일 1,000회 무료** → 월 비용 $0 가능
- 충분한 추론 성능: 트레이딩 신호 생성에 적합
- Prompt Caching: 캐시 읽기 시 90% 절감

### Upbit 거래 수수료

| 마켓 | Maker/Taker | 비고 |
|------|-------------|------|
| **KRW 마켓** | **0.05%** | BTC/KRW 거래 시 적용 |
| BTC/USDT | 0.25% | 사용 안함 |

**월간 비용 예상** (100만원 거래 기준):
- AI API: $0 (무료 티어)
- 거래 수수료: ~1,000원
- **총: ~1,000원/월**

### 기술 스택 결정

| 영역 | 선택 | 근거 |
|------|------|------|
| Backend Framework | FastAPI | 비동기, 자동 문서화 |
| HTTP Client | httpx | 비동기 지원 |
| ORM | SQLAlchemy 2.0 | 비동기, 타입 안전성 |
| Scheduler | APScheduler | 간단한 주기적 작업 |
| AI SDK | google-generativeai | Gemini 공식 SDK |
| Frontend | React + Vite | 빠른 개발, SPA |
| UI | Tailwind CSS | 빠른 스타일링 |
| Chart | Recharts | React 네이티브 |
| State | React Query | 서버 상태 캐싱 |

### 리스크 파라미터

| 파라미터 | 기본값 | 설정 가능 범위 |
|----------|--------|---------------|
| 포지션 크기 | 2% | 1~5% |
| 개별 손절 | 5% | 3~10% |
| 일일 손실 한도 | 5% | 3~10% |
| AI 신호 주기 | 1시간 | 30분~4시간 |
| 데이터 보존 | 1년 | 6개월~무제한 |
| 변동성 임계값 | 3% | 1~10% |

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution이 템플릿 상태이므로 기본 원칙을 적용:
- [x] 독립적 테스트 가능한 모듈 구조
- [x] 명확한 API 계약 정의
- [x] 로깅 및 관찰 가능성 확보
- [x] 단순성 우선 (YAGNI)

---

## Project Structure

### Documentation (this feature)

```text
specs/001-bitcoin-auto-trading/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (Monorepo Structure)

```text
Bitcoin-Auto-Trading/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 앱 진입점
│   │   ├── config.py           # 설정 관리 (Pydantic Settings)
│   │   ├── database.py         # DB 연결 및 세션
│   │   │
│   │   ├── models/             # SQLAlchemy 모델
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py
│   │   │   ├── trading_signal.py
│   │   │   ├── order.py
│   │   │   ├── position.py
│   │   │   ├── risk_event.py
│   │   │   ├── daily_stats.py
│   │   │   ├── backtest_result.py
│   │   │   └── system_config.py
│   │   │
│   │   ├── services/           # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── data_collector.py
│   │   │   ├── signal_generator.py
│   │   │   ├── order_executor.py
│   │   │   ├── risk_manager.py
│   │   │   ├── backtest_runner.py
│   │   │   └── notifier.py
│   │   │
│   │   ├── api/                # FastAPI 라우터
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py
│   │   │   ├── trading.py
│   │   │   ├── signals.py
│   │   │   ├── risk.py
│   │   │   ├── config.py
│   │   │   └── backtest.py
│   │   │
│   │   └── scheduler/          # APScheduler 작업
│   │       ├── __init__.py
│   │       └── jobs.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   │
│   ├── alembic/                # DB 마이그레이션
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                # API 클라이언트
│   │   │   └── client.ts
│   │   ├── components/         # 재사용 컴포넌트
│   │   │   ├── PriceChart.tsx
│   │   │   ├── OrderTable.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   └── RiskStatus.tsx
│   │   ├── pages/              # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Signals.tsx
│   │   │   ├── Backtest.tsx
│   │   │   └── Settings.tsx
│   │   └── hooks/              # 커스텀 훅
│   │       └── useApi.ts
│   │
│   ├── tests/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml          # 통합 실행
├── Makefile                    # 공통 커맨드
├── README.md
└── .gitignore
```

**Structure Decision**: 모노레포 구조 선택. Backend(Python)와 Frontend(React)를 같은 레포에서 관리하되 각각 독립적으로 빌드/배포 가능. Docker Compose로 통합 실행.

---

## Key Design Decisions

### 1. Monorepo 구조

**근거**:
- Backend/Frontend를 한 레포에서 통합 관리
- 각각 독립적인 빌드/테스트/배포 가능
- Docker Compose로 간편한 로컬 개발 환경
- 단일 PR로 Full-stack 변경 가능

### 2. AI 모델: Gemini 2.5 Flash

**근거**:
- 무료 티어로 월 비용 $0
- GPT-4o-mini와 동등한 성능
- 공식 Python SDK 제공

### 3. 스케줄러: APScheduler (In-Process)

**근거**:
- Celery 대비 설정 단순
- 단일 프로세스로 충분 (1시간 주기)
- 외부 Redis/RabbitMQ 불필요

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | 현재 복잡성 위반 없음 | - |

---

## External Dependencies

### APIs

| API | 용도 | Rate Limit | 인증 |
|-----|------|------------|------|
| Upbit REST API | 시세, 주문, 잔고 | 초당 10회 | JWT |
| Upbit WebSocket | 실시간 체결 (선택) | - | - |
| Google Gemini API | AI 신호 생성 | 1,000회/일 (무료) | API Key |
| Slack Webhook | 알림 | 1회/초 | Webhook URL |

### Backend Libraries (Core)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| fastapi | ^0.115 | 웹 프레임워크 |
| uvicorn | ^0.34 | ASGI 서버 |
| httpx | ^0.28 | HTTP 클라이언트 |
| sqlalchemy | ^2.0 | ORM |
| alembic | ^1.14 | DB 마이그레이션 |
| pydantic | ^2.10 | 데이터 검증 |
| pydantic-settings | ^2.7 | 설정 관리 |
| google-generativeai | ^0.8 | Gemini SDK |
| apscheduler | ^3.11 | 스케줄러 |
| loguru | ^0.7 | 로깅 |

### Frontend Libraries (Core)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| react | ^18 | UI 프레임워크 |
| react-router-dom | ^6 | 라우팅 |
| @tanstack/react-query | ^5 | 서버 상태 관리 |
| recharts | ^2 | 차트 |
| tailwindcss | ^3 | 스타일링 |
| axios | ^1 | HTTP 클라이언트 |

---

## Deployment

### 권장 환경: Oracle Cloud Free Tier

| 항목 | 사양 | 월 비용 |
|------|------|--------|
| VM | ARM 4 OCPU, 24GB RAM | $0 |
| Storage | 200GB Block | $0 |
| Database | PostgreSQL (VM 내장) | $0 |
| **Total** | | **$0** |

### Docker Compose 구성

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/trading
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=trading

volumes:
  postgres_data:
```

---

## Makefile (공통 커맨드)

```makefile
.PHONY: dev test build

# 전체 실행
dev:
	docker-compose up -d

# Backend만
dev-backend:
	cd backend && uvicorn src.main:app --reload --port 8000

# Frontend만
dev-frontend:
	cd frontend && npm run dev

# 테스트
test:
	cd backend && pytest
	cd frontend && npm test

# 빌드
build:
	docker-compose build
```

---

## Next Steps

`/speckit.tasks` 명령으로 구현 태스크 생성
