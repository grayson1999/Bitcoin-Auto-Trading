# Bitcoin Auto-Trading

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-2.5_Pro-8E75B2?logo=googlegemini&logoColor=white)

> Gemini AI 기반 매매 신호 생성 및 Upbit 자동 거래 시스템

## Directory Structure

```
Bitcoin-Auto-Trading/
├── backend/          # FastAPI 백엔드 (Python 3.11+)
├── frontend/         # React 프론트엔드 (TypeScript)
├── docker-compose.yml
├── Makefile
└── CLAUDE.md         # 개발 가이드 (상세)
```

## Quick Start

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/Bitcoin-Auto-Trading.git
cd Bitcoin-Auto-Trading

# 2. 환경 변수 설정
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# backend/.env 에서 GEMINI_API_KEY, UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY 설정

# 3. PostgreSQL 시작
make dev-db

# 4. 백엔드 실행 (새 터미널)
cd backend && uv sync && uv run alembic upgrade head
cd .. && make dev-backend

# 5. 프론트엔드 실행 (새 터미널)
cd frontend && npm install
make dev-frontend
```

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

## Environment Variables

| 위치 | 파일 | 필수 변수 |
|------|------|-----------|
| `/backend` | `.env.example` | `DATABASE_URL`, `GEMINI_API_KEY` |
| `/frontend` | `.env.example` | `VITE_API_URL` |

## Production

### 서비스 관리

```bash
# 전체 서비스 재시작
sudo systemctl restart trading-stack.target

# 상태 확인
sudo systemctl status auth-server bitcoin-trading-backend

# 로그 확인
sudo journalctl -u bitcoin-trading-backend -f
```

### Nginx

```bash
sudo systemctl status nginx
sudo nginx -t && sudo systemctl reload nginx
```

## Documentation

| 문서 | 설명 |
|------|------|
| [CLAUDE.md](./CLAUDE.md) | 개발 가이드, 아키텍처, API 상세 |
| [backend/README.md](./backend/README.md) | 백엔드 설치·실행·API 문서 |
| [frontend/README.md](./frontend/README.md) | 프론트엔드 설치·실행·빌드 |
