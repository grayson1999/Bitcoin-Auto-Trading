# Data Model: AI 신호 프롬프트 최적화

**Date**: 2026-01-24
**Branch**: `001-signal-prompt-optimization`

---

## Overview

이 기능은 기존 데이터 모델을 변경하지 않습니다. 설정값과 로직만 변경됩니다.

---

## Configuration Changes

### 1. settings.py 변경

**Before**:
```python
signal_interval_hours: int = Field(
    default=1,
    ge=1,
    le=4,
    description="AI 신호 생성 주기 (1-4시간)"
)
```

**After**:
```python
signal_interval_minutes: int = Field(
    default=30,
    ge=5,
    le=120,
    description="AI 신호 생성 주기 (5-120분) [DB 오버라이드 가능]"
)
```

### 2. constants.py 추가

```python
# 시장 데이터 샘플링 설정
SAMPLING_CONFIG = {
    "long_term": {
        "hours": 336,        # 14일
        "interval_min": 60,  # 1시간 간격
    },
    "mid_term": {
        "hours": 24,         # 1일
        "interval_min": 15,  # 15분 간격
    },
    "short_term": {
        "hours": 1,          # 1시간
        "interval_min": 5,   # 5분 간격
    },
}
```

### 3. DB_OVERRIDABLE_KEYS 업데이트

```python
DB_OVERRIDABLE_KEYS = frozenset({
    "position_size_min_pct",
    "position_size_max_pct",
    "stop_loss_pct",
    "daily_loss_limit_pct",
    "signal_interval_minutes",  # 변경: hours → minutes
    "volatility_threshold_pct",
    "ai_model",
})
```

---

## Existing Entities (No Changes)

### TradingSignal

```python
class TradingSignal(Base, TimestampMixin):
    """AI 매매 신호 엔티티"""
    id: int
    market_data_id: int
    signal_type: SignalType  # BUY, HOLD, SELL
    confidence: Decimal
    reasoning: str
    model_name: str
    input_tokens: int
    output_tokens: int
    price_at_signal: Decimal
    technical_snapshot: str  # JSON
    created_at: datetime
```

### MarketData

```python
class MarketData(Base):
    """시장 데이터 엔티티"""
    id: int
    ticker: str
    price: Decimal
    volume: Decimal
    timestamp: datetime
```

---

## New Module: MarketDataSampler

```python
# modules/signal/sampler.py

from datetime import datetime, timedelta
from src.entities import MarketData
from src.config.constants import SAMPLING_CONFIG

class MarketDataSampler:
    """
    시간대별 시장 데이터 샘플링

    10초 간격으로 수집된 데이터를 시간대별로 다른 간격으로 샘플링하여
    AI 프롬프트에 필요한 최소한의 데이터만 추출합니다.
    """

    def __init__(self, config: dict = None):
        self.config = config or SAMPLING_CONFIG

    def sample_by_interval(
        self,
        data: list[MarketData],
        interval_minutes: int
    ) -> list[MarketData]:
        """
        주어진 간격으로 데이터 샘플링

        Args:
            data: 시장 데이터 목록 (timestamp 내림차순 정렬)
            interval_minutes: 샘플링 간격 (분)

        Returns:
            샘플링된 데이터 목록
        """
        pass

    def get_sampled_data(
        self,
        data: list[MarketData],
        now: datetime = None
    ) -> dict[str, list[MarketData]]:
        """
        장기/중기/단기별 샘플링된 데이터 반환

        Args:
            data: 전체 시장 데이터 목록
            now: 현재 시간 (테스트용)

        Returns:
            {
                "long_term": [...],   # 14일, 1시간 간격
                "mid_term": [...],    # 24시간, 15분 간격
                "short_term": [...],  # 1시간, 5분 간격
            }
        """
        pass

    def get_total_count(self, sampled: dict) -> int:
        """샘플링된 총 데이터 개수 반환"""
        return sum(len(v) for v in sampled.values())
```

---

## Data Flow

### Before (현재)

```
MarketData (1000개) → service.py → builder.py → AI 프롬프트
                        ↓
              perf_tracker.generate_performance_summary()
```

### After (최적화 후)

```
MarketData (전체) → MarketDataSampler → 샘플링된 데이터 (~450개)
                                              ↓
                                    service.py → builder.py → AI 프롬프트
                                    (성과 피드백 제거)
```

---

## Validation Rules

1. **signal_interval_minutes**:
   - 최소: 5분
   - 최대: 120분 (2시간)
   - 기본값: 30분

2. **샘플링 데이터**:
   - 장기: 최소 24개 (1일치)
   - 중기: 최소 4개 (1시간치)
   - 단기: 최소 1개 (현재가)

3. **토큰 제한**:
   - 입력 토큰: 4,000개 이하
   - 출력 토큰: 1,024개 이하 (기존 유지)

---

## Migration Notes

### system_config 테이블 업데이트

기존 `signal_interval_hours` 레코드가 있다면:
1. 새 `signal_interval_minutes` 레코드 추가 (value = old_value * 60)
2. 구 레코드는 삭제하거나 무시 (코드에서 더 이상 참조하지 않음)

### 롤백 시

1. `signal_interval_minutes` → `signal_interval_hours` 복원
2. DB_OVERRIDABLE_KEYS 원복
3. system_config 테이블에서 minutes 레코드 삭제
