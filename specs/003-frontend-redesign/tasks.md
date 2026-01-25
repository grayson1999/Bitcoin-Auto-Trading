# 태스크: 프론트엔드 재설계 - 비트코인 자동 거래 대시보드

**입력**: `/specs/003-frontend-redesign/` 설계 문서
**사전 요구사항**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**테스트**: 명시적 요청 없음 - 테스트 태스크 생략 (필요시 개발 테스트만)

**구성**: 태스크는 사용자 스토리별로 그룹화되어 각 스토리를 독립적으로 구현하고 테스트할 수 있음

## 형식: `[ID] [P?] [Story] 설명`

- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- **[Story]**: 해당 태스크가 속한 사용자 스토리 (예: US1, US2, US3)
- 설명에 정확한 파일 경로 포함

## 경로 규칙

- **웹 앱 (프론트엔드만)**: `frontend/src/`
- 모든 경로는 저장소 루트 `/home/ubuntu/Bitcoin-Auto-Trading/` 기준 상대 경로

---

## Phase 1: 셋업 (프로젝트 초기화)

**목적**: 기존 프론트엔드 삭제 및 필수 의존성과 함께 새 프로젝트 초기화

- [X] T001 기존 프론트엔드 디렉토리를 `frontend_backup_YYYYMMDD`로 백업
- [X] T002 `frontend/`에 새 Vite + React + TypeScript 프로젝트 초기화
- [X] T003 핵심 의존성 설치 (react-router-dom, @tanstack/react-query, axios, lightweight-charts)
- [X] T004 [P] shadcn/ui 의존성 설치 (clsx, tailwind-merge, class-variance-authority, lucide-react)
- [X] T005 [P] 개발 의존성 설치 (vitest, @testing-library/react, @types/node)
- [X] T006 `frontend/tailwind.config.js`에 커스텀 테마 색상으로 Tailwind CSS 구성
- [X] T007 [P] `frontend/tsconfig.json`과 `frontend/vite.config.ts`에 경로 별칭 구성
- [X] T008 shadcn/ui 초기화 및 컴포넌트 설치 (button, card, dialog, table, tabs, select, input, badge, skeleton, alert, tooltip, dropdown-menu, progress, slider, switch)
- [X] T009 plan.md 기준으로 `frontend/src/`에 폴더 구조 생성 (core/, api/, stores/, components/, views/, router/, assets/)
- [X] T010 [P] `frontend/`에 환경 파일 `.env`와 `.env.production` 생성

---

## Phase 2: 기반 구축 (핵심 인프라)

**목적**: 모든 사용자 스토리 구현 전에 반드시 완료해야 하는 핵심 인프라

**⚠️ 중요**: 이 단계가 완료될 때까지 사용자 스토리 작업을 시작할 수 없음

### 코어 레이어

- [X] T011 `frontend/src/core/types/index.ts`에 TypeScript 타입과 열거형 생성 (data-model.md 기반)
- [X] T012 `frontend/src/core/api/client.ts`에 인증 인터셉터가 포함된 API 클라이언트 생성
- [X] T013 [P] `frontend/src/core/errors/ApiError.ts`에 ApiError 클래스 생성
- [X] T014 [P] `frontend/src/core/utils/formatters.ts`에 유틸리티 포매터 생성 (통화, 날짜, 퍼센트)
- [X] T015 [P] `frontend/src/core/utils/cn.ts`에 Tailwind 클래스용 cn() 유틸리티 생성
- [X] T016 [P] `frontend/src/core/composables/useDebounce.ts`에 useDebounce 훅 생성
- [X] T017 [P] `frontend/src/core/composables/useToggle.ts`에 useToggle 훅 생성

### 인증 인프라

- [X] T018 `frontend/src/stores/auth.store.tsx`에 AuthContext와 AuthProvider 생성
- [X] T019 `frontend/src/api/auth.api.ts`에 인증 API 함수 생성 (login, logout, refresh)
- [X] T020 `frontend/src/router/ProtectedRoute.tsx`에 ProtectedRoute 컴포넌트 생성
- [X] T021 `frontend/src/router/AdminRoute.tsx`에 AdminRoute 컴포넌트 생성

### 레이아웃 컴포넌트

- [X] T022 `frontend/src/core/layouts/MainLayout.tsx`에 사이드바 네비게이션 포함 MainLayout 생성
- [X] T023 [P] `frontend/src/core/layouts/AuthLayout.tsx`에 로그인 페이지용 AuthLayout 생성
- [X] T024 `frontend/src/core/components/Sidebar.tsx`에 반응형 사이드바 컴포넌트 생성

### 공통 컴포넌트

- [X] T025 [P] `frontend/src/core/components/CommonButton.tsx`에 CommonButton 래퍼 생성
- [X] T026 [P] `frontend/src/core/components/CommonCard.tsx`에 CommonCard 래퍼 생성
- [X] T027 [P] `frontend/src/core/components/CommonModal.tsx`에 CommonModal 래퍼 생성
- [X] T028 [P] `frontend/src/core/components/LoadingSpinner.tsx`에 LoadingSpinner 컴포넌트 생성
- [X] T029 [P] `frontend/src/core/components/ErrorMessage.tsx`에 ErrorMessage 컴포넌트 생성
- [X] T030 [P] `frontend/src/core/components/EmptyState.tsx`에 EmptyState 컴포넌트 생성

### 라우팅 설정

- [X] T031 `frontend/src/router/routes.tsx`에 라우트 정의 생성
- [X] T032 `frontend/src/router/index.tsx`에 프로바이더 포함 라우터 인덱스 생성
- [X] T033 `frontend/src/main.tsx`에 QueryClient, BrowserRouter, AuthProvider 업데이트
- [X] T034 `frontend/src/views/LoginView.tsx`에 LoginView 페이지 생성

### 글로벌 스타일

- [X] T035 `frontend/src/assets/styles/index.css`에 다크 테마 기본 스타일로 글로벌 CSS 업데이트
- [X] T036 `frontend/src/App.tsx`에서 라우터 렌더링하도록 App.tsx 업데이트

**체크포인트**: 기반 구축 완료 - 사용자 스토리 구현을 병렬로 시작할 수 있음

---

## Phase 3: 사용자 스토리 1 - 실시간 시세 및 포지션 모니터링 (우선순위: P1) 🎯 MVP

**목표**: 캔들스틱 차트, 기술적 지표, 포지션 표시, 잔고 표시, 자동 갱신이 포함된 대시보드

**독립 테스트**: 사용자가 로그인하고, 대시보드에 접속하여 지표가 포함된 실시간 BTC 차트를 보고, 포지션과 잔고를 확인할 수 있음

### US1용 API 레이어

- [X] T037 [P] [US1] `frontend/src/api/market.api.ts`에 시장 API 함수 생성
- [X] T038 [P] [US1] `frontend/src/api/dashboard.api.ts`에 대시보드 API 함수 생성
- [X] T039 [P] [US1] `frontend/src/api/trading.api.ts`에 거래 API 함수 생성 (포지션, 잔고)
- [X] T040 [P] [US1] `frontend/src/api/risk.api.ts`에 리스크 API 함수 생성

### US1용 차트 컴포넌트

- [X] T041 [US1] `frontend/src/components/dashboard/PriceChart.tsx`에 TradingView Lightweight Charts로 PriceChart 컴포넌트 생성
- [X] T042 [US1] PriceChart 컴포넌트에 시간 간격 선택기 생성 (1분/5분/15분/1시간)
- [X] T043 [US1] `frontend/src/components/dashboard/indicators/MAIndicator.ts`에 MA 지표 오버레이 구현 (20, 50, 200)
- [X] T044 [P] [US1] `frontend/src/components/dashboard/indicators/RSIIndicator.ts`에 RSI 지표 구현
- [X] T045 [P] [US1] `frontend/src/components/dashboard/indicators/MACDIndicator.ts`에 MACD 지표 구현
- [X] T046 [US1] `frontend/src/components/dashboard/IndicatorControls.tsx`에 IndicatorControls 컴포넌트 생성 (MA/RSI/MACD 토글)

### US1용 대시보드 컴포넌트

- [X] T047 [P] [US1] `frontend/src/components/dashboard/PositionCard.tsx`에 PositionCard 컴포넌트 생성
- [X] T048 [P] [US1] `frontend/src/components/dashboard/BalanceCard.tsx`에 BalanceCard 컴포넌트 생성
- [X] T049 [P] [US1] `frontend/src/components/dashboard/MetricCards.tsx`에 MetricCards 컴포넌트 생성 (가격, 24시간 변동, 일일 손익)
- [X] T050 [P] [US1] `frontend/src/components/dashboard/LatestSignalCard.tsx`에 LatestSignalCard 컴포넌트 생성
- [X] T051 [P] [US1] `frontend/src/components/dashboard/RiskStatusCard.tsx`에 RiskStatusCard 컴포넌트 생성

### US1용 대시보드 뷰

- [X] T052 [US1] `frontend/src/views/DashboardView.tsx`에 모든 대시보드 컴포넌트를 조합한 DashboardView 페이지 생성
- [X] T053 [US1] TanStack Query refetchInterval로 5초 자동 갱신 구현
- [X] T054 [US1] Skeleton 컴포넌트로 로딩 상태 추가
- [X] T055 [US1] 재시도 기능이 포함된 에러 처리 추가

**체크포인트**: 사용자 스토리 1 완료 - 실시간 차트, 지표, 포지션, 잔고가 포함된 대시보드 동작

---

## Phase 4: 사용자 스토리 2 - 포트폴리오 수익 현황 확인 (우선순위: P1)

**목표**: 누적 수익률, 오늘 수익률, 승률, MDD, 수익 차트가 포함된 포트폴리오 페이지

**독립 테스트**: 사용자가 포트폴리오 페이지에 접속하여 정확한 수익률 계산을 보고, 30일 수익 차트를 확인할 수 있음

**참고**: 백엔드 API `GET /api/v1/portfolio/summary` 필요 - 사용 불가 시 초기에는 mock 데이터 사용

### US2용 API 레이어

- [X] T056 [P] [US2] `frontend/src/api/portfolio.api.ts`에 포트폴리오 API 함수 생성
- [X] T057 [P] [US2] `frontend/src/api/mocks/portfolio.mock.ts`에 포트폴리오 요약 mock 데이터 폴백 생성

### US2용 포트폴리오 컴포넌트

- [X] T058 [P] [US2] `frontend/src/components/portfolio/CumulativeReturnCard.tsx`에 CumulativeReturnCard 컴포넌트 생성
- [X] T059 [P] [US2] `frontend/src/components/portfolio/TodayReturnCard.tsx`에 TodayReturnCard 컴포넌트 생성
- [X] T060 [P] [US2] `frontend/src/components/portfolio/TradeStatsCard.tsx`에 TradeStatsCard 컴포넌트 생성 (승률, 평균 수익률, MDD)
- [X] T061 [US2] `frontend/src/components/portfolio/ProfitChart.tsx`에 ProfitChart 컴포넌트 생성 (30일 라인 차트)
- [X] T062 [P] [US2] `frontend/src/components/portfolio/DepositHistoryCard.tsx`에 DepositHistoryCard 컴포넌트 생성

### US2용 포트폴리오 뷰

- [X] T063 [US2] `frontend/src/views/PortfolioView.tsx`에 모든 포트폴리오 컴포넌트를 조합한 PortfolioView 페이지 생성
- [X] T064 [US2] 거래 기록이 없는 사용자를 위한 빈 상태 구현
- [X] T065 [US2] 로딩 및 에러 상태 추가

**체크포인트**: 사용자 스토리 2 완료 - 정확한 수익률 계산이 포함된 포트폴리오 페이지 동작

---

## Phase 5: 사용자 스토리 3 - AI 신호 확인 및 분석 (우선순위: P2)

**목표**: 카드 그리드, 타임라인 뷰, 타입 필터, 상세 모달이 포함된 신호 페이지

**독립 테스트**: 사용자가 그리드/타임라인에서 AI 신호를 보고, 타입별로 필터링하고, 클릭하여 상세 모달을 확인할 수 있음

### US3용 API 레이어

- [X] T066 [P] [US3] `frontend/src/api/signal.api.ts`에 신호 API 함수 생성

### US3용 신호 컴포넌트

- [X] T067 [P] [US3] `frontend/src/components/signals/SignalCard.tsx`에 SignalCard 컴포넌트 생성 (BUY/SELL/HOLD 색상)
- [X] T068 [P] [US3] `frontend/src/components/signals/SignalTimeline.tsx`에 SignalTimeline 컴포넌트 생성
- [X] T069 [US3] `frontend/src/components/signals/SignalDetailModal.tsx`에 SignalDetailModal 컴포넌트 생성
- [X] T070 [P] [US3] `frontend/src/components/signals/SignalTypeFilter.tsx`에 SignalTypeFilter 컴포넌트 생성
- [X] T071 [P] [US3] `frontend/src/components/signals/ViewToggle.tsx`에 ViewToggle 컴포넌트 생성 (그리드/타임라인)

### US3용 신호 뷰

- [X] T072 [US3] `frontend/src/views/SignalsView.tsx`에 그리드와 타임라인 모드가 포함된 SignalsView 페이지 생성
- [X] T073 [US3] 신호 타입 필터링 구현 (BUY/SELL/HOLD/전체)
- [X] T074 [US3] 신호 목록 페이지네이션 구현
- [X] T075 [US3] 로딩 및 빈 상태 추가

**체크포인트**: 사용자 스토리 3 완료 - 그리드/타임라인 뷰와 필터링이 포함된 신호 페이지 동작

---

## Phase 6: 사용자 스토리 4 - 주문 내역 조회 (우선순위: P2)

**목표**: 테이블, 상태 필터, 페이지네이션이 포함된 주문 페이지

**독립 테스트**: 사용자가 주문 내역을 보고, 상태별로 필터링하고, 페이지를 이동할 수 있음

### US4용 주문 컴포넌트

- [X] T076 [P] [US4] `frontend/src/components/trading/OrderTable.tsx`에 OrderTable 컴포넌트 생성 (ID, 타입, 가격, 수량, 상태, 시간 컬럼)
- [X] T077 [P] [US4] `frontend/src/components/trading/OrderStatusFilter.tsx`에 OrderStatusFilter 컴포넌트 생성
- [X] T078 [P] [US4] `frontend/src/components/trading/OrderStatusBadge.tsx`에 OrderStatusBadge 컴포넌트 생성
- [X] T079 [P] [US4] `frontend/src/core/components/Pagination.tsx`에 Pagination 컴포넌트 생성

### US4용 주문 뷰

- [X] T080 [US4] `frontend/src/views/OrdersView.tsx`에 테이블과 필터가 포함된 OrdersView 페이지 생성
- [X] T081 [US4] 상태 필터링 구현 (전체/대기/체결/취소/실패)
- [X] T082 [US4] 페이지네이션 구현 (페이지당 20개 항목)
- [X] T083 [US4] 로딩 및 빈 상태 추가

**체크포인트**: 사용자 스토리 4 완료 - 필터링과 페이지네이션이 포함된 주문 페이지 동작

---

## Phase 7: 사용자 스토리 5 - 시스템 설정 관리 (우선순위: P2)

**목표**: 거래 파라미터, AI 설정, 초기화 기능이 포함된 설정 페이지

**독립 테스트**: 사용자가 설정을 보고 수정하고, 기본값으로 초기화하고, 성공/에러 메시지를 확인할 수 있음

### US5용 API 레이어

- [X] T084 [P] [US5] `frontend/src/api/config.api.ts`에 설정 API 함수 생성

### US5용 설정 컴포넌트

- [X] T085 [P] [US5] `frontend/src/components/settings/TradingSettingsForm.tsx`에 TradingSettingsForm 컴포넌트 생성 (포지션 크기, 손절매, 일일 한도)
- [X] T086 [P] [US5] `frontend/src/components/settings/AISettingsForm.tsx`에 AISettingsForm 컴포넌트 생성 (모델, 신호 주기)
- [X] T087 [P] [US5] `frontend/src/components/settings/ResetSettingsButton.tsx`에 ResetSettingsButton 컴포넌트 생성
- [X] T088 [P] [US5] `frontend/src/components/settings/SettingsSection.tsx`에 SettingsSection 래퍼 컴포넌트 생성

### US5용 설정 뷰

- [X] T089 [US5] `frontend/src/views/SettingsView.tsx`에 모든 설정 폼이 포함된 SettingsView 페이지 생성
- [X] T090 [US5] 숫자 입력 폼 유효성 검사 구현
- [X] T091 [US5] 성공/에러 토스트 알림과 함께 저장 기능 구현
- [X] T092 [US5] 확인 다이얼로그와 함께 기본값 초기화 구현

**체크포인트**: 사용자 스토리 5 완료 - 저장 및 초기화 기능이 포함된 설정 페이지 동작

---

## Phase 8: 사용자 스토리 6 - 관리자 서버 모니터링 (우선순위: P3)

**목표**: 스케줄러 상태, DB 상태, 시스템 리소스, 디스크 사용량이 포함된 관리자 전용 페이지

**독립 테스트**: 관리자는 시스템 메트릭을 볼 수 있고, 일반 사용자는 차단되어 리다이렉트됨(일반 사용자는 메뉴 자체에서도 접근할 수 없음)

**참고**: 백엔드 API `GET /api/v1/admin/system` 필요 - 사용 불가 시 초기에는 mock 데이터 사용

### US6용 API 레이어

- [X] T093 [P] [US6] `frontend/src/api/admin.api.ts`에 관리자 API 함수 생성
- [X] T094 [P] [US6] `frontend/src/api/health.api.ts`에 헬스 API 함수 생성
- [X] T095 [P] [US6] `frontend/src/api/mocks/admin.mock.ts`에 관리자 시스템 메트릭 mock 데이터 폴백 생성

### US6용 관리자 컴포넌트

- [X] T096 [P] [US6] `frontend/src/components/admin/SchedulerStatus.tsx`에 SchedulerStatus 컴포넌트 생성
- [X] T097 [P] [US6] `frontend/src/components/admin/DatabaseStatus.tsx`에 DatabaseStatus 컴포넌트 생성
- [X] T098 [P] [US6] `frontend/src/components/admin/SystemResources.tsx`에 SystemResources 컴포넌트 생성 (CPU, 메모리)
- [X] T099 [P] [US6] `frontend/src/components/admin/DiskUsage.tsx`에 70% 경고가 포함된 DiskUsage 컴포넌트 생성
- [X] T100 [P] [US6] `frontend/src/components/admin/SystemHealthOverview.tsx`에 SystemHealthOverview 컴포넌트 생성

### US6용 관리자 뷰

- [X] T101 [US6] `frontend/src/views/AdminView.tsx`에 모든 관리자 컴포넌트를 조합한 AdminView 페이지 생성
- [X] T102 [US6] AdminRoute 가드 구현 (비관리자는 대시보드로 리다이렉트)
- [X] T103 [US6] 시스템 메트릭 자동 갱신 구현 (10초 간격)
- [X] T104 [US6] Skeleton 컴포넌트로 로딩 상태 추가

**체크포인트**: 사용자 스토리 6 완료 - 시스템 모니터링이 포함된 관리자 페이지 동작 (관리자 전용 접근)

---

## Phase 9: 마무리 및 공통 관심사

**목적**: 여러 사용자 스토리에 영향을 미치는 개선 사항

### 반응형 디자인

- [ ] T105 [P] MainLayout과 Sidebar의 모바일 반응형 확인 (640px 브레이크포인트)
- [ ] T106 [P] DashboardView의 모바일 반응형 확인 (차트 높이 조정)
- [ ] T107 [P] OrderTable의 모바일 반응형 확인 (가로 스크롤)
- [ ] T108 [P] 모바일 뷰포트(640px)에서 모든 페이지 테스트

### 에러 처리 및 엣지 케이스

- [ ] T109 [P] 모든 뷰에 재시도 버튼이 포함된 네트워크 에러 처리 구현
- [ ] T110 [P] 로딩 타임아웃 처리 구현 (5초 타임아웃 메시지)
- [ ] T111 [P] 세션 만료 처리 구현 (로그인으로 자동 리다이렉트)

### 성능 및 UX

- [ ] T112 [P] React.lazy로 라우트 기반 코드 분할 추가
- [ ] T113 [P] 최적의 UX를 위한 TanStack Query 캐시 설정 최적화
- [ ] T114 [P] 페이지 전환 애니메이션 추가 (선택사항)

### 최종 검증

- [ ] T115 quickstart.md 검증 체크리스트 실행
- [ ] T116 모든 사용자 스토리가 독립적으로 동작하는지 확인
- [ ] T117 프로덕션 빌드 실행 및 에러 없음 확인 (`npm run build`)
- [ ] T118 frontend/README.md에 설정 가이드 업데이트

---

## 의존성 및 실행 순서

### Phase 의존성

- **셋업 (Phase 1)**: 의존성 없음 - 즉시 시작 가능
- **기반 구축 (Phase 2)**: 셋업 완료에 의존 - 모든 사용자 스토리 차단
- **사용자 스토리 (Phase 3-8)**: 모두 기반 구축 완료에 의존
  - 인력이 있으면 사용자 스토리를 병렬로 진행 가능
  - 또는 우선순위 순서대로 순차 진행 (P1 → P2 → P3)
- **마무리 (Phase 9)**: 원하는 모든 사용자 스토리 완료에 의존

### 사용자 스토리 의존성

- **사용자 스토리 1 (P1)**: 대시보드 - 다른 스토리에 대한 의존성 없음
- **사용자 스토리 2 (P1)**: 포트폴리오 - 다른 스토리에 대한 의존성 없음 (다른 API 사용)
- **사용자 스토리 3 (P2)**: 신호 - 다른 스토리에 대한 의존성 없음
- **사용자 스토리 4 (P2)**: 주문 - 다른 스토리에 대한 의존성 없음
- **사용자 스토리 5 (P2)**: 설정 - 다른 스토리에 대한 의존성 없음
- **사용자 스토리 6 (P3)**: 관리자 - 다른 스토리에 대한 의존성 없음 (관리자 역할 필요)

### 각 사용자 스토리 내부

- API 레이어 먼저 (컴포넌트 활성화)
- 컴포넌트는 병렬로 빌드 가능 [P]
- 뷰 페이지는 컴포넌트를 조합 (컴포넌트에 의존)
- 로딩/에러 상태는 메인 구현 이후

### 병렬 실행 기회

- [P]로 표시된 모든 셋업 태스크는 병렬 실행 가능
- [P]로 표시된 모든 기반 구축 태스크는 병렬 실행 가능
- **기반 구축 완료 후, 모든 6개 사용자 스토리를 병렬로 시작 가능** (다른 파일, 충돌 없음)
- 스토리 내의 [P]로 표시된 모든 컴포넌트는 병렬 실행 가능
- [P]로 표시된 모든 마무리 태스크는 병렬 실행 가능

---

## 병렬 실행 예시: 기반 구축 Phase 이후

```bash
# 개발자 A: 사용자 스토리 1 (대시보드)
태스크: "frontend/src/api/market.api.ts에 시장 API 함수 생성"
태스크: "frontend/src/components/dashboard/PriceChart.tsx에 PriceChart 컴포넌트 생성"
...

# 개발자 B: 사용자 스토리 2 (포트폴리오)
태스크: "frontend/src/api/portfolio.api.ts에 포트폴리오 API 함수 생성"
태스크: "frontend/src/components/portfolio/ProfitChart.tsx에 ProfitChart 컴포넌트 생성"
...

# 개발자 C: 사용자 스토리 3 (신호)
태스크: "frontend/src/api/signal.api.ts에 신호 API 함수 생성"
태스크: "frontend/src/components/signals/SignalCard.tsx에 SignalCard 컴포넌트 생성"
...
```

---

## 병렬 실행 예시: 사용자 스토리 1 내부 (컴포넌트)

```bash
# 이 모든 것은 병렬 실행 가능 (다른 파일):
태스크: "[US1] frontend/src/components/dashboard/PositionCard.tsx에 PositionCard 컴포넌트 생성"
태스크: "[US1] frontend/src/components/dashboard/BalanceCard.tsx에 BalanceCard 컴포넌트 생성"
태스크: "[US1] frontend/src/components/dashboard/MetricCards.tsx에 MetricCards 컴포넌트 생성"
태스크: "[US1] frontend/src/components/dashboard/LatestSignalCard.tsx에 LatestSignalCard 컴포넌트 생성"
태스크: "[US1] frontend/src/components/dashboard/RiskStatusCard.tsx에 RiskStatusCard 컴포넌트 생성"
```

---

## 구현 전략

### MVP 먼저 (사용자 스토리 1만)

1. Phase 1: 셋업 완료
2. Phase 2: 기반 구축 완료 (중요 - 모든 스토리 차단)
3. Phase 3: 사용자 스토리 1 (대시보드) 완료
4. **중지 및 검증**: 대시보드 독립적으로 테스트 - 사용자가 로그인하고, 차트를 보고, 포지션 확인 가능
5. 준비되면 배포/데모 - 대시보드만으로도 모니터링 가치 제공

### 권장 점진적 배포

1. **MVP**: 셋업 + 기반 구축 + US1 (대시보드) → 핵심 모니터링
2. **+포트폴리오**: US2 추가 → 투자 성과 추적
3. **+신호**: US3 추가 → AI 분석 검토
4. **+주문**: US4 추가 → 거래 내역 확인
5. **+설정**: US5 추가 → 파라미터 커스터마이징
6. **+관리자**: US6 추가 → 시스템 모니터링 (관리자 전용)

### 병렬 팀 전략 (3명 개발자)

1. 팀이 함께 셋업 + 기반 구축 완료
2. 기반 구축 완료 후:
   - 개발자 A: 사용자 스토리 1 (대시보드) + 사용자 스토리 4 (주문)
   - 개발자 B: 사용자 스토리 2 (포트폴리오) + 사용자 스토리 5 (설정)
   - 개발자 C: 사용자 스토리 3 (신호) + 사용자 스토리 6 (관리자)
3. 스토리 완료 후 독립적으로 통합

---

## 백엔드 API 참고

### 기존 API (준비됨)
US1, US3, US4, US5용 모든 API 사용 가능:
- `/api/v1/market`, `/api/v1/market/history`
- `/api/v1/dashboard/summary`
- `/api/v1/signals`, `/api/v1/signals/latest`
- `/api/v1/trading/orders`, `/api/v1/trading/position`, `/api/v1/trading/balance`
- `/api/v1/config`, `/api/v1/config/{key}`
- `/api/v1/risk/status`
- `/api/v1/health/detail`

### 새로 필요한 API (백엔드 작업)
- **US2**: `GET /api/v1/portfolio/summary`, `GET /api/v1/portfolio/deposits`
- **US6**: `GET /api/v1/admin/system`

백엔드가 이 API를 구현하는 동안 프론트엔드는 mock 데이터 사용 가능

---

## 참고사항

- [P] 태스크 = 다른 파일, 의존성 없음
- [Story] 라벨은 태스크를 특정 사용자 스토리에 매핑하여 추적성 확보
- 각 사용자 스토리는 독립적으로 완료하고 테스트할 수 있어야 함
- 각 태스크 또는 논리적 그룹 후 커밋
- 스토리를 독립적으로 검증하려면 체크포인트에서 중지
- 피해야 할 것: 모호한 태스크, 같은 파일 충돌, 독립성을 깨는 스토리 간 의존성
