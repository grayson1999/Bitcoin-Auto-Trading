# Research: Backend Layered Architecture Refactoring

**Date**: 2026-01-21
**Feature**: [spec.md](./spec.md)

## 1. Repository 패턴 Best Practices

### Decision
Generic BaseRepository + 도메인별 Repository 상속 구조 사용

### Rationale
- SQLAlchemy 2.0 async session과 호환
- 공통 CRUD 메서드 재사용
- 도메인 특화 쿼리 메서드 추가 가능

### Alternatives Considered
| 대안 | 기각 사유 |
|------|----------|
| Repository 미적용 | 쿼리 중복, 테스트 어려움 |
| 단일 GenericRepository | 도메인 특화 쿼리 불가 |
| Django-style Manager | SQLAlchemy와 패턴 불일치 |

### Implementation Pattern
```python
class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100) -> list[T]:
        result = await self.session.execute(
            select(self.model).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
```

---

## 2. 설정 우선순위 구현

### Decision
ConfigService에서 DB → 환경변수 → 기본값 순서로 조회

### Rationale
- DB 설정으로 런타임 변경 가능
- 환경변수는 DB에 없을 때 fallback
- 민감 정보는 환경변수 전용

### Implementation Pattern
```python
class ConfigService:
    def __init__(self, config_repo: ConfigRepository, settings: Settings):
        self.config_repo = config_repo
        self.settings = settings

    async def get(self, key: str, default: Any = None) -> Any:
        # 1. DB에서 조회
        db_value = await self.config_repo.get_value(key)
        if db_value is not None:
            return db_value

        # 2. 환경변수에서 조회
        env_value = getattr(self.settings, key, None)
        if env_value is not None:
            return env_value

        # 3. 기본값 반환
        return default
```

### 민감 정보 분류
| 설정 | 저장 위치 | DB 저장 가능 |
|------|----------|-------------|
| API 키 (Upbit, Gemini, OpenAI) | 환경변수 전용 | X |
| DB URL | 환경변수 전용 | X |
| Slack Webhook URL | 환경변수 전용 | X |
| trading_enabled | DB 우선 | O |
| position_size_pct | DB 우선 | O |
| ai_model | DB 우선 | O |

---

## 3. 대형 파일 분할 전략

### Decision
책임 단위로 분할, 순환 의존성 방지

### order_executor.py (1,129줄) 분할

| 새 파일 | 책임 | 주요 클래스/함수 |
|---------|------|-----------------|
| `service.py` | 주문 실행 코어 | `OrderExecutor.execute()` |
| `order_validator.py` | 사전 검증 | `validate_balance()`, `validate_limits()` |
| `order_monitor.py` | 체결 모니터링 | `poll_order_status()`, `sync_pending_orders()` |

### signal_generator.py (790줄) 분할

| 새 파일 | 책임 | 주요 클래스/함수 |
|---------|------|-----------------|
| `service.py` | 신호 생성 코어 | `SignalGenerator.generate()` |
| `prompt_builder.py` | 프롬프트 구성 | `build_prompt()`, `format_market_data()` |
| `response_parser.py` | AI 응답 파싱 | `parse_signal()`, `extract_confidence()` |

### backtest_runner.py (792줄) 분할

| 새 파일 | 책임 | 주요 클래스/함수 |
|---------|------|-----------------|
| `engine.py` | 시뮬레이션 | `BacktestEngine.run()` |
| `reporter.py` | 결과 분석 | `generate_report()`, `calculate_metrics()` |

### upbit_client.py (741줄) 분할

| 새 파일 | 책임 | 주요 클래스/함수 |
|---------|------|-----------------|
| `public_api.py` | 공개 API | `get_ticker()`, `get_candles()` |
| `private_api.py` | 비공개 API | `place_order()`, `get_balance()` |

---

## 4. Import 경로 마이그레이션

### Decision
한번에 전환, 기존 경로 호환성 유지 안 함

### Rationale
- 점진적 마이그레이션은 중복 코드 발생
- IDE의 일괄 치환 기능 활용 가능
- 하루 내 완료 목표

### 주요 경로 변경

| 기존 경로 | 새 경로 |
|----------|--------|
| `from models.market_data import MarketData` | `from entities.market_data import MarketData` |
| `from services.upbit_client import UpbitClient` | `from clients.upbit import UpbitClient` |
| `from services.order_executor import OrderExecutor` | `from modules.trading.service import TradingService` |
| `from api.dashboard import router` | `from modules.market.routes import router` |
| `from config import settings` | `from config.settings import settings` |

---

## 5. 스케줄러 작업 분리

### Decision
도메인별 job 파일 분리, 스케줄러 초기화는 별도 파일

### Rationale
- 현재 jobs.py (530줄)에 모든 작업 혼재
- 도메인별 분리로 관련 코드 응집도 향상

### 분할 계획

| 새 파일 | 책임 | 기존 함수 |
|---------|------|----------|
| `data_collection.py` | 시세 수집 | `collect_market_data()` |
| `signal_generation.py` | AI 신호 생성 | `generate_signal()` |
| `order_sync.py` | 주문 동기화 | `sync_pending_orders()` |
| `cleanup.py` | 데이터 정리 | `cleanup_old_data()` |

---

## 6. 하드코딩 상수 분류

### constants.py로 이동
```python
# 거래소 제한
UPBIT_FEE_RATE = 0.0005
UPBIT_MIN_ORDER_KRW = 5000
UPBIT_RATE_LIMIT_ORDER = 10
UPBIT_RATE_LIMIT_QUERY = 30

# 재시도 설정
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 2
DEFAULT_TIMEOUT_SECONDS = 30

# AI 모델 비용
AI_MODEL_COSTS = {
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}

# 로깅
LOG_ROTATION_SIZE = "10MB"
LOG_RETENTION_DAYS = 7
```

### 환경변수로 이동 (스케줄러 주기)
```python
# settings.py
data_collection_interval_seconds: int = 10
signal_interval_hours: int = 1
data_cleanup_interval_hours: int = 24
```

---

## 7. Ruff 규칙 강화

### Decision
기존 규칙 유지 + 보안/단순화 규칙 추가

### 추가 규칙
```toml
[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "B", "C4", "UP",  # 기존
    "S",      # flake8-bandit (보안)
    "SIM",    # flake8-simplify (단순화)
    "RUF",    # Ruff 전용
]
ignore = [
    "E501",   # line too long
    "S101",   # assert 허용 (테스트)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]
```
