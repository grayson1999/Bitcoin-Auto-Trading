# Tasks: Frontend Redesign - Bitcoin Auto Trading Dashboard

**Input**: Design documents from `/specs/003-frontend-redesign/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested - test tasks omitted (development tests only where needed)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (frontend only)**: `frontend/src/`
- All paths are relative to repository root `/home/ubuntu/Bitcoin-Auto-Trading/`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Delete existing frontend and initialize new project with required dependencies

- [ ] T001 Backup existing frontend directory to `frontend_backup_YYYYMMDD`
- [ ] T002 Initialize new Vite + React + TypeScript project in `frontend/`
- [ ] T003 Install core dependencies (react-router-dom, @tanstack/react-query, axios, lightweight-charts)
- [ ] T004 [P] Install shadcn/ui dependencies (clsx, tailwind-merge, class-variance-authority, lucide-react)
- [ ] T005 [P] Install dev dependencies (vitest, @testing-library/react, @types/node)
- [ ] T006 Configure Tailwind CSS with custom theme colors in `frontend/tailwind.config.js`
- [ ] T007 [P] Configure path aliases in `frontend/tsconfig.json` and `frontend/vite.config.ts`
- [ ] T008 Initialize shadcn/ui and install components (button, card, dialog, table, tabs, select, input, badge, skeleton, alert, tooltip, dropdown-menu, progress, slider, switch)
- [ ] T009 Create folder structure per plan.md in `frontend/src/` (core/, api/, stores/, components/, views/, router/, assets/)
- [ ] T010 [P] Create environment files `.env` and `.env.production` in `frontend/`

---

## Phase 2: Foundational (Core Infrastructure)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Core Layer

- [ ] T011 Create TypeScript types and enums in `frontend/src/core/types/index.ts` (from data-model.md)
- [ ] T012 Create API client with auth interceptors in `frontend/src/core/api/client.ts`
- [ ] T013 [P] Create ApiError class in `frontend/src/core/errors/ApiError.ts`
- [ ] T014 [P] Create utility formatters (currency, date, percentage) in `frontend/src/core/utils/formatters.ts`
- [ ] T015 [P] Create cn() utility for Tailwind classes in `frontend/src/core/utils/cn.ts`
- [ ] T016 [P] Create useDebounce hook in `frontend/src/core/composables/useDebounce.ts`
- [ ] T017 [P] Create useToggle hook in `frontend/src/core/composables/useToggle.ts`

### Auth Infrastructure

- [ ] T018 Create AuthContext and AuthProvider in `frontend/src/stores/auth.store.ts`
- [ ] T019 Create auth API functions (login, logout, refresh) in `frontend/src/api/auth.api.ts`
- [ ] T020 Create ProtectedRoute component in `frontend/src/router/ProtectedRoute.tsx`
- [ ] T021 Create AdminRoute component in `frontend/src/router/AdminRoute.tsx`

### Layout Components

- [ ] T022 Create MainLayout with sidebar navigation in `frontend/src/core/layouts/MainLayout.tsx`
- [ ] T023 [P] Create AuthLayout for login page in `frontend/src/core/layouts/AuthLayout.tsx`
- [ ] T024 Create responsive sidebar component in `frontend/src/core/components/Sidebar.tsx`

### Common Components

- [ ] T025 [P] Create CommonButton wrapper in `frontend/src/core/components/CommonButton.tsx`
- [ ] T026 [P] Create CommonCard wrapper in `frontend/src/core/components/CommonCard.tsx`
- [ ] T027 [P] Create CommonModal wrapper in `frontend/src/core/components/CommonModal.tsx`
- [ ] T028 [P] Create LoadingSpinner component in `frontend/src/core/components/LoadingSpinner.tsx`
- [ ] T029 [P] Create ErrorMessage component in `frontend/src/core/components/ErrorMessage.tsx`
- [ ] T030 [P] Create EmptyState component in `frontend/src/core/components/EmptyState.tsx`

### Routing Setup

- [ ] T031 Create route definitions in `frontend/src/router/routes.tsx`
- [ ] T032 Create router index with providers in `frontend/src/router/index.tsx`
- [ ] T033 Update main.tsx with QueryClient, BrowserRouter, AuthProvider in `frontend/src/main.tsx`
- [ ] T034 Create LoginView page in `frontend/src/views/LoginView.tsx`

### Global Styles

- [ ] T035 Update global CSS with dark theme base styles in `frontend/src/assets/styles/index.css`
- [ ] T036 Update App.tsx to render router in `frontend/src/App.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 실시간 시세 및 포지션 모니터링 (Priority: P1) 🎯 MVP

**Goal**: Dashboard with candlestick chart, technical indicators, position display, balance display, auto-refresh

**Independent Test**: User can login, access dashboard, see live BTC chart with indicators, view position and balance

### API Layer for US1

- [ ] T037 [P] [US1] Create market API functions in `frontend/src/api/market.api.ts`
- [ ] T038 [P] [US1] Create dashboard API functions in `frontend/src/api/dashboard.api.ts`
- [ ] T039 [P] [US1] Create trading API functions (position, balance) in `frontend/src/api/trading.api.ts`
- [ ] T040 [P] [US1] Create risk API functions in `frontend/src/api/risk.api.ts`

### Chart Components for US1

- [ ] T041 [US1] Create PriceChart component with TradingView Lightweight Charts in `frontend/src/components/dashboard/PriceChart.tsx`
- [ ] T042 [US1] Create interval selector (1m/5m/15m/1h) in PriceChart component
- [ ] T043 [US1] Implement MA indicator overlay (20, 50, 200) in `frontend/src/components/dashboard/indicators/MAIndicator.ts`
- [ ] T044 [P] [US1] Implement RSI indicator in `frontend/src/components/dashboard/indicators/RSIIndicator.ts`
- [ ] T045 [P] [US1] Implement MACD indicator in `frontend/src/components/dashboard/indicators/MACDIndicator.ts`
- [ ] T046 [US1] Create IndicatorControls component (toggle MA/RSI/MACD) in `frontend/src/components/dashboard/IndicatorControls.tsx`

### Dashboard Components for US1

- [ ] T047 [P] [US1] Create PositionCard component in `frontend/src/components/dashboard/PositionCard.tsx`
- [ ] T048 [P] [US1] Create BalanceCard component in `frontend/src/components/dashboard/BalanceCard.tsx`
- [ ] T049 [P] [US1] Create MetricCards component (price, 24h change, daily P&L) in `frontend/src/components/dashboard/MetricCards.tsx`
- [ ] T050 [P] [US1] Create LatestSignalCard component in `frontend/src/components/dashboard/LatestSignalCard.tsx`
- [ ] T051 [P] [US1] Create RiskStatusCard component in `frontend/src/components/dashboard/RiskStatusCard.tsx`

### Dashboard View for US1

- [ ] T052 [US1] Create DashboardView page composing all dashboard components in `frontend/src/views/DashboardView.tsx`
- [ ] T053 [US1] Implement 5-second auto-refresh with TanStack Query refetchInterval
- [ ] T054 [US1] Add loading states with Skeleton components
- [ ] T055 [US1] Add error handling with retry functionality

**Checkpoint**: User Story 1 complete - Dashboard with live chart, indicators, position, balance is functional

---

## Phase 4: User Story 2 - 포트폴리오 수익 현황 확인 (Priority: P1)

**Goal**: Portfolio page with cumulative return, today's return, win rate, MDD, profit chart

**Independent Test**: User can access portfolio page, see accurate return calculations, view 30-day profit chart

**Note**: Requires backend API `GET /api/v1/portfolio/summary` - use mock data initially if not available

### API Layer for US2

- [ ] T056 [P] [US2] Create portfolio API functions in `frontend/src/api/portfolio.api.ts`
- [ ] T057 [P] [US2] Create mock data fallback for portfolio summary in `frontend/src/api/mocks/portfolio.mock.ts`

### Portfolio Components for US2

- [ ] T058 [P] [US2] Create CumulativeReturnCard component in `frontend/src/components/portfolio/CumulativeReturnCard.tsx`
- [ ] T059 [P] [US2] Create TodayReturnCard component in `frontend/src/components/portfolio/TodayReturnCard.tsx`
- [ ] T060 [P] [US2] Create TradeStatsCard component (win rate, avg return, MDD) in `frontend/src/components/portfolio/TradeStatsCard.tsx`
- [ ] T061 [US2] Create ProfitChart component (30-day line chart) in `frontend/src/components/portfolio/ProfitChart.tsx`
- [ ] T062 [P] [US2] Create DepositHistoryCard component in `frontend/src/components/portfolio/DepositHistoryCard.tsx`

### Portfolio View for US2

- [ ] T063 [US2] Create PortfolioView page composing all portfolio components in `frontend/src/views/PortfolioView.tsx`
- [ ] T064 [US2] Implement empty state for users with no trades
- [ ] T065 [US2] Add loading and error states

**Checkpoint**: User Story 2 complete - Portfolio page with accurate return calculations is functional

---

## Phase 5: User Story 3 - AI 신호 확인 및 분석 (Priority: P2)

**Goal**: Signals page with card grid, timeline view, type filter, detail modal

**Independent Test**: User can view AI signals in grid/timeline, filter by type, click to see detail modal

### API Layer for US3

- [ ] T066 [P] [US3] Create signal API functions in `frontend/src/api/signal.api.ts`

### Signal Components for US3

- [ ] T067 [P] [US3] Create SignalCard component (BUY/SELL/HOLD colors) in `frontend/src/components/signals/SignalCard.tsx`
- [ ] T068 [P] [US3] Create SignalTimeline component in `frontend/src/components/signals/SignalTimeline.tsx`
- [ ] T069 [US3] Create SignalDetailModal component in `frontend/src/components/signals/SignalDetailModal.tsx`
- [ ] T070 [P] [US3] Create SignalTypeFilter component in `frontend/src/components/signals/SignalTypeFilter.tsx`
- [ ] T071 [P] [US3] Create ViewToggle component (grid/timeline) in `frontend/src/components/signals/ViewToggle.tsx`

### Signals View for US3

- [ ] T072 [US3] Create SignalsView page with grid and timeline modes in `frontend/src/views/SignalsView.tsx`
- [ ] T073 [US3] Implement signal type filtering (BUY/SELL/HOLD/all)
- [ ] T074 [US3] Implement pagination for signal list
- [ ] T075 [US3] Add loading and empty states

**Checkpoint**: User Story 3 complete - Signals page with grid/timeline views and filtering is functional

---

## Phase 6: User Story 4 - 주문 내역 조회 (Priority: P2)

**Goal**: Orders page with table, status filter, pagination

**Independent Test**: User can view order history, filter by status, navigate pages

### Order Components for US4

- [ ] T076 [P] [US4] Create OrderTable component with columns (ID, type, price, qty, status, time) in `frontend/src/components/trading/OrderTable.tsx`
- [ ] T077 [P] [US4] Create OrderStatusFilter component in `frontend/src/components/trading/OrderStatusFilter.tsx`
- [ ] T078 [P] [US4] Create OrderStatusBadge component in `frontend/src/components/trading/OrderStatusBadge.tsx`
- [ ] T079 [P] [US4] Create Pagination component in `frontend/src/core/components/Pagination.tsx`

### Orders View for US4

- [ ] T080 [US4] Create OrdersView page with table and filters in `frontend/src/views/OrdersView.tsx`
- [ ] T081 [US4] Implement status filtering (all/pending/executed/cancelled/failed)
- [ ] T082 [US4] Implement pagination (20 items per page)
- [ ] T083 [US4] Add loading and empty states

**Checkpoint**: User Story 4 complete - Orders page with filtering and pagination is functional

---

## Phase 7: User Story 5 - 시스템 설정 관리 (Priority: P2)

**Goal**: Settings page with trading params, AI settings, reset functionality

**Independent Test**: User can view and modify settings, reset to defaults, see success/error messages

### API Layer for US5

- [ ] T084 [P] [US5] Create config API functions in `frontend/src/api/config.api.ts`

### Settings Components for US5

- [ ] T085 [P] [US5] Create TradingSettingsForm component (position size, stop loss, daily limit) in `frontend/src/components/settings/TradingSettingsForm.tsx`
- [ ] T086 [P] [US5] Create AISettingsForm component (model, signal interval) in `frontend/src/components/settings/AISettingsForm.tsx`
- [ ] T087 [P] [US5] Create ResetSettingsButton component in `frontend/src/components/settings/ResetSettingsButton.tsx`
- [ ] T088 [P] [US5] Create SettingsSection wrapper component in `frontend/src/components/settings/SettingsSection.tsx`

### Settings View for US5

- [ ] T089 [US5] Create SettingsView page with all settings forms in `frontend/src/views/SettingsView.tsx`
- [ ] T090 [US5] Implement form validation for numeric inputs
- [ ] T091 [US5] Implement save with success/error toast notifications
- [ ] T092 [US5] Implement reset to defaults with confirmation dialog

**Checkpoint**: User Story 5 complete - Settings page with save and reset functionality is functional

---

## Phase 8: User Story 6 - 관리자 서버 모니터링 (Priority: P3)

**Goal**: Admin-only page with scheduler status, DB status, system resources, disk usage

**Independent Test**: Admin can view system metrics, regular users are blocked and redirected

**Note**: Requires backend API `GET /api/v1/admin/system` - use mock data initially if not available

### API Layer for US6

- [ ] T093 [P] [US6] Create admin API functions in `frontend/src/api/admin.api.ts`
- [ ] T094 [P] [US6] Create health API functions in `frontend/src/api/health.api.ts`
- [ ] T095 [P] [US6] Create mock data fallback for admin system metrics in `frontend/src/api/mocks/admin.mock.ts`

### Admin Components for US6

- [ ] T096 [P] [US6] Create SchedulerStatus component in `frontend/src/components/admin/SchedulerStatus.tsx`
- [ ] T097 [P] [US6] Create DatabaseStatus component in `frontend/src/components/admin/DatabaseStatus.tsx`
- [ ] T098 [P] [US6] Create SystemResources component (CPU, memory) in `frontend/src/components/admin/SystemResources.tsx`
- [ ] T099 [P] [US6] Create DiskUsage component with 70% warning in `frontend/src/components/admin/DiskUsage.tsx`
- [ ] T100 [P] [US6] Create SystemHealthOverview component in `frontend/src/components/admin/SystemHealthOverview.tsx`

### Admin View for US6

- [ ] T101 [US6] Create AdminView page composing all admin components in `frontend/src/views/AdminView.tsx`
- [ ] T102 [US6] Implement AdminRoute guard (redirect non-admin to dashboard)
- [ ] T103 [US6] Implement auto-refresh for system metrics (10 second interval)
- [ ] T104 [US6] Add loading states with Skeleton components

**Checkpoint**: User Story 6 complete - Admin page with system monitoring is functional (admin-only access)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Responsive Design

- [ ] T105 [P] Ensure mobile responsiveness for MainLayout and Sidebar (640px breakpoint)
- [ ] T106 [P] Ensure mobile responsiveness for DashboardView (chart height adjustment)
- [ ] T107 [P] Ensure mobile responsiveness for OrderTable (horizontal scroll)
- [ ] T108 [P] Test all pages on mobile viewport (640px)

### Error Handling & Edge Cases

- [ ] T109 [P] Implement network error handling with retry button across all views
- [ ] T110 [P] Implement loading timeout handling (5s timeout message)
- [ ] T111 [P] Implement session expiry handling (auto redirect to login)

### Performance & UX

- [ ] T112 [P] Add route-based code splitting with React.lazy
- [ ] T113 [P] Optimize TanStack Query cache settings for optimal UX
- [ ] T114 [P] Add page transition animations (optional)

### Final Validation

- [ ] T115 Run quickstart.md verification checklist
- [ ] T116 Verify all user stories work independently
- [ ] T117 Run production build and verify no errors (`npm run build`)
- [ ] T118 Update frontend/README.md with setup instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Dashboard - No dependencies on other stories
- **User Story 2 (P1)**: Portfolio - No dependencies on other stories (uses different API)
- **User Story 3 (P2)**: Signals - No dependencies on other stories
- **User Story 4 (P2)**: Orders - No dependencies on other stories
- **User Story 5 (P2)**: Settings - No dependencies on other stories
- **User Story 6 (P3)**: Admin - No dependencies on other stories (requires admin role)

### Within Each User Story

- API layer first (enables components)
- Components can be built in parallel [P]
- View page composes components (depends on components)
- Loading/error states after main implementation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- **Once Foundational completes, ALL 6 user stories can start in parallel** (different files, no conflicts)
- All components within a story marked [P] can run in parallel
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: After Foundational Phase

```bash
# Developer A: User Story 1 (Dashboard)
Task: "Create market API functions in frontend/src/api/market.api.ts"
Task: "Create PriceChart component in frontend/src/components/dashboard/PriceChart.tsx"
...

# Developer B: User Story 2 (Portfolio)
Task: "Create portfolio API functions in frontend/src/api/portfolio.api.ts"
Task: "Create ProfitChart component in frontend/src/components/portfolio/ProfitChart.tsx"
...

# Developer C: User Story 3 (Signals)
Task: "Create signal API functions in frontend/src/api/signal.api.ts"
Task: "Create SignalCard component in frontend/src/components/signals/SignalCard.tsx"
...
```

---

## Parallel Example: Within User Story 1 (Components)

```bash
# All these can run in parallel (different files):
Task: "[US1] Create PositionCard component in frontend/src/components/dashboard/PositionCard.tsx"
Task: "[US1] Create BalanceCard component in frontend/src/components/dashboard/BalanceCard.tsx"
Task: "[US1] Create MetricCards component in frontend/src/components/dashboard/MetricCards.tsx"
Task: "[US1] Create LatestSignalCard component in frontend/src/components/dashboard/LatestSignalCard.tsx"
Task: "[US1] Create RiskStatusCard component in frontend/src/components/dashboard/RiskStatusCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dashboard)
4. **STOP and VALIDATE**: Test Dashboard independently - user can login, see chart, view position
5. Deploy/demo if ready - Dashboard alone provides monitoring value

### Recommended Incremental Delivery

1. **MVP**: Setup + Foundational + US1 (Dashboard) → Core monitoring
2. **+Portfolio**: Add US2 → Track investment performance
3. **+Signals**: Add US3 → Review AI analysis
4. **+Orders**: Add US4 → Audit trade history
5. **+Settings**: Add US5 → Customize parameters
6. **+Admin**: Add US6 → System monitoring (admin only)

### Parallel Team Strategy (3 Developers)

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Dashboard) + User Story 4 (Orders)
   - Developer B: User Story 2 (Portfolio) + User Story 5 (Settings)
   - Developer C: User Story 3 (Signals) + User Story 6 (Admin)
3. Stories complete and integrate independently

---

## Backend API Notes

### Existing APIs (Ready)
All APIs for US1, US3, US4, US5 are available:
- `/api/v1/market`, `/api/v1/market/history`
- `/api/v1/dashboard/summary`
- `/api/v1/signals`, `/api/v1/signals/latest`
- `/api/v1/trading/orders`, `/api/v1/trading/position`, `/api/v1/trading/balance`
- `/api/v1/config`, `/api/v1/config/{key}`
- `/api/v1/risk/status`
- `/api/v1/health/detail`

### New APIs Required (Backend Work)
- **US2**: `GET /api/v1/portfolio/summary`, `GET /api/v1/portfolio/deposits`
- **US6**: `GET /api/v1/admin/system`

Frontend can use mock data while backend implements these APIs.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
