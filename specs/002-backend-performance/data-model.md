# Data Model: Backend 성능 최적화

**Date**: 2026-01-24 | **Branch**: `002-backend-performance`

## 신규 엔티티

이 기능은 새로운 DB 엔티티를 추가하지 않습니다. 기존 엔티티를 활용합니다.

---

## 인메모리 구조

### TTLCache[T]

**목적**: 설정값 캐싱

```python
class TTLCache(Generic[T]):
    _cache: dict[str, tuple[T, datetime]]  # key → (value, expires_at)
    _ttl: timedelta                         # 만료 시간 (1시간)
    _lock: asyncio.Lock                     # 동시성 제어
    _hits: int                              # 캐시 히트 카운트
    _misses: int                            # 캐시 미스 카운트
```

**메서드**:
| 메서드 | 시그니처 | 설명 |
|--------|----------|------|
| get_or_set | `(key, factory) → T` | 캐시 조회 또는 팩토리 호출 |
| invalidate | `(key?) → None` | 키 또는 전체 무효화 |
| stats | `() → dict` | 히트율 통계 반환 |

---

### ComponentHealth

**목적**: 헬스체크 구성요소 상태

```python
class ComponentHealth(BaseModel):
    name: str                                      # 구성요소 이름
    status: Literal["healthy", "unhealthy", "warning"]
    latency_ms: float | None                       # 응답 시간 (ms)
    message: str | None                            # 상태 메시지
```

---

### DetailedHealthResponse

**목적**: 상세 헬스체크 API 응답

```python
class DetailedHealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy", "degraded"]
    timestamp: datetime
    version: str
    components: list[ComponentHealth]              # 6개 구성요소
```

**구성요소 목록**:
1. `database` - PostgreSQL 연결 상태
2. `upbit_api` - Upbit 거래소 API
3. `gemini_api` - Google Gemini AI API
4. `scheduler` - APScheduler 상태
5. `recent_signal` - 최근 1시간 내 신호 존재
6. `recent_order` - 최근 활성 주문 상태

---

### JobMetric (로그 기반)

**목적**: 스케줄러 작업 메트릭

```json
{
  "metric_type": "job",
  "job_name": "collect_market_data",
  "duration_ms": 123.45,
  "success": true,
  "error": null,
  "timestamp": "2026-01-24T10:00:00Z"
}
```

**수집 대상 작업**:
| 작업 ID | 주기 |
|---------|------|
| collect_market_data | 10초 |
| generate_trading_signal | 30분 |
| check_volatility | 30초 |
| sync_pending_orders | 5분 |
| cleanup_old_data | 24시간 |

---

## 기존 엔티티 (변경 없음)

### SystemConfig

설정값 저장 테이블 - 캐시와 연동

```python
class SystemConfig(Base):
    id: int
    key: str           # UNIQUE
    value: str
    description: str | None
    created_at: datetime
    updated_at: datetime
```

**캐시 연동**:
- `get_value()` 호출 시 TTLCache 먼저 조회
- `set_value()` 호출 시 TTLCache 무효화

---

## 상태 다이어그램

### 캐시 상태 전이

```
┌─────────┐   get_or_set (miss)   ┌─────────┐
│  EMPTY  │ ───────────────────→  │ CACHED  │
└─────────┘                       └─────────┘
                                       │
                                       │ TTL 만료 또는
                                       │ invalidate() 호출
                                       ▼
                                  ┌─────────┐
                                  │ EXPIRED │
                                  └─────────┘
                                       │
                                       │ get_or_set (miss)
                                       ▼
                                  ┌─────────┐
                                  │ CACHED  │
                                  └─────────┘
```

### 헬스체크 상태 결정

```
All components healthy → status: "healthy"
Any component unhealthy → status: "unhealthy"
Any component warning (none unhealthy) → status: "degraded"
```

---

## 검증 규칙

| 항목 | 규칙 |
|------|------|
| TTL | 3600초 (1시간) 고정 |
| 캐시 키 | 설정 키 이름 (예: "stop_loss_pct") |
| latency_ms | 0 이상, 타임아웃 시 null |
| job_name | 등록된 스케줄러 작업 ID |
| duration_ms | 0 이상, 소수점 2자리 |
