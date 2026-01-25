# Bitcoin Auto Trading - Frontend

![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-06B6D4?logo=tailwindcss&logoColor=white)

비트코인 자동 거래 시스템의 프론트엔드 대시보드입니다.

## Tech Stack

- **Framework**: React 18.3 + TypeScript 5.6
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3 + shadcn/ui
- **Charts**: TradingView Lightweight Charts
- **State Management**: TanStack Query v5
- **Routing**: React Router v6

## 설치 및 실행

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+ or pnpm
- Backend server running on port 8000
- Auth server running on port 9000

### 개발 환경 설정

```bash
# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일을 수정하여 API URL 설정

# 개발 서버 실행
npm run dev
```

개발 서버: http://localhost:5173

### 프로덕션 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `VITE_API_URL` | 백엔드 API 서버 URL | `http://localhost:8000` |
| `VITE_AUTH_URL` | 인증 서버 URL | `http://localhost:9000` |

## 프로젝트 구조

```
src/
├── core/                   # 공통 모듈
│   ├── api/                # API 클라이언트 (Axios 인스턴스, 인터셉터)
│   ├── components/         # 공통 컴포넌트 + shadcn/ui
│   ├── composables/        # 재사용 훅 (useDebounce, useToggle)
│   ├── contexts/           # React Context (TradingConfig)
│   ├── layouts/            # 레이아웃 (MainLayout, AuthLayout)
│   ├── errors/             # 에러 클래스
│   ├── types/              # TypeScript 타입 정의
│   └── utils/              # 유틸리티 (formatters, cn)
│
├── api/                    # 도메인 API 함수
│   ├── market.api.ts
│   ├── dashboard.api.ts
│   ├── signals.api.ts
│   ├── trading.api.ts
│   ├── portfolio.api.ts
│   ├── config.api.ts
│   ├── admin.api.ts
│   └── mocks/              # Mock 데이터 (백엔드 미구현 API용)
│
├── stores/                 # 상태 관리 (Auth Context)
│
├── components/             # 도메인 컴포넌트
│   ├── dashboard/          # 대시보드 (차트, 지표, 메트릭 카드)
│   ├── trading/            # 거래 (주문 테이블, 상태 배지)
│   ├── signals/            # AI 신호 (카드, 타임라인, 모달)
│   ├── portfolio/          # 포트폴리오 (수익 카드, 차트)
│   ├── settings/           # 설정 (폼, 섹션)
│   └── admin/              # 관리자 (시스템 리소스, 스케줄러)
│
├── views/                  # 페이지 컴포넌트
│   ├── DashboardView.tsx
│   ├── PortfolioView.tsx
│   ├── SignalsView.tsx
│   ├── OrdersView.tsx
│   ├── SettingsView.tsx
│   ├── AdminView.tsx
│   └── LoginView.tsx
│
├── router/                 # 라우팅
│   ├── routes.tsx          # 라우트 정의 (React.lazy 코드 분할)
│   ├── ProtectedRoute.tsx  # 인증 필요 라우트 가드
│   └── AdminRoute.tsx      # 관리자 전용 라우트 가드
│
└── assets/                 # 정적 리소스
    └── styles/             # CSS
```

## 주요 기능

### 1. 대시보드 (Dashboard)
- 실시간 BTC/KRW 캔들스틱 차트
- 기술적 지표 (MA 20/50/200, RSI, MACD)
- 현재 포지션 및 잔고 표시
- 최신 AI 신호 카드
- 5초 자동 갱신

### 2. 포트폴리오 (Portfolio)
- 누적 수익률 및 오늘 수익률
- 승률, 평균 수익률, MDD 통계
- 30일 수익 차트

### 3. AI 신호 (Signals)
- 그리드/타임라인 뷰 전환
- BUY/SELL/HOLD 타입별 필터링
- 신호 상세 모달
- 수동 신호 생성

### 4. 주문 내역 (Orders)
- 주문 테이블 (가로 스크롤 지원)
- 상태별 필터링 (전체/대기/체결/취소/실패)
- 페이지네이션
- 대기 주문 동기화

### 5. 설정 (Settings)
- 거래 설정 (포지션 크기, 손절매, 일일 한도)
- AI 설정 (모델, 신호 주기)
- 실시간 유효성 검사
- 기본값 초기화

### 6. 관리자 (Admin)
- 시스템 리소스 모니터링 (CPU, 메모리)
- 디스크 사용량 (70% 경고)
- 데이터베이스 상태
- 스케줄러 작업 상태
- 10초 자동 갱신

## 명령어

```bash
# 개발
npm run dev           # 개발 서버 시작 (HMR)
npm run build         # 프로덕션 빌드
npm run preview       # 빌드 결과 미리보기

# 린트
npm run lint          # ESLint 검사
npm run lint:fix      # ESLint 자동 수정

# shadcn/ui 컴포넌트 추가
npx shadcn@latest add [component-name]
```

## 성능 최적화

- **코드 분할**: React.lazy로 모든 뷰 컴포넌트 지연 로딩
- **캐싱**: TanStack Query gcTime 5분, staleTime 최적화
- **자동 재시도**: 네트워크 오류 시 지수 백오프로 최대 3회 재시도
- **페이지 전환 애니메이션**: 부드러운 UX
- **타임아웃 처리**: 5초 이상 로딩 시 사용자 안내 메시지

## 브라우저 지원

- Chrome (최신 2개 버전)
- Firefox (최신 2개 버전)
- Safari (최신 2개 버전)
- Edge (최신 2개 버전)
- 모바일: 640px+ 반응형 지원
