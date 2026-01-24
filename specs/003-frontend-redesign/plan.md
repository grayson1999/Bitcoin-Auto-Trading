# Implementation Plan: Frontend Redesign - Bitcoin Auto Trading Dashboard

**Branch**: `003-frontend-redesign` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-frontend-redesign/spec.md`

## Summary

Complete frontend rebuild for Bitcoin Auto Trading Dashboard using TradingView Lightweight Charts for candlestick visualization, shadcn/ui for component library, and hierarchical folder architecture. Key features include real-time market monitoring, portfolio performance tracking with accurate profit calculations, AI signal analysis views, and admin-only server monitoring.

## Technical Context

**Language/Version**: TypeScript 5.6+ with React 18.3
**Primary Dependencies**: TradingView Lightweight Charts, shadcn/ui, TanStack Query v5, React Router v6, Tailwind CSS 3, Axios
**Storage**: N/A (frontend only, state via TanStack Query)
**Testing**: Vitest
**Target Platform**: Web (Chrome, Firefox, Safari, Edge - last 2 versions), Mobile responsive (640px+)
**Project Type**: Web application (frontend only, backend already exists)
**Performance Goals**: Dashboard load < 3s, chart interval change < 1s, 5s polling interval
**Constraints**: JWT token refresh every 14 minutes, Auth Server on port 9000, Backend API on port 8000
**Scale/Scope**: 7 pages (Dashboard, Orders, Signals, Settings, Portfolio, Admin, Login), ~50 components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file contains template placeholders. Applying reasonable software engineering principles:

### Pre-Design Check (Phase 0)

| Principle | Status | Notes |
|-----------|--------|-------|
| Component Reusability | ✅ PASS | Using shadcn/ui base components, creating Common* wrappers |
| Test Coverage | ✅ PASS | Vitest configured, will add unit tests for hooks and utils |
| Type Safety | ✅ PASS | TypeScript 5.6 with strict mode |
| Simplicity | ✅ PASS | Hierarchical architecture without over-abstraction |
| Security | ✅ PASS | JWT auth, role-based access control, no hardcoded secrets |

### Post-Design Check (Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| Component Reusability | ✅ PASS | 15+ shadcn/ui components configured, Common* wrappers designed |
| Test Coverage | ✅ PASS | Test strategy defined in research.md, Vitest + RTL selected |
| Type Safety | ✅ PASS | Complete TypeScript interfaces defined in data-model.md |
| Simplicity | ✅ PASS | 3-layer architecture (Core → Domain → Views) without over-engineering |
| Security | ✅ PASS | Auth flow with token refresh, AdminRoute guard for protected pages |
| API Contracts | ✅ PASS | OpenAPI 3.0 spec created in contracts/api-contracts.yaml |
| Mobile Support | ✅ PASS | Responsive design strategy defined (640px+ breakpoints) |

**Result**: All gates passed. Ready for task generation (`/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/003-frontend-redesign/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── core/                   # Core Layer (공통 모듈)
│   │   ├── api/
│   │   │   └── client.ts           # Axios 인스턴스, 인터셉터
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui 컴포넌트
│   │   │   ├── CommonButton.tsx
│   │   │   ├── CommonCard.tsx
│   │   │   └── CommonModal.tsx
│   │   ├── composables/            # 재사용 훅
│   │   │   ├── useDebounce.ts
│   │   │   └── useToggle.ts
│   │   ├── layouts/
│   │   │   ├── MainLayout.tsx
│   │   │   └── AuthLayout.tsx
│   │   ├── errors/
│   │   │   └── ApiError.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── utils/
│   │       └── formatters.ts
│   │
│   ├── api/                    # Domain Layer (도메인 API)
│   │   ├── market.api.ts
│   │   ├── signal.api.ts
│   │   ├── trading.api.ts
│   │   ├── config.api.ts
│   │   ├── risk.api.ts
│   │   ├── portfolio.api.ts
│   │   └── admin.api.ts
│   │
│   ├── stores/                 # Domain Layer (상태 관리)
│   │   └── auth.store.ts           # 인증 상태 (Context)
│   │
│   ├── components/             # Domain Layer (도메인 컴포넌트)
│   │   ├── dashboard/
│   │   │   ├── PriceChart.tsx
│   │   │   ├── IndicatorOverlay.tsx
│   │   │   ├── PositionCard.tsx
│   │   │   └── MetricCards.tsx
│   │   ├── trading/
│   │   │   └── OrderTable.tsx
│   │   ├── signals/
│   │   │   ├── SignalCard.tsx
│   │   │   ├── SignalTimeline.tsx
│   │   │   └── SignalDetailModal.tsx
│   │   ├── portfolio/
│   │   │   ├── AssetAllocation.tsx
│   │   │   └── ProfitChart.tsx
│   │   └── admin/
│   │       ├── SchedulerStatus.tsx
│   │       ├── DatabaseStatus.tsx
│   │       ├── SystemResources.tsx
│   │       └── DiskUsage.tsx
│   │
│   ├── views/                  # Domain Layer (페이지)
│   │   ├── DashboardView.tsx
│   │   ├── OrdersView.tsx
│   │   ├── SignalsView.tsx
│   │   ├── PortfolioView.tsx
│   │   ├── SettingsView.tsx
│   │   ├── AdminView.tsx
│   │   └── LoginView.tsx
│   │
│   ├── router/                 # Routing Layer
│   │   ├── index.tsx
│   │   ├── routes.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── AdminRoute.tsx
│   │
│   ├── assets/                 # Asset Layer
│   │   └── styles/
│   │       └── index.css
│   │
│   └── main.tsx
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── public/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── components.json              # shadcn/ui config
```

**Structure Decision**: Web application frontend-only structure with hierarchical architecture (Core → Domain → Views). Backend already exists at `backend/` directory.

## Complexity Tracking

> No constitution violations requiring justification.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Chart Library | TradingView Lightweight Charts | Professional financial chart library, smaller than full TradingView, supports candlesticks and technical indicators |
| UI Components | shadcn/ui | Copy-paste components, fully customizable, works with Tailwind |
| State Management | TanStack Query only | No need for Redux/Zustand for server state; auth context sufficient for client state |
| Folder Structure | Hierarchical | Scales better than flat structure, clear separation of concerns |

## Backend API Dependencies

### Existing APIs (Ready to Use)
- `GET /api/v1/market` - Current price (Upbit real-time)
- `GET /api/v1/market/history` - Historical OHLCV data for charts
- `GET /api/v1/dashboard/summary` - Dashboard aggregated data
- `GET /api/v1/signals` - AI signal list with pagination
- `GET /api/v1/signals/latest` - Latest signal
- `GET /api/v1/trading/orders` - Order history
- `GET /api/v1/trading/position` - Current position
- `GET /api/v1/trading/balance` - Account balance
- `GET /api/v1/config` - All configurations
- `PATCH /api/v1/config/{key}` - Update configuration
- `GET /api/v1/risk/status` - Risk status
- `GET /api/v1/health/detail` - Detailed health check

### Backend APIs Requiring Implementation
1. **Portfolio Summary API** (`GET /api/v1/portfolio/summary`)
   - Cumulative return calculation
   - Total deposit tracking
   - MDD calculation
   - Win rate statistics

2. **Deposit History API** (`GET /api/v1/portfolio/deposits`)
   - Track initial + additional deposits
   - Required for accurate cumulative return

3. **Admin System Metrics API** (`GET /api/v1/admin/system`)
   - CPU usage
   - Memory usage
   - Disk usage

4. **Scheduler Status Enhancement** (in `/api/v1/health/detail`)
   - Individual job status
   - Last run time
   - Next scheduled time
