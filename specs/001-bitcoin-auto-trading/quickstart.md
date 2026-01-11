# Quickstart: Bitcoin Auto-Trading System

**Date**: 2026-01-11
**Branch**: `001-bitcoin-auto-trading`

## Prerequisites

### Required Accounts & API Keys

1. **Upbit API Key**
   - [Upbit 개발자 센터](https://upbit.com/open_api_agreement)에서 API 키 발급
   - 필요 권한: 자산 조회, 주문 조회, 주문하기
   - IP 제한 설정 권장

2. **Google AI API Key** (Gemini)
   - [Google AI Studio](https://aistudio.google.com/)에서 발급
   - 무료 티어: 일일 1,000회 요청 → **월 비용 $0**

3. **Slack Webhook URL** (선택)
   - [Slack API](https://api.slack.com/messaging/webhooks)에서 생성

### System Requirements

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (권장)
- PostgreSQL 15+ (운영) 또는 SQLite (개발)

---

## Quick Setup (Docker)

### 1. Clone & Configure

```bash
git clone <repository-url>
cd Bitcoin-Auto-Trading

# 환경 변수 설정
cp backend/.env.example backend/.env
```

### 2. Edit `backend/.env`

```bash
# Required
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key
GOOGLE_AI_API_KEY=your_google_ai_api_key

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

# Database
DATABASE_URL=postgresql://user:password@db:5432/trading

# Settings
POSITION_SIZE_PCT=2.0
STOP_LOSS_PCT=5.0
DAILY_LOSS_LIMIT_PCT=5.0
SIGNAL_INTERVAL_HOURS=1
AI_MODEL=gemini-2.5-flash
```

### 3. Run with Docker Compose

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 상태 확인
curl http://localhost:8000/api/v1/health
```

### 4. Access

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## Local Development Setup

### Backend

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e ".[dev]"

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

---

## Project Structure (Monorepo)

```text
Bitcoin-Auto-Trading/
├── backend/                # Python FastAPI
│   ├── src/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── api/
│   │   └── scheduler/
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
│
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
│
├── docker-compose.yml
└── Makefile
```

---

## Common Commands

### Makefile

```bash
# 전체 실행
make dev

# Backend만
make dev-backend

# Frontend만
make dev-frontend

# 테스트
make test

# 빌드
make build
```

### Docker

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 로그
docker-compose logs -f backend
docker-compose logs -f frontend

# 재시작
docker-compose restart backend

# DB 접속
docker-compose exec db psql -U user -d trading
```

### Backend

```bash
cd backend

# 테스트
pytest
pytest tests/unit/
pytest --cov=src tests/

# 린트
ruff check .
ruff format .

# DB 마이그레이션
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd frontend

# 개발
npm run dev

# 빌드
npm run build

# 테스트
npm test

# 린트
npm run lint
```

---

## First Run Checklist

### 1. Verify API Connections

```bash
# Upbit 연결 확인
curl http://localhost:8000/api/v1/trading/balance

# AI 연결 확인
curl -X POST http://localhost:8000/api/v1/signals/generate
```

### 2. Check Settings

```bash
# 현재 설정 확인
curl http://localhost:8000/api/v1/config

# 설정 변경
curl -X PATCH http://localhost:8000/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"position_size_pct": 1.0}'
```

### 3. Test Trading (소액)

1. Dashboard에서 잔고 확인
2. `position_size_pct`를 1%로 설정
3. AI 신호 대기 (1시간 주기)
4. 주문 실행 확인

---

## Cost Summary

| 항목 | 비용 |
|------|------|
| AI API (Gemini 무료 티어) | **$0** |
| Upbit 거래 수수료 (100만원 거래) | ~1,000원 |
| 서버 (Oracle Free Tier) | $0 |
| **총 예상 비용** | **~1,000원/월** |

---

## Troubleshooting

### Upbit API 오류

| 오류 | 원인 | 해결 |
|-----|-----|-----|
| `401 Unauthorized` | 잘못된 API 키 | 키 재발급 |
| `429 Too Many Requests` | Rate limit 초과 | 요청 간격 조정 |

### AI API 오류

| 오류 | 원인 | 해결 |
|-----|-----|-----|
| `429 Quota exceeded` | 일일 한도 초과 | 다음 날 대기 |

### 시스템 관리

```bash
# 헬스체크
curl http://localhost:8000/api/v1/health

# 거래 수동 중단
curl -X POST http://localhost:8000/api/v1/risk/halt \
  -d '{"reason": "Manual halt"}'

# 거래 재개
curl -X POST http://localhost:8000/api/v1/risk/resume
```
