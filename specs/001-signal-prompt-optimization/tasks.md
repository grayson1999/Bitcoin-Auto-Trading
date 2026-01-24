# Tasks: AI 신호 프롬프트 최적화

**Input**: Design documents from `/specs/001-signal-prompt-optimization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: 테스트 태스크는 plan.md에서 요청된 샘플링 모듈에 대해서만 포함됨.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 설정값 변경 및 기본 상수 추가

- [x] T001 [P] Add signal_interval_minutes field to backend/src/config/settings.py (replace signal_interval_hours)
- [x] T002 [P] Update DB_OVERRIDABLE_KEYS in backend/src/config/settings.py (replace signal_interval_hours with signal_interval_minutes)
- [x] T003 [P] Add SAMPLING_CONFIG constant to backend/src/config/constants.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 샘플링 모듈 생성 - 모든 User Story의 토큰 절감에 필수

**⚠️ CRITICAL**: 샘플링 모듈이 완성되어야 프롬프트 최적화 진행 가능

- [x] T004 Create MarketDataSampler class in backend/src/modules/signal/sampler.py
- [x] T005 Implement sample_by_interval() method in backend/src/modules/signal/sampler.py
- [x] T006 Implement get_sampled_data() method in backend/src/modules/signal/sampler.py
- [x] T007 [P] Create unit tests for MarketDataSampler in backend/tests/unit/signal/test_sampler.py
- [x] T008 Export MarketDataSampler from backend/src/modules/signal/__init__.py

**Checkpoint**: 샘플링 모듈 완성 - User Story 구현 시작 가능

---

## Phase 3: User Story 1 - 더 빈번한 매매 신호 수신 (Priority: P1) 🎯 MVP

**Goal**: 신호 생성 주기를 1시간에서 30분으로 변경하여 하루 48회 신호 생성

**Independent Test**: 스케줄러 설정 확인 후 30분 후 신호 생성 여부 검증

### Implementation for User Story 1

- [x] T009 [US1] Update IntervalTrigger in backend/src/scheduler/scheduler.py (hours → minutes)
- [x] T010 [US1] Update scheduler log message in backend/src/scheduler/scheduler.py
- [x] T011 [US1] Verify signal_interval_minutes is loaded from settings in scheduler.py

**Checkpoint**: 30분 주기 신호 생성 작동 확인 가능

---

## Phase 4: User Story 2 - 비용 효율적인 AI 호출 (Priority: P1)

**Goal**: AI 프롬프트 입력 토큰을 10,000개에서 4,000개로 60% 절감

**Independent Test**: AI 호출 시 input_tokens 로그로 4,000개 이하 확인

### Implementation for User Story 2

- [x] T012 [US2] Integrate MarketDataSampler into SignalService in backend/src/modules/signal/service.py
- [x] T013 [US2] Replace _get_recent_market_data() to use sampler in backend/src/modules/signal/service.py
- [x] T014 [US2] Update PromptBuilder to accept sampled data structure in backend/src/modules/signal/prompt/builder.py

**Checkpoint**: 프롬프트 토큰 4,000개 이하 달성

---

## Phase 5: User Story 3 - 시장 데이터 샘플링 (Priority: P2)

**Goal**: 장기/중기/단기별 샘플링으로 데이터 개수 1,000개 → ~450개 감소

**Independent Test**: 샘플링된 데이터 개수가 정책에 맞는지 로그로 확인

### Implementation for User Story 3

- [ ] T015 [US3] Add sampling statistics logging in backend/src/modules/signal/service.py
- [ ] T016 [US3] Update _format_market_data method to use sampled structure in backend/src/modules/signal/prompt/builder.py (if exists)

**Checkpoint**: 샘플링 통계 로그 출력 확인

---

## Phase 6: User Story 4 - 정확한 신뢰도 점수 (Priority: P2)

**Goal**: 명시적 신뢰도 계산 공식을 프롬프트에 포함하여 0.5 고정 출력 감소

**Independent Test**: 다양한 시장 상황에서 신뢰도가 0.5 외 값으로 출력되는지 확인

### Implementation for User Story 4

- [ ] T017 [US4] Add confidence calculation formula to system prompt in backend/src/modules/signal/prompt/templates.py
- [ ] T018 [US4] Update JSON output format to include confidence_breakdown in backend/src/modules/signal/prompt/templates.py
- [ ] T019 [US4] Compress system prompt (remove duplicate rules) in backend/src/modules/signal/prompt/templates.py
- [ ] T020 [US4] Add 30-minute aggressive trading strategy description in backend/src/modules/signal/prompt/templates.py

**Checkpoint**: 신뢰도 계산 공식 프롬프트 반영 완료

---

## Phase 7: User Story 5 - 성과 피드백 제거 (Priority: P3)

**Goal**: 프롬프트에서 성과 피드백 섹션 제거로 ~500 토큰 절감

**Independent Test**: 프롬프트에 성과 피드백 섹션 미포함 확인

### Implementation for User Story 5

- [ ] T021 [US5] Remove perf_tracker import and call from backend/src/modules/signal/service.py
- [ ] T022 [US5] Remove performance_feedback parameter from build_enhanced_prompt() in backend/src/modules/signal/prompt/builder.py
- [ ] T023 [US5] Remove _format_performance_feedback() method from backend/src/modules/signal/prompt/builder.py
- [ ] T024 [US5] Remove performance feedback section from analysis prompt in backend/src/modules/signal/prompt/templates.py
- [ ] T025 [US5] (Optional) Remove evaluate_signal_performance_job from backend/src/scheduler/scheduler.py

**Checkpoint**: 성과 피드백 완전 제거 확인

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 통합 검증 및 최종 정리

- [ ] T026 Compress analysis prompt in backend/src/modules/signal/prompt/templates.py (target: 2,500 tokens)
- [ ] T027 Add token count logging in backend/src/modules/signal/service.py
- [ ] T028 Run manual signal generation test via API
- [ ] T029 Verify token count is under 4,000
- [ ] T030 Verify AI response time is under 4 seconds
- [ ] T031 Restart backend service via systemctl
- [ ] T032 Monitor 30-minute signal generation for 1 hour

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
- **Polish (Phase 8)**: Depends on all user stories completion

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (30분 주기) | Phase 2 | US5 |
| US2 (토큰 절감) | Phase 2, T004-T006 | - |
| US3 (샘플링) | Phase 2 | US4 |
| US4 (신뢰도) | Phase 2 | US3, US5 |
| US5 (피드백 제거) | Phase 2 | US1, US4 |

### Critical Path

```
Setup → Foundational (Sampler) → US2 (Token Reduction) → Polish
                                      ↑
                            US1 (30min) + US5 (Remove Feedback)
                            US3 (Sampling) + US4 (Confidence)
```

---

## Parallel Opportunities

### Phase 1 (All Parallel)

```bash
# T001, T002, T003 can run in parallel (different files)
Task: "Add signal_interval_minutes to settings.py"
Task: "Update DB_OVERRIDABLE_KEYS in settings.py"
Task: "Add SAMPLING_CONFIG to constants.py"
```

### Phase 2 (Partially Parallel)

```bash
# T007 can run in parallel with T004-T006 (different file)
Task: "Create unit tests for MarketDataSampler"  # Can start immediately
```

### User Stories (Mostly Parallel)

```bash
# After Phase 2 completes, these can run in parallel:
# US1 (T009-T011) and US5 (T021-T025) - different files, no dependencies
# US3 (T015-T016) and US4 (T017-T020) - different aspects of templates.py but can be sequenced
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup (settings, constants)
2. Complete Phase 2: Foundational (sampler module)
3. Complete Phase 3: US1 (30분 주기)
4. Complete Phase 4: US2 (토큰 절감)
5. **STOP and VALIDATE**: 30분 주기 + 4,000 토큰 이하 확인
6. Deploy if ready

### Incremental Delivery

1. Setup + Foundational → 샘플링 기반 구축
2. US1 → 30분 주기 신호 생성 (MVP!)
3. US2 → 토큰 60% 절감 달성
4. US3 + US4 → 샘플링 통계 + 신뢰도 개선
5. US5 → 성과 피드백 제거
6. Polish → 최종 검증

---

## Notes

- [P] tasks = different files, no dependencies
- [USn] label maps task to specific user story
- US1과 US2가 핵심 MVP - 나머지는 점진적 개선
- 각 Story 완료 후 커밋 권장
- 롤백 필요 시 develop 브랜치로 복귀
