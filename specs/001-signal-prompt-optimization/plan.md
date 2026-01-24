# Implementation Plan: AI 신호 프롬프트 최적화

**Branch**: `001-signal-prompt-optimization` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-signal-prompt-optimization/spec.md`

## Summary

AI 매매 신호 생성 시스템의 효율성을 개선하기 위해:
1. 신호 생성 주기를 1시간에서 30분으로 변경
2. 시장 데이터를 시간대별로 샘플링하여 토큰 사용량 감소
3. 성과 피드백 섹션을 프롬프트에서 제거
4. 신뢰도 계산 공식을 명시화하여 정확도 향상

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, APScheduler 3.10, google-genai
**Storage**: PostgreSQL 15 (asyncpg)
**Testing**: pytest
**Target Platform**: Linux server (systemd)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: AI 응답 2-4초, 입력 토큰 4,000개 이하
**Constraints**: 일일 비용 ₩480 이하 유지, 하루 48회 신호 생성
**Scale/Scope**: 단일 사용자, 1개 거래쌍 (SOL/KRW)

## Constitution Check

*GATE: Must pass before Phase 0 research.*

프로젝트에 별도의 Constitution이 정의되지 않았으므로 일반적인 소프트웨어 개발 원칙을 적용합니다:
- [x] 기존 코드 패턴 준수
- [x] 단일 책임 원칙
- [x] 테스트 가능한 변경
- [x] 점진적 변경 (롤백 가능)

## Project Structure

### Documentation (this feature)

```text
specs/001-signal-prompt-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - internal changes)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── config/
│   │   ├── settings.py      # 신호 주기 설정 변경 (hours → minutes)
│   │   └── constants.py     # 샘플링 설정 추가
│   │
│   ├── modules/signal/
│   │   ├── service.py       # 샘플링 로직 적용, 성과 피드백 제거
│   │   ├── prompt/
│   │   │   ├── builder.py   # 성과 피드백 메서드 제거
│   │   │   └── templates.py # 프롬프트 압축, 신뢰도 공식 추가
│   │   └── sampler.py       # [NEW] 시장 데이터 샘플링 모듈
│   │
│   └── scheduler/
│       └── scheduler.py     # IntervalTrigger(minutes=) 변경
│
└── tests/
    └── unit/
        └── signal/
            └── test_sampler.py  # [NEW] 샘플링 테스트
```

**Structure Decision**: 기존 backend/ 구조 유지, signal 모듈 내에 sampler.py 추가

## Complexity Tracking

현재 Constitution 위반 사항 없음.

---

## Phase 0: Research (완료)

### 1. 신호 주기 변경 방식

**Decision**: `signal_interval_hours` → `signal_interval_minutes` 변경
**Rationale**:
- 기존 `signal_interval_hours`는 정수 타입으로 1-4시간만 허용
- 30분 주기를 지원하려면 분 단위 설정 필요
- DB_OVERRIDABLE_KEYS 업데이트 필요

**Alternatives considered**:
- float 타입으로 0.5시간 허용 → 직관성 떨어짐
- signal_interval_minutes 신규 추가 → 채택

### 2. 시장 데이터 샘플링 전략

**Decision**: 시간대별 샘플링 (장기/중기/단기)
**Rationale**:
- 장기 (14일, 1시간 간격): 추세 파악용 ~336개
- 중기 (24시간, 15분 간격): 변동성 분석용 ~96개
- 단기 (1시간, 5분 간격): 최근 가격용 ~12개
- 총 ~450개로 기존 1000개 대비 55% 감소

**Implementation approach**:
- Python 후처리 방식: DB에서 전체 조회 후 메모리에서 샘플링
- 이유: SQL time_bucket 함수보다 유연하고 테스트 용이

### 3. 성과 피드백 제거

**Decision**: 프롬프트에서 완전 제거
**Rationale**:
- 대시보드에서 동일 정보 확인 가능
- 약 500 토큰 절감
- SignalPerformanceTracker는 별도 분석용으로 유지 (job만 제거 검토)

### 4. 신뢰도 계산 공식

**Decision**: AI 프롬프트에 명시적 공식 포함
**Rationale**:
- 현재 AI가 조건 불명확 시 0.5 기본값 출력
- 공식 명시로 일관된 신뢰도 계산 유도

---

## Phase 1: Design

### Data Model Changes

기존 엔티티 변경 없음. 설정값만 변경:

```python
# config/settings.py - 변경 사항
signal_interval_minutes: int = Field(
    default=30,
    ge=5,
    le=120,
    description="AI 신호 생성 주기 (5-120분) [DB 오버라이드 가능]",
)

# config/constants.py - 추가 사항
SAMPLING_CONFIG = {
    "long_term": {"hours": 336, "interval_min": 60},   # 14일, 1시간
    "mid_term": {"hours": 24, "interval_min": 15},     # 1일, 15분
    "short_term": {"hours": 1, "interval_min": 5},     # 1시간, 5분
}
```

### New Module: sampler.py

```python
# modules/signal/sampler.py
class MarketDataSampler:
    """시간대별 시장 데이터 샘플링"""

    def sample_by_interval(
        self,
        data: list[MarketData],
        interval_minutes: int
    ) -> list[MarketData]:
        """주어진 간격으로 데이터 샘플링"""

    def get_sampled_data(
        self,
        data: list[MarketData]
    ) -> dict[str, list[MarketData]]:
        """장기/중기/단기별 샘플링된 데이터 반환"""
```

### Prompt Template Changes

1. **시스템 프롬프트 압축**: 3,500 → 1,500 토큰
   - 중복 규칙 제거
   - 30분 주기 공격적 트레이딩 명시
   - 신뢰도 계산 공식 명시

2. **분석 프롬프트 압축**: 6,000 → 2,500 토큰
   - 성과 피드백 섹션 제거
   - 샘플링된 데이터만 포함
   - 핵심 지표 요약 형식

### API Contracts

내부 변경이므로 API 변경 없음. 기존 `/api/v1/signals` 엔드포인트 유지.

---

## Implementation Tasks Preview

### 1단계: 설정 변경 (신호 주기)
- `settings.py`: signal_interval_hours → signal_interval_minutes
- `scheduler.py`: IntervalTrigger(minutes=)
- DB_OVERRIDABLE_KEYS 업데이트

### 2단계: 시장 데이터 샘플링
- `constants.py`: SAMPLING_CONFIG 추가
- `sampler.py`: MarketDataSampler 클래스 구현
- `service.py`: 샘플링 로직 적용

### 3단계: 성과 피드백 제거
- `service.py`: perf_tracker 호출 제거
- `builder.py`: performance_feedback 제거
- `templates.py`: 프롬프트에서 섹션 제거
- `scheduler.py`: evaluate_signal_performance_job 제거 검토

### 4단계: 프롬프트 최적화
- `templates.py`: 시스템 프롬프트 압축
- `templates.py`: 분석 프롬프트 압축
- `templates.py`: 신뢰도 계산 공식 추가

### 5단계: 테스트 및 검증
- 샘플링 단위 테스트
- 토큰 사용량 측정
- 신호 생성 통합 테스트

---

## Files to Modify

| File | Changes | Priority |
|------|---------|:--------:|
| `backend/src/config/settings.py` | signal_interval_minutes 추가 | **P1** |
| `backend/src/config/constants.py` | SAMPLING_CONFIG 추가 | **P1** |
| `backend/src/scheduler/scheduler.py` | IntervalTrigger(minutes=) | **P1** |
| `backend/src/modules/signal/sampler.py` | **[NEW]** 샘플링 모듈 | **P1** |
| `backend/src/modules/signal/service.py` | 샘플링 적용, 성과 피드백 제거 | **P1** |
| `backend/src/modules/signal/prompt/builder.py` | performance_feedback 제거 | **P2** |
| `backend/src/modules/signal/prompt/templates.py` | 프롬프트 압축, 신뢰도 공식 | **P2** |
| `backend/tests/unit/signal/test_sampler.py` | **[NEW]** 샘플링 테스트 | **P2** |

---

## Rollback Plan

1. 기존 파일 백업 (Git 브랜치로 관리)
2. 문제 발생 시 `develop` 브랜치로 복귀
3. 설정값 롤백: signal_interval_minutes → signal_interval_hours

---

## Next Steps

Phase 2 (Tasks Generation)는 `/speckit.tasks` 명령으로 진행합니다.
