# Bitcoin-Auto-Trading Development Guidelines

Auto-generated from feature plans. Last updated: 2026-01-11

## Active Technologies

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI, SQLAlchemy 2.0, APScheduler
- **HTTP Client**: httpx
- **AI SDK**: google-genai (Gemini 2.5 Flash)
- **Validation**: Pydantic v2
- **Logging**: loguru

### Frontend
- **Language**: TypeScript
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State**: React Query
- **Chart**: Recharts

### Database
- PostgreSQL 15 (개발/운영 동일)

## Project Structure (Monorepo)

```text
Bitcoin-Auto-Trading/
├── backend/
│   ├── src/
│   │   ├── main.py             # FastAPI 진입점
│   │   ├── config.py           # 설정 관리
│   │   ├── database.py         # DB 연결
│   │   ├── models/             # SQLAlchemy 모델
│   │   ├── services/           # 비즈니스 로직
│   │   ├── api/                # FastAPI 라우터
│   │   └── scheduler/          # APScheduler
│   ├── tests/
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── api/                # API 클라이언트
│   │   ├── components/         # 컴포넌트
│   │   ├── pages/              # 페이지
│   │   └── hooks/              # 커스텀 훅
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml
└── Makefile
```

## Commands

```bash
# PostgreSQL 컨테이너 시작
make dev-db

# Backend 개발 (별도 터미널)
make dev-backend

# Frontend 개발 (별도 터미널)
make dev-frontend

# DB 컨테이너 중지
make dev-db-down

# 테스트
make test-backend
make test-frontend

# 린트
make lint
make lint-fix

# DB 마이그레이션
make db-migrate
```

## Code Style

### Backend (Python)
- PEP 8, type hints 필수
- Async: httpx, SQLAlchemy async session 사용
- 모델: Pydantic v2 BaseModel 상속
- 로깅: loguru 사용 (`from loguru import logger`)

### Frontend (TypeScript)
- ESLint + Prettier
- 컴포넌트: 함수형 + hooks
- 스타일: Tailwind CSS utility classes

## Key Configurations

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `POSITION_SIZE_PCT` | 2% | 주문당 자본 비율 |
| `STOP_LOSS_PCT` | 5% | 개별 손절 비율 |
| `DAILY_LOSS_LIMIT_PCT` | 5% | 일일 손실 한도 |
| `SIGNAL_INTERVAL_HOURS` | 1 | AI 신호 주기 |
| `AI_MODEL` | gemini-2.5-flash | AI 모델 |

## External APIs

- **Upbit**: 시세, 주문, 잔고 (JWT 인증)
- **Google Gemini**: AI 신호 생성 (무료 티어 1,000회/일)
- **Slack Webhook**: 알림 (선택)

## Recent Changes

- 001-bitcoin-auto-trading: Monorepo (Backend + Frontend) + Gemini 2.5 Flash

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
