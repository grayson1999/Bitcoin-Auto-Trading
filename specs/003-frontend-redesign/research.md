# Research: Frontend Redesign

**Date**: 2026-01-24
**Feature**: Frontend Redesign - Bitcoin Auto Trading Dashboard

## Research Tasks

### 1. Chart Library Selection

**Question**: Which chart library best supports candlestick charts with technical indicators for React?

**Decision**: TradingView Lightweight Charts v5.x

**Rationale**:
- Official TradingView library with high reliability
- Performant HTML5 canvas rendering
- Native candlestick series support
- Built-in indicator support (MA, EMA) via reactive primitives
- Real-time `update()` method for efficient live data
- Smaller bundle size (~40KB) compared to full TradingView
- Apache 2.0 license (commercial use allowed)

**Alternatives Considered**:
| Library | Rejected Because |
|---------|------------------|
| Recharts | No native candlestick support, designed for standard charts |
| Chart.js | Financial chart plugin less mature |
| Highcharts Stock | Commercial license required |
| Apache ECharts | Large bundle size |
| Full TradingView Charting Library | Requires license agreement, heavier |

**Implementation Pattern**:
```typescript
import { createChart, CandlestickSeries } from 'lightweight-charts';

// Create chart instance
const chart = createChart(container, {
  width: 800,
  height: 400,
  layout: {
    background: { color: '#0B0E14' },
    textColor: '#F1F5F9',
  }
});

// Add candlestick series
const candlestickSeries = chart.addSeries(CandlestickSeries, {
  upColor: '#10B981',
  downColor: '#F43F5E',
});
candlestickSeries.setData(ohlcData);

// Real-time update (efficient single bar update)
candlestickSeries.update({ time: '2026-01-24', open: 100, high: 110, low: 95, close: 105 });
```

**Technical Indicators**:
- MA can be added via `applyMovingAverageIndicator()` reactive helper (auto-updates)
- For RSI, MACD: use `lightweight-charts-indicators` package or calculate manually
- Indicators displayed as LineSeries overlaid on chart

---

### 2. UI Component Library Selection

**Question**: Which component library integrates best with Tailwind CSS for React?

**Decision**: shadcn/ui (copy-paste component library)

**Rationale**:
- Full ownership of component code (not an npm dependency)
- Built on Radix UI primitives (accessible by default)
- Perfect Tailwind CSS integration
- Highly customizable for dark theme
- CLI for easy component installation
- Optimized bundle (only include what you use)

**Alternatives Considered**:
| Library | Rejected Because |
|---------|------------------|
| Material UI | Opinionated styling conflicts with Tailwind |
| Chakra UI | Heavy runtime, theme override complexity |
| Ant Design | Large bundle, less Tailwind friendly |
| Mantine | Good but larger ecosystem than needed |
| Headless UI | Fewer components available |

**Installation Steps**:
```bash
# Initialize shadcn/ui in Vite project
npx shadcn@latest init

# Add components as needed
npx shadcn@latest add button card dialog table tabs select input badge skeleton alert tooltip dropdown-menu
```

**Components Required**:
| Component | Usage |
|-----------|-------|
| Button | Actions, form submissions |
| Card | Metric cards, signal cards, position cards |
| Dialog/Modal | Signal detail, confirmations |
| Table | Order list, config list |
| Tabs | View toggles (card/timeline) |
| Select | Dropdowns for filters |
| Input | Form inputs in Settings |
| Badge | Status indicators |
| Skeleton | Loading states |
| Alert | Error/success messages |
| Tooltip | Help text |
| Dropdown Menu | User menu, actions |

---

### 3. Folder Architecture Decision

**Question**: Flat vs Hierarchical folder structure for 7 pages, ~50 components?

**Decision**: Hierarchical (Core → Domain → Views)

**Rationale**:
- Clear separation of reusable (Core) vs domain-specific components
- Scales better as project grows
- Easier navigation for new developers
- Matches backend module structure
- Avoids duplication of shared components

**Alternatives Considered**:
| Structure | Rejected Because |
|-----------|------------------|
| Flat | Hard to navigate with 50+ files |
| Feature-based colocation | Causes duplication of shared components |
| Atomic Design | Over-engineering for this project size |

**Layer Responsibilities**:
| Layer | Contents | Rules |
|-------|----------|-------|
| Core | API client, utils, common components, layouts | No domain logic, fully reusable |
| Domain | Domain-specific components, API functions, types | Domain logic, uses Core |
| Views | Page components | Composes Domain + Core |
| Router | Route definitions, guards | Uses Views |

---

### 4. State Management Approach

**Question**: Redux/Zustand vs TanStack Query only?

**Decision**: TanStack Query for server state + React Context for auth state

**Rationale**:
- TanStack Query already handles all server state (caching, refetching, polling)
- Only client state needed is authentication (user, tokens)
- React Context sufficient for simple auth state
- Avoids additional dependency and boilerplate
- No complex client-side state transformations needed

**TanStack Query Configuration**:
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,        // 5 seconds before refetch
      refetchInterval: 5000,  // Auto-refetch every 5s (for live data)
      retry: 3,               // Retry failed requests
      refetchOnWindowFocus: false,
    },
  },
});

// Custom hook example
function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardApi.getSummary(),
    refetchInterval: 5000,
  });
}
```

---

### 5. Authentication Flow

**Question**: How to integrate with existing Auth Server?

**Decision**: Axios interceptors + token refresh + role-based routing

**Rationale**:
- Auth Server already provides JWT tokens (9000 port)
- Backend expects `Authorization: Bearer <token>` header
- Token refresh mechanism needed (14-minute expiry)

**Implementation Pattern**:
```typescript
// Axios interceptor for auto-refresh
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(error.config);
      }
      // Redirect to login
      window.location.href = '/login';
    }
    throw error;
  }
);
```

**Role-Based Routing**:
- `user` role: Dashboard, Orders, Signals, Settings, Portfolio
- `admin` role: Above + Admin page
- Use `AdminRoute` wrapper component to check role

---

### 6. Backend API Gaps Analysis

**Question**: Which backend APIs need to be implemented for frontend features?

**Decision**: 3 new API endpoints required

**Existing APIs (Ready)**:
| Endpoint | Frontend Usage |
|----------|----------------|
| GET /api/v1/market | Current price display |
| GET /api/v1/market/history | Candlestick chart data (hours, limit, interval params) |
| GET /api/v1/dashboard/summary | Dashboard metrics |
| GET /api/v1/signals | Signal list (with pagination, type filter) |
| GET /api/v1/signals/latest | Latest signal for dashboard |
| GET /api/v1/trading/orders | Order table (status filter, pagination) |
| GET /api/v1/trading/position | Position card |
| GET /api/v1/trading/balance | Balance display |
| GET /api/v1/config | Settings page (list all configs) |
| PATCH /api/v1/config/{key} | Update individual setting |
| GET /api/v1/risk/status | Risk status with all parameters |
| GET /api/v1/health/detail | Detailed health (DB, Upbit, Gemini, scheduler) |

**New APIs Required**:

1. **GET /api/v1/portfolio/summary**
   ```json
   {
     "total_deposit": 10000000,
     "current_value": 11500000,
     "cumulative_return_pct": 15.0,
     "today_return_pct": 2.3,
     "today_realized_pnl": 230000,
     "total_trades": 150,
     "win_count": 85,
     "win_rate": 56.67,
     "average_return_pct": 1.2,
     "max_drawdown_pct": 8.5,
     "profit_chart_data": [
       { "date": "2026-01-01", "value": 10000000 },
       { "date": "2026-01-02", "value": 10150000 }
     ]
   }
   ```

2. **GET /api/v1/portfolio/deposits**
   ```json
   {
     "deposits": [
       { "id": 1, "amount": 5000000, "deposited_at": "2026-01-01T00:00:00Z" },
       { "id": 2, "amount": 5000000, "deposited_at": "2026-01-15T00:00:00Z" }
     ],
     "total": 10000000
   }
   ```

3. **GET /api/v1/admin/system**
   ```json
   {
     "cpu_percent": 25.5,
     "memory_percent": 45.2,
     "memory_used_mb": 1024,
     "memory_total_mb": 2048,
     "disk_percent": 68.3,
     "disk_used_gb": 34.5,
     "disk_total_gb": 50.0,
     "scheduler_jobs": [
       { "name": "data_collection", "status": "running", "last_run": "...", "next_run": "..." },
       { "name": "signal_generation", "status": "running", "last_run": "...", "next_run": "..." },
       { "name": "order_sync", "status": "running", "last_run": "...", "next_run": "..." }
     ]
   }
   ```

**Note**: Frontend can start development using mock data while backend APIs are being implemented.

---

### 7. Mobile Responsiveness Strategy

**Question**: How to ensure mobile (640px+) compatibility?

**Decision**: Tailwind CSS responsive classes + single-column mobile layout

**Implementation**:
- Use `sm:`, `md:`, `lg:` breakpoints
- Chart: Full width on mobile, maintain readable height (300px min)
- Tables: Horizontal scroll on mobile
- Sidebar: Collapsible drawer on mobile (hamburger menu)

**Key Breakpoints**:
| Breakpoint | Width | Layout |
|------------|-------|--------|
| Default | <640px | Single column, drawer navigation |
| sm | ≥640px | Single column with collapsed sidebar icon menu |
| md | ≥768px | Two columns where applicable |
| lg | ≥1024px | Full desktop layout with expanded sidebar |

---

### 8. Error Handling Strategy

**Question**: How to handle API errors consistently?

**Decision**: Centralized error handling with user-friendly messages

**Implementation**:
```typescript
class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public retryable: boolean = false
  ) {
    super(message);
  }
}

// Error messages by status (Korean)
const ERROR_MESSAGES: Record<number, string> = {
  401: '세션이 만료되었습니다. 다시 로그인해 주세요.',
  403: '접근 권한이 없습니다.',
  404: '요청한 데이터를 찾을 수 없습니다.',
  429: '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.',
  500: '서버 오류가 발생했습니다.',
  503: '서비스를 일시적으로 사용할 수 없습니다.',
};
```

**Retry Logic**:
- TanStack Query handles automatic retry (3 times by default)
- Manual retry button for user-initiated retry
- Show loading state during retry
- Network error: "네트워크 연결을 확인해 주세요."

---

### 9. Technical Indicator Calculations

**Question**: Calculate indicators on frontend or backend?

**Decision**: Frontend calculation for chart display

**Rationale**:
- Reduces backend load
- Real-time recalculation when user changes parameters
- Integration with chart library for immediate display
- Backend `/market/history` provides raw OHLCV data

**Implementation (MA example)**:
```typescript
function calculateSMA(closes: number[], period: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < period - 1) return null;
    const sum = closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    return sum / period;
  });
}

// RSI and MACD calculations follow standard formulas
// Use lightweight-charts-indicators package for validated implementations
```

---

## Dependencies Summary

### Production Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.3.1 | UI framework |
| react-dom | ^18.3.1 | React DOM renderer |
| react-router-dom | ^6.28.0 | Client-side routing |
| @tanstack/react-query | ^5.62.0 | Server state management |
| axios | ^1.7.0 | HTTP client |
| lightweight-charts | ^5.0.0 | TradingView charts |
| tailwindcss | ^3.4.15 | Styling |
| lucide-react | ^0.460.0 | Icons (shadcn/ui default) |
| clsx | ^2.1.0 | Conditional classes |
| tailwind-merge | ^2.5.0 | Merge Tailwind classes |
| class-variance-authority | ^0.7.0 | Component variants (shadcn/ui) |

### Dev Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ~5.6.2 | Type checking |
| vite | ^6.0.1 | Build tool |
| vitest | ^2.1.0 | Testing |
| @testing-library/react | ^16.0.0 | React testing utilities |
| eslint | ^9.15.0 | Linting |
| @types/react | ^18.3.12 | React types |

### shadcn/ui Components to Install
```bash
npx shadcn@latest add button card dialog table tabs select input badge skeleton alert tooltip dropdown-menu progress slider switch
```

---

## Conclusion

All technical decisions have been resolved. The frontend redesign can proceed with:
- **TradingView Lightweight Charts** for professional candlestick visualization
- **shadcn/ui** for accessible, customizable components
- **Hierarchical folder structure** for scalability
- **TanStack Query** for efficient server state management
- **3 new backend APIs** required (portfolio summary, deposits, admin system)

**Development can begin immediately** - frontend can use mock data while backend APIs are implemented in parallel.
