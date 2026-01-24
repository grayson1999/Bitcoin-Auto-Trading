# Quickstart: Backend 성능 최적화

**Branch**: `002-backend-performance`

## 전제 조건

- Python 3.11+
- PostgreSQL 15 (Docker 또는 로컬)
- 기존 `.env` 파일 설정 완료

## 빠른 시작

```bash
# 1. 브랜치 전환
git checkout 002-backend-performance

# 2. 의존성 설치 (변경 없음)
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 3. 서비스 재시작 (커넥션 풀 변경 적용)
sudo systemctl restart bitcoin-backend

# 4. 헬스체크 확인
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/detail  # 상세 헬스체크
```

## 변경된 설정값

| 항목 | 이전 | 이후 |
|------|------|------|
| DB_POOL_SIZE | 5 | 10 |
| DB_POOL_MAX_OVERFLOW | 10 | 10 |
| isolation_level | (기본값) | READ COMMITTED |

## 새로운 API 엔드포인트

### GET /api/v1/health/detail

상세 헬스체크 - 6개 구성요소 상태 반환

```bash
curl -s http://localhost:8000/api/v1/health/detail | jq
```

**응답 예시**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T10:00:00Z",
  "version": "0.1.0",
  "components": [
    {"name": "database", "status": "healthy", "latency_ms": 1.2},
    {"name": "upbit_api", "status": "healthy", "latency_ms": 45.3},
    {"name": "gemini_api", "status": "healthy", "latency_ms": 120.5},
    {"name": "scheduler", "status": "healthy"},
    {"name": "recent_signal", "status": "healthy", "message": "Last signal 15m ago"},
    {"name": "recent_order", "status": "healthy", "message": "No pending orders"}
  ]
}
```

## 캐시 통계 확인

로그에서 캐시 히트율 확인:

```bash
journalctl -u bitcoin-backend -f | grep "cache"
```

## 메트릭 로그 확인

JSON 메트릭 로그 필터링:

```bash
journalctl -u bitcoin-backend -f | grep '"metric_type":"job"'
```

**예시 출력**:
```json
{"metric_type":"job","job_name":"collect_market_data","duration_ms":23.45,"success":true}
```

## 테스트 실행

```bash
cd backend

# 전체 테스트
pytest

# 새로운 테스트만
pytest tests/unit/test_cache.py
pytest tests/unit/test_retry.py
pytest tests/unit/test_masking.py
pytest tests/integration/test_health_detail.py

# 커버리지 확인
pytest --cov=src --cov-report=term-missing
```

## 트러블슈팅

### 커넥션 풀 고갈

```bash
# PostgreSQL 연결 수 확인
PGPASSWORD=trading psql -h localhost -U trading -d bitcoin -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='bitcoin';"
```

### 캐시 무효화 강제

```python
# Python REPL에서
from src.repositories.config_repository import ConfigRepository
ConfigRepository._cache.invalidate()
```

### 헬스체크 실패 시

```bash
# 개별 구성요소 확인
curl -s http://localhost:8000/api/v1/health/detail | jq '.components[] | select(.status != "healthy")'
```
