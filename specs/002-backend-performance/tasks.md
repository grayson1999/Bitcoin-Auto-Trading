# Tasks: Backend 성능 최적화

**Input**: Design documents from `/specs/002-backend-performance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`

---

## Phase 1: Setup

**Purpose**: 공통 유틸리티 모듈 생성

- [X] T001 [P] Create TTLCache class in backend/src/utils/cache.py
- [X] T002 [P] Create retry decorator in backend/src/utils/retry.py
- [X] T003 [P] Add balance masking patterns to backend/src/config/logging.py (기존 mask_sensitive_data 확장)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB 설정 변경 (모든 스토리에 영향)

**⚠️ CRITICAL**: 이 Phase 완료 후 서비스 재시작 필요

- [X] T004 Update DB_POOL_SIZE to 10 in backend/src/config/constants.py
- [X] T005 Add isolation_level="READ COMMITTED" to engine in backend/src/utils/database.py
- [X] T006 Verify existing indexes on Order, TradingSignal, MarketData tables (READ-ONLY verification)

**Checkpoint**: DB 설정 완료 - 서비스 재시작 후 User Story 구현 시작

---

## Phase 3: User Story 1 - 동시 작업 안정성 향상 (Priority: P1) 🎯 MVP

**Goal**: DB 커넥션 풀 확장으로 동시 10개 이상 작업 처리

**Independent Test**: 동시 15개 세션 생성 테스트 통과

### Tests for User Story 1

- [X] T007 [P] [US1] Create concurrent session test in backend/tests/unit/test_database_pool.py

### Implementation for User Story 1

- [X] T008 [US1] Verify pool size change effective by checking engine.pool.size() in backend/src/utils/database.py

**Checkpoint**: 동시 DB 작업 테스트 통과 확인

---

## Phase 4: User Story 2 - 설정값 조회 성능 개선 (Priority: P1)

**Goal**: TTL 1시간 캐시로 설정값 조회 DB 부하 95% 감소

**Independent Test**: 캐시 히트율 95% 이상 달성

### Tests for User Story 2

- [X] T009 [P] [US2] Create TTLCache unit tests in backend/tests/unit/test_cache.py

### Implementation for User Story 2

- [X] T010 [US2] Add TTLCache instance to ConfigRepository in backend/src/repositories/config_repository.py
- [X] T011 [US2] Integrate cache in get_value() method in backend/src/repositories/config_repository.py
- [X] T012 [US2] Add cache invalidation in set_value() method in backend/src/repositories/config_repository.py
- [X] T013 [US2] Update ConfigService to use cached repository in backend/src/modules/config/service.py

**Checkpoint**: 설정값 조회 시 캐시 히트율 95%+ 확인

---

## Phase 5: User Story 3 - 데이터베이스 쿼리 성능 개선 (Priority: P1)

**Goal**: 인덱스 활용으로 쿼리 성능 20% 이상 개선

**Independent Test**: EXPLAIN ANALYZE로 인덱스 스캔 확인

### Implementation for User Story 3

- [X] T014 [US3] Document existing indexes in research.md for verification (READ-ONLY)
- [X] T015 [US3] Run EXPLAIN ANALYZE on order queries to verify index usage

**Checkpoint**: 인덱스 스캔 사용 확인 ✓ (TradingSignal, MarketData: Index Scan 확인)

---

## Phase 6: User Story 4 - 스케줄러 에러 복구 (Priority: P2)

**Goal**: 지수 백오프 재시도(3회, 1초→2초→4초)로 일시적 오류 자동 복구

**Independent Test**: Rate Limit 시뮬레이션 후 재시도 성공

### Tests for User Story 4

- [X] T016 [P] [US4] Create retry decorator tests in backend/tests/unit/test_retry.py

### Implementation for User Story 4

- [X] T017 [US4] Apply @with_retry to collect_market_data_job in backend/src/scheduler/jobs/data_collection.py
- [X] T018 [US4] Apply @with_retry to generate_trading_signal_job in backend/src/scheduler/jobs/signal_generation.py
- [X] T019 [US4] Add Rate Limit handling to Gemini client in backend/src/clients/ai/gemini_client.py

**Checkpoint**: 재시도 로직 적용 완료 ✓ (13개 테스트 통과, 지수 백오프 1s→2s→4s)

---

## Phase 7: User Story 5 - 시스템 상태 상세 모니터링 (Priority: P2)

**Goal**: 6개 구성요소 상태 보고하는 상세 헬스체크 API

**Independent Test**: GET /api/v1/health/detail 호출 시 6개 구성요소 반환

### Tests for User Story 5

- [X] T020 [P] [US5] Create health detail integration test in backend/tests/integration/test_health_detail.py

### Implementation for User Story 5

- [X] T021 [P] [US5] Add ComponentHealth, DetailedHealthResponse schemas in backend/src/modules/health/schemas.py
- [X] T022 [US5] Create HealthService with 6 component checks in backend/src/modules/health/service.py
- [X] T023 [US5] Add /health/detail endpoint in backend/src/modules/health/routes.py

**Checkpoint**: /health/detail API 응답에 6개 구성요소 포함 확인 ✓ (11개 테스트 통과)

---

## Phase 8: User Story 6 - 메트릭 수집 및 모니터링 (Priority: P3)

**Goal**: 구조화된 JSON 로그로 작업별 실행 시간, 성공률 수집

**Independent Test**: 로그에서 metric_type="job" 필터링 가능

### Implementation for User Story 6

- [X] T024 [P] [US6] Create track_job context manager in backend/src/scheduler/metrics.py
- [X] T025 [US6] Apply track_job to data_collection job in backend/src/scheduler/jobs/data_collection.py
- [X] T026 [US6] Apply track_job to signal_generation job in backend/src/scheduler/jobs/signal_generation.py
- [X] T027 [US6] Apply track_job to volatility_check job in backend/src/scheduler/jobs/signal_generation.py
- [X] T028 [US6] Apply track_job to order_sync job in backend/src/scheduler/jobs/order_sync.py

**Checkpoint**: journalctl에서 JSON 메트릭 로그 확인 ✓ (track_job 컨텍스트 매니저 적용 완료)

---

## Phase 9: User Story 7 - 코드 품질 및 유지보수성 개선 (Priority: P3)

**Goal**: 민감정보 마스킹, 에러 로깅 강화

**Independent Test**: 로그에 잔고, API 키 노출되지 않음

### Tests for User Story 7

- [X] T029 [P] [US7] Create masking utility tests in backend/tests/unit/test_masking.py

### Implementation for User Story 7

- [X] T030 [US7] Apply mask_sensitive to prompt logging in backend/src/modules/signal/service.py
- [X] T031 [US7] Add HTTP client cleanup in lifespan in backend/src/app.py
- [X] T032 [US7] Review and add warning logs for silent failures

**Checkpoint**: 민감정보 마스킹 테스트 통과 ✓ (27개 테스트 통과, HTTP 클라이언트 cleanup 추가)

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 최종 검증 및 문서화

- [ ] T033 Run full test suite with coverage (pytest --cov=src)
- [ ] T034 Verify test coverage >= 80%
- [ ] T035 Run quickstart.md validation
- [ ] T036 Update CLAUDE.md if needed

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → [서비스 재시작]
                                          ↓
                    ┌──────────────────────┼──────────────────────┐
                    ↓                      ↓                      ↓
              Phase 3 (US1)          Phase 4 (US2)          Phase 5 (US3)
                    ↓                      ↓                      ↓
              Phase 6 (US4)          Phase 7 (US5)          Phase 8 (US6)
                    ↓                      ↓                      ↓
                    └──────────────────────┼──────────────────────┘
                                          ↓
                                    Phase 9 (US7)
                                          ↓
                                   Phase 10 (Polish)
```

### User Story Dependencies

| Story | Depends On | Can Run In Parallel With |
|-------|------------|--------------------------|
| US1 | Foundational | US2, US3 |
| US2 | Foundational, T001 (cache.py) | US1, US3 |
| US3 | Foundational | US1, US2 |
| US4 | Foundational, T002 (retry.py) | US5, US6 |
| US5 | Foundational | US4, US6 |
| US6 | Foundational | US4, US5 |
| US7 | Foundational, T003 (masking.py) | - |

### Within Each User Story

1. Tests (if included) written first
2. Core implementation
3. Integration with existing code
4. Checkpoint verification

### Parallel Opportunities

**Phase 1 (모두 병렬)**:
```bash
Task: "T001 Create TTLCache class"
Task: "T002 Create retry decorator"
Task: "T003 Create masking utility"
```

**Phase 3-5 (P1 스토리 병렬)**:
```bash
# US1, US2, US3 동시 진행 가능 (서로 독립적)
Developer A: US1 (커넥션 풀)
Developer B: US2 (캐시)
Developer C: US3 (인덱스 확인)
```

**Phase 6-8 (P2-P3 스토리 병렬)**:
```bash
# US4, US5, US6 동시 진행 가능
Developer A: US4 (재시도)
Developer B: US5 (헬스체크)
Developer C: US6 (메트릭)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. **서비스 재시작**
4. Complete Phase 3: US1 (커넥션 풀)
5. Complete Phase 4: US2 (캐시)
6. **STOP and VALIDATE**: 동시 작업 + 캐시 히트율 확인
7. Deploy MVP

### Incremental Delivery

1. **MVP**: US1 + US2 (커넥션 풀 + 캐시) → 즉시 성능 개선
2. **+US3**: 인덱스 확인 (이미 존재 확인됨)
3. **+US4**: 재시도 로직 → 안정성 향상
4. **+US5**: 상세 헬스체크 → 모니터링 강화
5. **+US6**: 메트릭 수집 → 성능 추적
6. **+US7**: 코드 품질 → 유지보수성 향상

---

## Summary

| Phase | Tasks | Stories | Parallel |
|-------|-------|---------|----------|
| 1. Setup | 3 | - | Yes |
| 2. Foundational | 3 | - | No |
| 3. US1 | 2 | 동시 작업 안정성 | - |
| 4. US2 | 5 | 설정값 캐시 | - |
| 5. US3 | 2 | 인덱스 확인 | - |
| 6. US4 | 4 | 재시도 | - |
| 7. US5 | 4 | 헬스체크 | - |
| 8. US6 | 5 | 메트릭 | - |
| 9. US7 | 4 | 코드 품질 | - |
| 10. Polish | 4 | - | - |
| **Total** | **36** | **7** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- 서비스 재시작: Phase 2 완료 후 필수
- US3 (인덱스): 이미 존재 확인됨, 검증만 필요
- Commit after each task or logical group
