# Implementation Plan: Backend 성능 최적화

**Branch**: `002-backend-performance` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-backend-performance/spec.md`

## Summary

비트코인 자동 거래 시스템의 백엔드 성능 및 안정성 개선. DB 커넥션 풀 확장(5/10 → 10/20), 설정값 TTL 캐시(1시간), 스케줄러 지수 백오프 재시도(3회), 6개 구성요소 상세 헬스체크, 구조화된 JSON 메트릭 로깅을 구현한다.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), APScheduler 3.10, loguru, httpx
**Storage**: PostgreSQL 15 (asyncpg)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Ubuntu)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 동시 10개 이상 DB 작업 처리, 캐시 히트율 95%+, 쿼리 20%+ 개선
**Constraints**: 기존 테스트 커버리지 80% 유지, 무중단 배포
**Scale/Scope**: 단일 서비스, 1개 거래 페어 (KRW-BTC)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 원칙 | 상태 | 비고 |
|------|------|------|
| 기존 코드 우선 재사용 | ✅ PASS | 기존 database.py, config_repository.py 수정 |
| 단일 책임 원칙 | ✅ PASS | 캐시, 재시도, 헬스체크 각각 분리 |
| 테스트 필수 | ✅ PASS | 각 변경사항에 대한 테스트 작성 |
| 에러 핸들링 | ✅ PASS | 재시도 로직에 상세 로깅 포함 |
| 보안 | ✅ PASS | 민감정보 마스킹 포함 |

## Project Structure

### Documentation (this feature)

```text
specs/002-backend-performance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── config/
│   │   └── constants.py          # DB 풀 크기 상수 수정
│   ├── utils/
│   │   ├── database.py           # 커넥션 풀 설정 수정
│   │   ├── cache.py              # [신규] TTLCache 구현
│   │   ├── retry.py              # [신규] 재시도 데코레이터
│   │   └── masking.py            # [신규] 민감정보 마스킹
│   ├── repositories/
│   │   └── config_repository.py  # 캐시 통합
│   ├── modules/
│   │   ├── health/
│   │   │   ├── routes.py         # 상세 헬스체크 엔드포인트
│   │   │   ├── service.py        # [신규] 헬스체크 서비스
│   │   │   └── schemas.py        # 상세 응답 스키마
│   │   └── config/
│   │       └── service.py        # 캐시 무효화 연동
│   ├── scheduler/
│   │   ├── jobs/
│   │   │   ├── data_collection.py    # 재시도 적용
│   │   │   └── signal_generation.py  # 재시도 적용
│   │   └── metrics.py            # [신규] 작업 메트릭 수집
│   └── clients/
│       └── ai/
│           └── gemini.py         # Rate Limit 재시도
└── tests/
    ├── unit/
    │   ├── test_cache.py         # [신규]
    │   ├── test_retry.py         # [신규]
    │   └── test_masking.py       # [신규]
    └── integration/
        └── test_health_detail.py # [신규]
```

**Structure Decision**: 기존 backend/ 구조 유지, utils/에 공통 유틸리티 추가

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | 모든 변경이 기존 구조 내에서 수행됨 | - |

---

## Phase 1: 즉시 적용 (P1)

### 1.1 DB 커넥션 풀 확장

**변경 파일**:
- `backend/src/config/constants.py:13-14`
- `backend/src/utils/database.py:23-24`

**변경 내용**:
```python
# constants.py
DB_POOL_SIZE = 10  # 기존 5
DB_POOL_MAX_OVERFLOW = 10  # 기존 10 유지 (총 20)
```

**테스트**: 동시 15개 세션 생성 테스트

### 1.2 인덱스 추가 (이미 완료 확인)

**현재 상태**: Order, TradingSignal, MarketData 테이블에 인덱스 이미 존재
- `idx_order_status`, `idx_order_created_desc`
- `idx_signal_created_desc`, `idx_signal_type_created`
- `idx_market_data_symbol_timestamp`

**추가 작업 없음** - 인덱스 존재 확인됨

### 1.3 트랜잭션 격리 레벨

**변경 파일**: `backend/src/utils/database.py`

**변경 내용**:
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_POOL_MAX_OVERFLOW,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",  # 추가
)
```

---

## Phase 2: 1주일 내 (P1)

### 2.1 TTL 캐시 구현

**신규 파일**: `backend/src/utils/cache.py`

```python
from typing import TypeVar, Generic, Callable, Awaitable
from datetime import datetime, timedelta
import asyncio

T = TypeVar("T")

class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[T, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get_or_set(
        self, key: str, factory: Callable[[], Awaitable[T]]
    ) -> T:
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if datetime.now() < expires_at:
                    self._hits += 1
                    return value

            self._misses += 1
            value = await factory()
            self._cache[key] = (value, datetime.now() + self._ttl)
            return value

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def stats(self) -> dict[str, int]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0,
        }
```

### 2.2 ConfigRepository 캐시 통합

**변경 파일**: `backend/src/repositories/config_repository.py`

**변경 내용**:
- `TTLCache` 인스턴스를 클래스 변수로 추가
- `get_value()` 메서드에 캐시 조회 우선
- `set_value()` 메서드에 캐시 무효화 추가

### 2.3 HTTP 클라이언트 정상 종료

**변경 파일**: `backend/src/app.py`

**변경 내용**: lifespan에서 모든 httpx 클라이언트 명시적 close() 호출

---

## Phase 3: 2주일 내 (P2-P3)

### 3.1 지수 백오프 재시도 데코레이터

**신규 파일**: `backend/src/utils/retry.py`

```python
import asyncio
from functools import wraps
from typing import Callable, TypeVar, ParamSpec
from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    delay = base_delay * (2 ** (attempt - 1))  # 1, 2, 4초
                    logger.warning(f"{func.__name__} attempt {attempt} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3.2 상세 헬스체크

**변경 파일**:
- `backend/src/modules/health/schemas.py` (스키마 확장)
- `backend/src/modules/health/service.py` (신규)
- `backend/src/modules/health/routes.py` (엔드포인트 추가)

**응답 스키마**:
```python
class ComponentHealth(BaseModel):
    name: str
    status: Literal["healthy", "unhealthy", "warning"]
    latency_ms: float | None = None
    message: str | None = None

class DetailedHealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy", "degraded"]
    timestamp: datetime
    version: str
    components: list[ComponentHealth]
```

**체크 대상 (6개)**:
1. DB 연결 (SELECT 1)
2. Upbit API (ping)
3. Gemini API (models list)
4. 스케줄러 상태
5. 최근 신호 (1시간 이내 존재 여부)
6. 최근 주문 (활성 주문 상태)

### 3.3 메트릭 수집 (JSON 로깅)

**신규 파일**: `backend/src/scheduler/metrics.py`

```python
from datetime import datetime
from loguru import logger
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def track_job(job_name: str):
    start = time.perf_counter()
    success = True
    error_msg = None
    try:
        yield
    except Exception as e:
        success = False
        error_msg = str(e)
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.bind(
            metric_type="job",
            job_name=job_name,
            duration_ms=round(duration_ms, 2),
            success=success,
            error=error_msg,
            timestamp=datetime.utcnow().isoformat(),
        ).info(f"Job {job_name} completed")
```

### 3.4 민감정보 마스킹

**신규 파일**: `backend/src/utils/masking.py`

```python
import re

SENSITIVE_PATTERNS = [
    (r'"balance":\s*"?[\d.]+"?', '"balance": "***"'),
    (r'"krw":\s*"?[\d.]+"?', '"krw": "***"'),
    (r'"btc":\s*"?[\d.]+"?', '"btc": "***"'),
    (r'(access_key|secret_key|api_key)["\']?\s*[:=]\s*["\']?[\w-]+', r'\1: ***'),
]

def mask_sensitive(text: str) -> str:
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result
```

---

## 테스트 계획

| 테스트 | 파일 | 검증 내용 |
|--------|------|----------|
| TTL 캐시 | test_cache.py | get_or_set, invalidate, stats, TTL 만료 |
| 재시도 | test_retry.py | 성공, 실패, 지수 백오프 |
| 마스킹 | test_masking.py | 잔고, API 키 마스킹 |
| 헬스체크 | test_health_detail.py | 6개 구성요소 응답 |
| 커넥션 풀 | test_database.py | 동시 15개 세션 |

---

## 배포 순서

1. **Phase 1**: 커넥션 풀 확장 + 격리 레벨 → 서비스 재시작
2. **Phase 2**: 캐시 모듈 추가 → 무중단 배포
3. **Phase 3**: 재시도 + 헬스체크 + 메트릭 → 무중단 배포

---

## 성공 기준 검증

| SC | 검증 방법 |
|----|----------|
| SC-001 | 동시 10개 DB 작업 테스트 통과 |
| SC-002 | 캐시 stats() 히트율 95%+ 확인 |
| SC-003 | EXPLAIN ANALYZE로 인덱스 사용 확인 (이미 완료) |
| SC-004 | 재시도 3회 후 성공률 90%+ 로그 확인 |
| SC-005 | /health/detail 응답에 6개 구성요소 포함 |
| SC-006 | JSON 로그에서 p95 계산 가능 |
| SC-007 | pytest --cov 80%+ 확인 |
