# Backend

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)

> Bitcoin Auto-Trading API 서버

## Tech Stack

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 런타임 |
| FastAPI | 0.115 | 웹 프레임워크 |
| SQLAlchemy | 2.0 | ORM (비동기) |
| asyncpg | 0.30 | PostgreSQL 드라이버 |
| Alembic | 1.14 | DB 마이그레이션 |
| APScheduler | 3.11 | 백그라운드 작업 |
| Pydantic | 2.10 | 데이터 검증 |
| httpx | 0.28 | HTTP 클라이언트 |
| google-genai | 1.0 | Gemini AI SDK |

## Setup

```bash
# 의존성 설치 (uv 사용)
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 DATABASE_URL, GEMINI_API_KEY 등 설정
```

## Development

```bash
# PostgreSQL 시작 (프로젝트 루트에서)
make dev-db

# DB 마이그레이션
uv run alembic upgrade head

# 개발 서버 실행
uv run uvicorn src.main:app --reload --port 8000
```

http://localhost:8000 에서 실행됩니다.

## Environment Variables

| 변수 | 설명 | 필수 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | O |
| `GEMINI_API_KEY` | Google Gemini API 키 | O |
| `UPBIT_ACCESS_KEY` | Upbit API Access Key | - |
| `UPBIT_SECRET_KEY` | Upbit API Secret Key | - |
| `SLACK_WEBHOOK_URL` | Slack 알림 URL | - |

## API Documentation

| URL | 설명 |
|-----|------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/health` | 서버 상태 |
| GET | `/api/v1/dashboard/summary` | 대시보드 요약 |
| GET | `/api/v1/signals` | AI 신호 목록 |
| POST | `/api/v1/signals/generate` | AI 신호 생성 |

## Database Migration

```bash
# 마이그레이션 적용
uv run alembic upgrade head

# 새 마이그레이션 생성
uv run alembic revision --autogenerate -m "설명"

# 마이그레이션 롤백 (1단계)
uv run alembic downgrade -1

# 현재 상태 확인
uv run alembic current
```

## Scripts

| 명령어 | 설명 |
|--------|------|
| `uv run pytest` | 테스트 실행 |
| `uv run ruff check .` | 린트 검사 |
| `uv run ruff format .` | 코드 포맷팅 |
