# Quickstart: Backend Layered Architecture

**Date**: 2026-01-21
**Feature**: [spec.md](./spec.md)

## Prerequisites

- Python 3.11+
- PostgreSQL 15
- Docker (optional, for DB)

## Setup

```bash
# 1. DB 시작
make dev-db

# 2. 의존성 설치
cd backend
pip install -e ".[dev]"

# 3. 마이그레이션 적용
make db-migrate

# 4. 백엔드 실행
make dev-backend
```

## 구조 확인

리팩토링 후 디렉토리 구조:

```bash
backend/src/
├── config/          # 설정 중앙화
├── entities/        # ORM 모델 (기존 models/)
├── repositories/    # DB 접근 계층 (신규)
├── modules/         # 도메인별 모듈 (기존 api/ + services/)
├── clients/         # 외부 API 클라이언트 (기존 services/에서 분리)
├── scheduler/       # 스케줄러 (기존 유지, 내부 분할)
└── utils/           # 공통 유틸리티 (신규)
```

## 주요 변경 사항

### 1. Import 경로 변경

```python
# Before
from models.market_data import MarketData
from services.upbit_client import UpbitClient
from api.dashboard import router

# After
from entities.market_data import MarketData
from clients.upbit import UpbitClient
from modules.market.routes import router
```

### 2. 설정 조회

```python
# 환경변수 (민감 정보)
from config.settings import settings
api_key = settings.gemini_api_key

# 불변 상수
from config.constants import UPBIT_FEE_RATE

# 런타임 설정 (DB 우선)
from modules.config.service import ConfigService
config_service = ConfigService(config_repo, settings)
trading_enabled = await config_service.get("trading_enabled")
```

### 3. Repository 사용

```python
from repositories.order_repository import OrderRepository

async def get_pending_orders(session: AsyncSession):
    repo = OrderRepository(session)
    return await repo.get_pending()
```

### 4. 모듈 구조

각 도메인 모듈은 동일한 구조:

```
modules/<domain>/
├── __init__.py
├── schemas.py      # Pydantic DTO
├── routes.py       # FastAPI Router
└── service.py      # 비즈니스 로직
```

## 검증

```bash
# 린트 검사
make lint

# 테스트 실행
make test-backend

# API 엔드포인트 확인
curl http://localhost:8000/api/v1/health
```

## 롤백

문제 발생 시 기존 브랜치로 복귀:

```bash
git checkout main
git branch -D 2-backend-layered-arch
```
