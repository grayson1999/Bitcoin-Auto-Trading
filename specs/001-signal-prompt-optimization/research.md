# Research: AI 신호 프롬프트 최적화

**Date**: 2026-01-24
**Branch**: `001-signal-prompt-optimization`

---

## 1. 신호 주기 변경 (hours → minutes)

### 현재 상태

```python
# settings.py:93-98
signal_interval_hours: int = Field(
    default=1,
    ge=1,
    le=4,
    description="AI 신호 생성 주기 (1-4시간)"
)
```

### 문제점

- 정수 타입으로 1시간 미만 설정 불가
- 30분 주기를 지원할 수 없음

### 해결 방안

**Decision**: `signal_interval_hours` → `signal_interval_minutes` 변경

```python
signal_interval_minutes: int = Field(
    default=30,
    ge=5,
    le=120,
    description="AI 신호 생성 주기 (5-120분)"
)
```

**Rationale**:
- 분 단위로 더 세밀한 제어 가능
- 5분 ~ 2시간 범위로 유연성 확보
- DB_OVERRIDABLE_KEYS도 업데이트 필요

**Alternatives considered**:
- float 타입으로 0.5시간 허용 → 직관성 떨어짐, 기각

---

## 2. 시장 데이터 샘플링 전략

### 현재 상태

```python
# constants.py:72
SIGNAL_MARKET_DATA_HOURS = 168  # 7일

# service.py:252-253
.limit(1000)  # 최대 1000개 전체 로드
```

10초마다 데이터 수집 → 1시간에 360개, 하루 8,640개
프롬프트에 1000개 전체 전달 → 토큰 낭비

### 해결 방안

**Decision**: 시간대별 샘플링 적용

| 시간대 | 기간 | 샘플링 간격 | 예상 데이터 수 |
|--------|------|:-----------:|:--------------:|
| 장기 | 14일 | 1시간 | ~336개 |
| 중기 | 24시간 | 15분 | ~96개 |
| 단기 | 1시간 | 5분 | ~12개 |
| **합계** | | | **~450개** |

**Rationale**:
- 장기 추세 파악에는 세밀한 데이터 불필요
- 최근 데이터는 더 촘촘하게 유지
- 55% 데이터 절감으로 토큰 사용량 감소

**Implementation approach**:
- DB 쿼리: 최근 14일 데이터 전체 조회
- Python 후처리: 시간대별로 샘플링
- 이유: SQL time_bucket보다 유연, 테스트 용이

**샘플링 알고리즘**:
```python
def sample_by_interval(data: list, interval_min: int) -> list:
    """interval_min 간격으로 데이터 추출"""
    result = []
    last_time = None
    for item in sorted(data, key=lambda x: x.timestamp):
        if last_time is None or (item.timestamp - last_time).total_seconds() >= interval_min * 60:
            result.append(item)
            last_time = item.timestamp
    return result
```

---

## 3. 성과 피드백 제거

### 현재 상태

```python
# service.py:159-165
perf_tracker = SignalPerformanceTracker(self.db)
perf_summary = await perf_tracker.generate_performance_summary(limit=30)

# builder.py:84
performance_feedback = self._format_performance_feedback(perf_summary)
```

- 매번 30개 신호 성과 분석
- 프롬프트에 약 500 토큰 추가

### 해결 방안

**Decision**: 프롬프트에서 성과 피드백 완전 제거

**Rationale**:
- 대시보드에서 동일 정보 확인 가능 (`/api/v1/dashboard/summary`)
- 약 500 토큰 절감
- AI가 과거 성과에 과의존하는 것 방지

**제거 대상**:
1. `service.py`: perf_tracker 호출 제거
2. `builder.py`: `_format_performance_feedback()` 제거
3. `templates.py`: 성과 피드백 섹션 제거

**유지 대상**:
- `SignalPerformanceTracker` 클래스 자체는 유지 (별도 분석용)
- `evaluate_signal_performance_job` 제거 검토 (선택적)

---

## 4. 신뢰도 계산 공식

### 현재 문제

- AI가 조건 불명확 시 기본값 0.5 출력
- 시스템 프롬프트의 신뢰도 기준이 모호

### 해결 방안

**Decision**: 명시적 계산 공식 프롬프트에 포함

```text
신뢰도 = base + tf_bonus + indicator_bonus

기본값 (base):
- 손절 조건 충족: 0.9
- 익절 조건 충족: 0.85
- 매수 조건 충족: 0.6
- HOLD: 0.5

TF 보너스 (같은 방향 타임프레임 수):
- 4개 일치: +0.15
- 3개 일치: +0.10
- 2개 일치: +0.05
- 1개 일치: +0.00

지표 보너스:
- RSI 과매도/과매수 극단: +0.05
- MACD + BB 신호 일치: +0.05

최종값 = min(1.0, 계산값)
```

**Rationale**:
- 명확한 공식으로 AI 혼란 감소
- 일관된 신뢰도 출력 유도
- 0.5 고정 출력 비율 감소 예상

---

## 5. 프롬프트 압축 전략

### 시스템 프롬프트 압축 (3,500 → 1,500 토큰)

**현재 문제**:
- 손절 규칙 3번 반복
- 포지션별 상세 테이블 과다
- 신뢰도 기준표 중복

**압축 방안**:
```markdown
당신은 {currency} 단기 트레이딩 AI입니다.

## 전략 특성
- **30분 주기** 신호 생성 → 공격적 단기 매매
- 빠른 진입/청산 우선, 장기 보유 지양

## 핵심 규칙 (우선순위 순)
1. 손절: 미실현 손실 >= {stop_loss}% → SELL (신뢰도 0.9)
2. 익절: 미실현 이익 >= {take_profit}% AND 하락 신호 → SELL
3. 매수: Confluence >= {min_confluence} AND RSI < {rsi_overbought} → BUY
4. 기타 → HOLD

## 신뢰도 계산
[위 공식 포함]

## 출력 (JSON만)
{"signal": "BUY|HOLD|SELL", "confidence": 0.0~1.0, "reasoning": "..."}
```

### 분석 프롬프트 압축 (6,000 → 2,500 토큰)

**제거**:
- 성과 피드백 섹션 (~500 토큰)
- 샘플링으로 시장 데이터 축소 (~2,000 토큰 → ~500 토큰)

**유지**:
- 현재가/변동률
- 포지션 정보
- 기술적 지표 (1D 기준)
- MTF 분석 요약

---

## 6. 예상 효과

| 항목 | 현재 | 최적화 후 | 개선율 |
|------|:----:|:---------:|:------:|
| 신호 생성 주기 | 1시간 (24회/일) | 30분 (48회/일) | 2배 빈번 |
| 입력 토큰 | ~10,000 | ~4,000 | 60%↓ |
| 비용/회 (Gemini) | ₩20 | ₩8 | 60%↓ |
| 일일 비용 | ₩480 (24회) | ₩384 (48회) | 20%↓ |
| 응답 시간 | 5-8초 | 2-4초 | 50%↓ |
| 시장 데이터 | 1000개 | ~450개 | 55%↓ |

---

## 7. 리스크 및 완화 방안

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 프롬프트 압축으로 AI 정확도 저하 | 중간 | A/B 테스트로 검증 후 배포 |
| 샘플링으로 중요 데이터 누락 | 낮음 | 단기 데이터는 5분 간격으로 촘촘하게 유지 |
| 30분 주기로 API 비용 증가 | 낮음 | 토큰 60% 절감으로 상쇄 |
| 신뢰도 공식이 AI에 과부하 | 낮음 | 간단한 산술 연산만 요구 |

---

## 8. 결론

모든 NEEDS CLARIFICATION 항목이 해결되었습니다. Phase 1 설계로 진행 가능합니다.
