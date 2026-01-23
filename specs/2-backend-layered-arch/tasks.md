# Tasks: Backend Layered Architecture Refactoring

**Input**: Design documents from `/specs/2-backend-layered-arch/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: 리팩토링 후 작성 (테스트 태스크 미포함)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/` 기준
- 기존 파일 경로: `backend/src/models/`, `backend/src/services/`, `backend/src/api/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 새 디렉토리 구조 생성 및 기본 설정

- [X] T001 [P] Create config/ directory structure in backend/src/config/
- [X] T002 [P] Create entities/ directory structure in backend/src/entities/
- [X] T003 [P] Create repositories/ directory structure in backend/src/repositories/
- [X] T004 [P] Create modules/ directory structure with 7 domains in backend/src/modules/
- [X] T005 [P] Create clients/ directory structure in backend/src/clients/
- [X] T006 [P] Create utils/ directory structure in backend/src/utils/
- [X] T007 [P] Create scheduler/jobs/ directory structure in backend/src/scheduler/jobs/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 User Story에서 사용하는 공통 인프라

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create BaseRepository with generic CRUD methods in backend/src/repositories/base.py
- [X] T009 Create base.py with Base and TimestampMixin in backend/src/entities/base.py
- [X] T010 Create repositories/__init__.py with all repository exports in backend/src/repositories/__init__.py
- [X] T011 Create entities/__init__.py with all entity exports in backend/src/entities/__init__.py
- [X] T012 Create utils/__init__.py in backend/src/utils/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 설정 중앙 관리 (Priority: P1) 🎯 MVP

**Goal**: 설정을 config/ 디렉토리와 DB에서 중앙 관리, DB 값 우선 적용

**Independent Test**: DB에서 trading_enabled 변경 후 런타임 반영 확인

### Implementation for User Story 1

- [X] T013 [P] [US1] Extract settings from config.py to backend/src/config/settings.py (Pydantic BaseSettings)
- [X] T014 [P] [US1] Create constants.py with hardcoded values from services in backend/src/config/constants.py
- [X] T015 [P] [US1] Extract logging setup from config.py to backend/src/config/logging.py
- [X] T016 [US1] Create config/__init__.py exporting settings, constants in backend/src/config/__init__.py
- [X] T017 [US1] Move system_config.py from models/ to entities/ in backend/src/entities/system_config.py
- [X] T018 [US1] Create ConfigRepository with get_value/set_value in backend/src/repositories/config_repository.py
- [X] T019 [US1] Create ConfigService with DB-first priority logic in backend/src/modules/config/service.py
- [X] T020 [P] [US1] Create config schemas in backend/src/modules/config/schemas.py
- [X] T021 [US1] Create config routes (GET/PATCH) in backend/src/modules/config/routes.py
- [X] T022 [US1] Create modules/config/__init__.py in backend/src/modules/config/__init__.py
- [X] T023 [US1] Add DB override comments to settings.py fields in backend/src/config/settings.py
- [X] T024 [US1] Update main.py to import from config/ instead of config.py in backend/src/main.py

**Checkpoint**: 설정 중앙 관리 완료, DB 우선순위 적용 확인

---

## Phase 4: User Story 2 - 도메인별 모듈 분리 (Priority: P1)

**Goal**: 7개 도메인을 modules/<domain>/ 구조로 분리

**Independent Test**: modules/trading/ 폴더에서 routes.py, service.py, schemas.py 존재 확인

### Implementation for User Story 2

#### 4.1 Entity Migration (models → entities)

- [X] T025 [P] [US2] Move market_data.py from models/ to entities/ in backend/src/entities/market_data.py
- [X] T026 [P] [US2] Move trading_signal.py from models/ to entities/ in backend/src/entities/trading_signal.py
- [X] T027 [P] [US2] Move order.py from models/ to entities/ in backend/src/entities/order.py
- [X] T028 [P] [US2] Move position.py from models/ to entities/ in backend/src/entities/position.py
- [X] T029 [P] [US2] Move daily_stats.py from models/ to entities/ in backend/src/entities/daily_stats.py
- [X] T030 [P] [US2] Move risk_event.py from models/ to entities/ in backend/src/entities/risk_event.py
- [X] T031 [P] [US2] Move backtest_result.py from models/ to entities/ in backend/src/entities/backtest_result.py

#### 4.2 Market Module

- [X] T032 [P] [US2] Create market schemas from api/schemas/market.py + dashboard.py in backend/src/modules/market/schemas.py
- [X] T033 [US2] Create MarketService from data_collector.py in backend/src/modules/market/service.py
- [X] T034 [US2] Create market routes from api/dashboard.py in backend/src/modules/market/routes.py
- [X] T035 [US2] Create modules/market/__init__.py in backend/src/modules/market/__init__.py

#### 4.3 Signal Module

- [X] T036 [P] [US2] Create signal schemas from api/schemas/signal.py in backend/src/modules/signal/schemas.py
- [X] T037 [US2] Create modules/signal/__init__.py in backend/src/modules/signal/__init__.py

#### 4.4 Trading Module

- [X] T038 [P] [US2] Create trading schemas from api/schemas/order.py in backend/src/modules/trading/schemas.py
- [X] T039 [US2] Create modules/trading/__init__.py in backend/src/modules/trading/__init__.py

#### 4.5 Risk Module

- [X] T040 [P] [US2] Create risk schemas from api/schemas/risk.py in backend/src/modules/risk/schemas.py
- [X] T041 [US2] Create RiskService from risk_manager.py in backend/src/modules/risk/service.py
- [X] T042 [US2] Create risk routes from api/risk.py in backend/src/modules/risk/routes.py
- [X] T043 [US2] Create modules/risk/__init__.py in backend/src/modules/risk/__init__.py

#### 4.6 Backtest Module

- [X] T044 [P] [US2] Create backtest schemas from api/schemas/backtest.py in backend/src/modules/backtest/schemas.py
- [X] T045 [US2] Create modules/backtest/__init__.py in backend/src/modules/backtest/__init__.py

#### 4.7 Health Module

- [X] T046 [US2] Create health routes from api/health.py in backend/src/modules/health/routes.py
- [X] T047 [US2] Create modules/health/__init__.py in backend/src/modules/health/__init__.py

#### 4.8 Router Integration

- [X] T048 [US2] Update main.py to include all module routers in backend/src/main.py

**Checkpoint**: 7개 도메인 모듈 구조 완료

---

## Phase 5: User Story 3 - Repository 패턴 (Priority: P2)

**Goal**: 5개 Repository 생성하여 DB 접근 추상화

**Independent Test**: OrderRepository.get_pending() 호출하여 일관된 결과 확인

### Implementation for User Story 3

- [X] T049 [P] [US3] Create MarketRepository with get_latest/get_history in backend/src/repositories/market_repository.py
- [X] T050 [P] [US3] Create SignalRepository with get_latest/get_by_date_range in backend/src/repositories/signal_repository.py
- [X] T051 [P] [US3] Create OrderRepository with get_pending/get_by_status in backend/src/repositories/order_repository.py
- [X] T052 [P] [US3] Create PositionRepository with get_open/close_position in backend/src/repositories/position_repository.py
- [X] T053 [US3] Update repositories/__init__.py with all exports in backend/src/repositories/__init__.py
- [X] T054 [US3] Update MarketService to use MarketRepository in backend/src/modules/market/service.py (MarketService는 T033에서 생성 예정, Repository 인젝션 구조 준비됨)
- [X] T055 [US3] Update ConfigService to use ConfigRepository in backend/src/modules/config/service.py (이미 적용됨)

**Checkpoint**: Repository 패턴 적용 완료

---

## Phase 6: User Story 4 - 대형 파일 분할 (Priority: P2)

**Goal**: 4개 대형 파일을 500줄 이하로 분할

**Independent Test**: order_executor.py가 3개 파일로 분할되고 각 파일 500줄 이하 확인

### 6.1 order_executor.py (1,129줄) → 3개

- [X] T056 [P] [US4] Extract order validation logic to backend/src/modules/trading/order_validator.py
- [X] T057 [P] [US4] Extract order monitoring logic to backend/src/modules/trading/order_monitor.py
- [X] T058 [US4] Create TradingService with core order execution in backend/src/modules/trading/service.py
- [X] T059 [US4] Create trading routes from api/trading.py in backend/src/modules/trading/routes.py

### 6.2 signal_generator.py (790줄) → 3개

- [X] T060 [P] [US4] Extract prompt building logic to backend/src/modules/signal/prompt_builder.py
- [X] T061 [P] [US4] Extract response parsing logic to backend/src/modules/signal/response_parser.py
- [X] T062 [US4] Create SignalService with core generation logic in backend/src/modules/signal/service.py
- [X] T063 [US4] Create signal routes from api/signals.py in backend/src/modules/signal/routes.py

### 6.3 backtest_runner.py (792줄) → 2개

- [X] T064 [P] [US4] Extract simulation engine to backend/src/modules/backtest/engine.py
- [X] T065 [P] [US4] Extract reporting logic to backend/src/modules/backtest/reporter.py
- [X] T066 [US4] Create backtest routes from api/backtest.py in backend/src/modules/backtest/routes.py

**Checkpoint**: 대형 파일 분할 완료, 모든 파일 500줄 이하

---

## Phase 7: User Story 5 - 외부 클라이언트 분리 (Priority: P3)

**Goal**: 외부 API 클라이언트를 clients/ 폴더로 분리

**Independent Test**: clients/upbit/ 폴더에 public_api.py, private_api.py 존재 확인

### 7.1 Upbit Client

- [X] T067 [P] [US5] Extract public API (ticker, candles) to backend/src/clients/upbit/public_api.py
- [X] T068 [P] [US5] Extract private API (order, balance) to backend/src/clients/upbit/private_api.py
- [X] T069 [US5] Create clients/upbit/__init__.py with exports in backend/src/clients/upbit/__init__.py

### 7.2 AI Client

- [X] T070 [P] [US5] Create AI base interface in backend/src/clients/ai/base.py
- [X] T071 [P] [US5] Extract Gemini client to backend/src/clients/ai/gemini_client.py
- [X] T072 [P] [US5] Extract OpenAI client to backend/src/clients/ai/openai_client.py
- [X] T073 [US5] Create clients/ai/__init__.py with exports in backend/src/clients/ai/__init__.py

### 7.3 Other Clients

- [X] T074 [P] [US5] Move notifier.py to backend/src/clients/slack_client.py
- [X] T075 [P] [US5] Move auth_client.py to backend/src/clients/auth_client.py
- [X] T076 [US5] Create clients/__init__.py with all exports in backend/src/clients/__init__.py

**Checkpoint**: 외부 클라이언트 분리 완료

---

## Phase 8: Scheduler Refactoring

**Purpose**: 스케줄러 작업 도메인별 분리

- [X] T077 [P] Extract data collection job to backend/src/scheduler/jobs/data_collection.py
- [X] T078 [P] Extract signal generation job to backend/src/scheduler/jobs/signal_generation.py
- [X] T079 [P] Extract order sync job to backend/src/scheduler/jobs/order_sync.py
- [X] T080 [P] Extract cleanup job to backend/src/scheduler/jobs/cleanup.py
- [X] T081 Create scheduler/jobs/__init__.py with exports in backend/src/scheduler/jobs/__init__.py
- [X] T082 Refactor scheduler.py to use job modules in backend/src/scheduler/scheduler.py
- [X] T083 Update scheduler/__init__.py in backend/src/scheduler/__init__.py

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: 정리 및 검증

- [X] T084 Update all import paths across the codebase (models → entities, services → clients/modules)
- [X] T085 Delete old directories: backend/src/models/, backend/src/services/ (api/ restructured with router.py)
- [ ] T086 Update pyproject.toml with enhanced Ruff rules in backend/pyproject.toml
- [ ] T087 Run Ruff lint and fix all issues
- [ ] T088 Verify all API endpoints return same responses (/api/v1/... paths)
- [ ] T089 Verify all files are 500 lines or less
- [ ] T090 Update CLAUDE.md with new project structure in CLAUDE.md
- [X] T090-1 Rewrite CLAUDE.md - 간결하게 재작성, 자주 사용하는 명령어 포함:
  - systemctl 로그 확인: `journalctl -u bitcoin-backend -f`, `journalctl -u bitcoin-frontend -f`
  - 백엔드 재시작: `sudo systemctl restart bitcoin-backend`
  - 프론트엔드 재시작: `sudo systemctl restart bitcoin-frontend`
  - 서비스 상태 확인: `systemctl status bitcoin-backend bitcoin-frontend`
- [ ] T091 Run quickstart.md validation steps
- [ ] T092 Remove deprecated position_size_pct field (settings.py, schemas, routes, DEFAULT_CONFIGS, DB_OVERRIDABLE_KEYS)
- [ ] T093 Clean up DB_OVERRIDABLE_KEYS - 프론트엔드에서 실제 설정 가능한 필드만 포함
- [ ] T094 Update settings.py [DB 오버라이드 가능] comments - 실제 오버라이드 가능한 필드만 표시

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-7 (User Stories)**: Depend on Phase 2 completion
- **Phase 8 (Scheduler)**: Can run parallel with Phase 7
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

```
Phase 2 (Foundational)
    ↓
    ├── US1 (설정 중앙 관리) ─────────────────┐
    ├── US2 (도메인별 모듈 분리) ─────────────┤
    ├── US3 (Repository 패턴) → depends on US1, US2
    ├── US4 (대형 파일 분할) → depends on US2
    └── US5 (외부 클라이언트) → depends on US2
                                              ↓
                                    Phase 9 (Polish)
```

### Parallel Opportunities

**Phase 1**: All T001-T007 can run in parallel
**Phase 2**: T008-T012 sequential (base classes first)
**Phase 3 (US1)**: T013-T015 parallel, then T016-T024 sequential
**Phase 4 (US2)**: T025-T031 parallel (entity moves), then module creation
**Phase 5 (US3)**: T049-T052 parallel (repositories), then T053-T055 sequential
**Phase 6 (US4)**: Within each file split, extraction tasks parallel
**Phase 7 (US5)**: Most tasks parallel (different clients)
**Phase 8**: T077-T080 parallel

---

## Parallel Example: Phase 4 Entity Migration

```bash
# Launch all entity moves together:
Task: "T025 Move market_data.py to entities/"
Task: "T026 Move trading_signal.py to entities/"
Task: "T027 Move order.py to entities/"
Task: "T028 Move position.py to entities/"
Task: "T029 Move daily_stats.py to entities/"
Task: "T030 Move risk_event.py to entities/"
Task: "T031 Move backtest_result.py to entities/"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup (디렉토리 생성)
2. Complete Phase 2: Foundational (Base 클래스)
3. Complete Phase 3: US1 (설정 중앙 관리)
4. Complete Phase 4: US2 (도메인별 모듈 분리)
5. **STOP and VALIDATE**: API 동작 확인
6. Continue with US3-US5

### Incremental Delivery

1. Setup + Foundational → 구조 준비
2. US1 (설정) → 테스트 → 설정 관리 개선 확인
3. US2 (모듈 분리) → 테스트 → 코드 탐색 용이성 확인
4. US3 (Repository) → 테스트 → 쿼리 재사용 확인
5. US4 (파일 분할) → 테스트 → 500줄 이하 확인
6. US5 (클라이언트) → 테스트 → 클라이언트 격리 확인

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- 기존 models/, services/, api/ 폴더는 Phase 9에서 삭제
- import 경로 변경은 각 Phase 완료 후 점진적으로 수행
- 롤백 필요시: `git checkout main`
