# Frontend Redesign Spec

> 작성일: 2026-01-24

---

## 1. 기술 스택

### 유지
- React 18 + TypeScript 5
- Vite 6
- TanStack Query v5
- Tailwind CSS 3
- React Router v6

### 변경
- 차트: Recharts → **TradingView Lightweight Charts**
- UI: 직접 구현 → **shadcn/ui**
- 폴더: 플랫 구조 → **기능별 모듈화**

---

## 2. 페이지 구성

| 페이지 | 상태 | 접근 권한 |
|--------|------|-----------|
| Dashboard | 재구현 | 일반 |
| Orders | 재구현 | 일반 |
| Signals | 재구현 | 일반 |
| Settings | 재구현 | 일반 |
| Portfolio | **신규** | 일반 |
| Admin | **신규** | **관리자** |
| ~~Backtest~~ | 삭제 | - |

---

## 3. 페이지별 기능

### Dashboard
- 캔들스틱 차트 (1분/5분/15분/1시간)
- 기술적 지표 오버레이
  - MA (이동평균선)
  - RSI
  - MACD
- 포지션 현황
- 주요 지표 카드
- 최신 AI 신호
- 리스크 상태

### Orders
- 주문 테이블
- 상태 필터링
- 페이지네이션

### Signals
- 신호 카드 그리드
- **신호 타임라인 뷰** (신규)
- 타입 필터링
- 상세 모달

### Settings
- 포지션 사이징 (최소/최대 %)
- 손절매 임계값
- 일일 손실 한도
- AI 모델 선택
- 신호 생성 주기

### Portfolio (신규)
- 자산 배분 차트
- **누적 수익**
  - 계산: `(현재 총 평가금액 - 최초 투자금액) / 최초 투자금액 × 100`
  - 총 평가금액 = KRW 잔고 + (BTC 보유량 × 현재가)
  - **백엔드 필요**: `initial_investment` 설정 추가 (system_configs 또는 user_configs)
- **오늘 수익**
  - 계산: `realized_pnl / starting_balance × 100`
  - 데이터 소스: `daily_stats.realized_pnl`, `daily_stats.starting_balance`
  - **백엔드 현황**: dashboard/summary API에서 `daily_pnl`, `daily_pnl_pct` 제공 중
- 거래 성과 통계
  - 승률: `win_count / trade_count`
  - 평균 수익률
  - 최대 손실 (MDD)

**백엔드 추가 작업:**
1. `initial_investment` 자동 기록
   - 첫 거래(주문 체결) 시점에 현재 총 평가금액을 자동 저장
   - user_configs 또는 별도 테이블에 저장
2. Portfolio API 엔드포인트 추가 (GET /api/v1/portfolio/summary)
   - 누적 수익 (initial_investment 기준)
   - 전체 기간 통계 (daily_stats 집계)

### Admin (신규, 관리자 전용)
- 스케줄러 작업 상태
  - 데이터 수집
  - 신호 생성
  - 주문 동기화
- 데이터베이스 상태
  - 커넥션 풀
  - 쿼리 성능
- 시스템 리소스
  - CPU 사용률
  - 메모리 사용률
- **볼륨/디스크 용량**
  - 사용량
  - 여유 공간
  - 사용률 %

---

## 4. 폴더 구조 (계층형 아키텍처)

```
src/
├── core/                   # Core Layer (공통 모듈)
│   ├── api/
│   │   └── client.ts           # Axios 인스턴스, 인터셉터
│   ├── components/
│   │   ├── ui/                 # shadcn/ui 컴포넌트
│   │   ├── CommonButton.tsx
│   │   ├── CommonCard.tsx
│   │   └── CommonModal.tsx
│   ├── composables/            # 재사용 훅
│   │   ├── useDebounce.ts
│   │   └── useToggle.ts
│   ├── layouts/
│   │   ├── MainLayout.tsx
│   │   └── AuthLayout.tsx
│   ├── errors/
│   │   └── ApiError.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── formatters.ts
│
├── api/                    # Domain Layer (도메인 API)
│   ├── market.api.ts
│   ├── signal.api.ts
│   ├── trading.api.ts
│   ├── config.api.ts
│   ├── risk.api.ts
│   └── admin.api.ts
│
├── stores/                 # Domain Layer (상태 관리)
│   └── auth.store.ts           # 인증 상태 (Context)
│
├── components/             # Domain Layer (도메인 컴포넌트)
│   ├── dashboard/
│   │   ├── PriceChart.tsx
│   │   ├── IndicatorOverlay.tsx
│   │   ├── PositionCard.tsx
│   │   └── MetricCards.tsx
│   ├── trading/
│   │   └── OrderTable.tsx
│   ├── signals/
│   │   ├── SignalCard.tsx
│   │   ├── SignalTimeline.tsx
│   │   └── SignalDetailModal.tsx
│   ├── portfolio/
│   │   ├── AssetAllocation.tsx
│   │   └── ProfitChart.tsx
│   └── admin/
│       ├── SchedulerStatus.tsx
│       ├── DatabaseStatus.tsx
│       ├── SystemResources.tsx
│       └── DiskUsage.tsx
│
├── views/                  # Domain Layer (페이지)
│   ├── DashboardView.tsx
│   ├── OrdersView.tsx
│   ├── SignalsView.tsx
│   ├── PortfolioView.tsx
│   ├── SettingsView.tsx
│   ├── AdminView.tsx
│   └── LoginView.tsx
│
├── router/                 # Routing Layer
│   ├── index.tsx
│   ├── routes.tsx
│   ├── ProtectedRoute.tsx
│   └── AdminRoute.tsx
│
├── assets/                 # Asset Layer
│   └── styles/
│       └── index.css
│
└── main.tsx
```

**계층별 역할:**

| 계층 | 구성 요소 | 역할 |
|------|-----------|------|
| Core | core/api/ | Axios 인스턴스, 인터셉터 |
| Core | core/components/ | Common* 공용 컴포넌트, shadcn/ui |
| Core | core/composables/ | use* 훅 (재사용 로직) |
| Core | core/layouts/ | *Layout 레이아웃 컴포넌트 |
| Core | core/errors/ | 에러 클래스, 메시지 |
| Core | core/types/ | 공용 타입 정의 |
| Core | core/utils/ | 유틸리티 함수 |
| Domain | api/ | 도메인 API 호출 (*.api.ts) |
| Domain | stores/ | 상태 관리 (인증 Context) |
| Domain | components/ | 도메인별 컴포넌트 |
| Domain | views/ | 페이지 컴포넌트 (*View.tsx) |
| Routing | router/ | 라우트 정의, 가드 |
| Asset | assets/ | 스타일, 이미지 |

---

## 5. 디자인

### 유지
- 다크 테마
- 글래스모피즘 패널
- 바나나 옐로우 (#FACC15) 악센트
- Inter 폰트
- 반응형 레이아웃

### 컬러 코드
| 용도 | 색상 |
|------|------|
| 배경 | #0B0E14 |
| 표면 | #151921 |
| 악센트 | #FACC15 |
| 상승/성공 | 에메랄드 |
| 하락/실패 | 로즈 |
| 중립 | 앰버 |

---

## 6. 인증

- Auth Server 유지 (9000 포트)
- JWT 토큰 (14분 갱신)
- 역할 기반 접근 제어
  - `user`: 일반 페이지
  - `admin`: Admin 페이지 추가 접근

---

## 7. 데이터 통신

- 방식: Polling (5초 간격)
- 클라이언트: Axios
- 상태 관리: TanStack Query

---

## 8. 참고

- [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/)
- [shadcn/ui](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query)
