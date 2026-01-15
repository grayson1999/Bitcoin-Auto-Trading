# 태스크: Bitcoin Auto-Trading System

**입력**: `/specs/001-bitcoin-auto-trading/` 설계 문서
**전제조건**: plan.md (필수), spec.md (필수), research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**구성**: 태스크는 사용자 스토리별로 그룹화되어 각 스토리를 독립적으로 구현하고 테스트할 수 있습니다.

## 형식: `[ID] [P?] [Story] 설명`

- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- **[Story]**: 해당 태스크가 속한 사용자 스토리 (예: US1, US2, US3)
- 설명에 정확한 파일 경로 포함

## 경로 규칙

- **Backend**: `backend/src/`
- **Frontend**: `frontend/src/`
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: 셋업 (공유 인프라)

**목적**: 프로젝트 초기화, 기본 구조 및 설정

- [x] T001 plan.md에 따라 모노레포 디렉토리 구조 생성 (backend/, frontend/, docker-compose.yml, Makefile)
- [x] T002 [P] pyproject.toml과 의존성으로 백엔드 Python 프로젝트 초기화 (FastAPI, httpx, SQLAlchemy 2.0, APScheduler, google-generativeai, pydantic, loguru)
- [x] T003 [P] Vite, TypeScript, 의존성으로 프론트엔드 React 프로젝트 초기화 (react-router-dom, @tanstack/react-query, recharts, tailwindcss, axios)
- [x] T004 [P] 모든 필수 환경 변수가 포함된 backend/.env.example 생성
- [x] T005 [P] backend, frontend, PostgreSQL 서비스가 포함된 docker-compose.yml 생성
- [x] T006 [P] dev, test, build 명령어가 포함된 Makefile 생성

---

## Phase 2: 기반 구축 (필수 선행 조건)

**목적**: 모든 사용자 스토리 구현 전에 반드시 완료해야 하는 핵심 인프라

**⚠️ 중요**: 이 단계가 완료될 때까지 사용자 스토리 작업을 시작할 수 없습니다

- [x] T007 backend/src/config.py에 Pydantic Settings로 설정 관리 생성
- [x] T008 backend/src/database.py에 SQLAlchemy 비동기 엔진 및 세션 팩토리 설정
- [x] T009 backend/alembic/에 Alembic 마이그레이션 프레임워크 초기화
- [x] T010 [P] backend/src/models/__init__.py에 기본 SQLAlchemy 모델 클래스 생성
- [x] T011 [P] backend/src/config.py에 loguru 로거 설정 구성
- [x] T012 backend/src/main.py에 lifespan, CORS, 오류 핸들러가 포함된 FastAPI 앱 생성
- [x] T013 [P] backend/src/api/__init__.py에 버전 관리가 포함된 API 라우터 구조 설정
- [x] T014 [P] backend/src/api/health.py에 헬스체크 엔드포인트 구현
- [x] T015 [P] frontend/src/api/client.ts에 axios로 프론트엔드 API 클라이언트 생성
- [x] T016 [P] frontend/src/App.tsx에 페이지 구조가 포함된 React Router 설정
- [x] T017 [P] frontend/tailwind.config.js에 Tailwind CSS 구성
- [x] T018 [P] frontend/src/main.tsx에 React Query 프로바이더 설정

**체크포인트**: 기반 구축 완료 - 사용자 스토리 구현 시작 가능

---

## Phase 3: 사용자 스토리 3 - 실시간 시장 데이터 수집 (우선순위: P1) 🎯 MVP

**목표**: AI 분석의 기반이 되는 Upbit의 실시간 비트코인 가격, 거래량, 체결 정보 수집

**독립 테스트**: 데이터 수집 모듈만 실행하여 Upbit에서 실시간 데이터가 정상적으로 수신되고 저장되는지 확인

**첫 번째 이유**: 이 스토리는 US4(AI 신호)와 US1(자동 매매)이 의존하는 입력 데이터를 제공

### 사용자 스토리 3 구현

- [x] T019 [P] [US3] backend/src/models/market_data.py에 MarketData SQLAlchemy 모델 생성
- [x] T020 [US3] MarketData 테이블용 Alembic 마이그레이션 생성
- [x] T021 [US3] backend/src/services/upbit_client.py에 JWT 인증이 포함된 Upbit API 클라이언트 구현
- [x] T022 [US3] backend/src/services/data_collector.py에 시장 데이터 수집용 DataCollector 서비스 구현
- [x] T023 [US3] backend/src/api/schemas/market.py에 MarketData API 응답용 Pydantic 스키마 생성
- [x] T024 [US3] backend/src/api/dashboard.py에 GET /dashboard/market 엔드포인트 구현
- [x] T025 [US3] backend/src/scheduler/jobs.py에 1초 주기 데이터 수집용 APScheduler 작업 설정
- [x] T026 [US3] backend/src/services/data_collector.py에 네트워크 장애 시 자동 재연결 로직 추가
- [x] T027 [US3] backend/src/services/data_collector.py에 데이터 수집 이벤트 로깅 추가

**체크포인트**: Upbit에서 데이터 수집이 작동하고 시장 데이터가 저장됨

---

## Phase 4: 사용자 스토리 4 - AI 기반 매매 신호 생성 (우선순위: P1)

**목표**: Gemini 2.5 Flash AI를 사용하여 신뢰도 점수와 함께 Buy/Hold/Sell 신호 생성

**독립 테스트**: 과거 시장 데이터를 입력하고 올바른 형식(Buy/Hold/Sell + 신뢰도 0-1)으로 신호가 반환되는지 확인

**의존**: US3 (분석을 위한 시장 데이터 필요)

### 사용자 스토리 4 구현

- [x] T028 [P] [US4] backend/src/models/trading_signal.py에 TradingSignal SQLAlchemy 모델 생성
- [x] T029 [US4] TradingSignal 테이블용 Alembic 마이그레이션 생성
- [x] T030 [US4] backend/src/services/ai_client.py에 google-generativeai SDK로 Gemini AI 클라이언트 구현
- [x] T031 [US4] backend/src/services/signal_generator.py에 매매 신호 프롬프트 템플릿 생성
- [x] T032 [US4] backend/src/services/signal_generator.py에 시장 데이터 전처리가 포함된 SignalGenerator 서비스 구현
- [x] T033 [US4] backend/src/api/schemas/signal.py에 TradingSignal용 Pydantic 스키마 생성
- [x] T034 [US4] backend/src/api/signals.py에 GET /signals 엔드포인트 구현
- [x] T035 [US4] backend/src/api/signals.py에 GET /signals/latest 엔드포인트 구현
- [x] T036 [US4] backend/src/api/signals.py에 POST /signals/generate 엔드포인트 (수동 트리거) 구현
- [x] T037 [US4] backend/src/scheduler/jobs.py에 1시간 주기 신호 생성용 APScheduler 작업 설정
- [x] T038 [US4] backend/src/services/ai_client.py에 AI API 호출 5초 타임아웃 및 재시도 로직 추가
- [x] T039 [US4] backend/src/services/signal_generator.py에 비용 추적용 토큰 사용량 로깅 추가

**체크포인트**: AI 신호 생성이 1시간 스케줄링으로 작동

---

## Phase 5: 사용자 스토리 2 - 리스크 관리 및 자본 보호 (우선순위: P1)

**목표**: 과도한 손실로부터 자본을 보호하기 위한 리스크 규칙 적용 (손절, 일일 한도, 포지션 크기 제한)

**독립 테스트**: 손실 시나리오를 시뮬레이션하고 손절 및 거래 중단 기능이 정상 작동하는지 확인

**의존**: 없음 (기반 구축 완료 후 독립 실행 가능)

### 사용자 스토리 2 구현

- [x] T040 [P] [US2] backend/src/models/risk_event.py에 RiskEvent SQLAlchemy 모델 생성
- [x] T041 [P] [US2] backend/src/models/daily_stats.py에 DailyStats SQLAlchemy 모델 생성
- [x] T042 [P] [US2] backend/src/models/position.py에 Position SQLAlchemy 모델 생성
- [x] T043 [P] [US2] backend/src/models/system_config.py에 SystemConfig SQLAlchemy 모델 생성
- [x] T044 [US2] RiskEvent, DailyStats, Position, SystemConfig 테이블용 Alembic 마이그레이션 생성
- [x] T045 [US2] backend/src/services/risk_manager.py에 포지션 크기 검증이 포함된 RiskManager 서비스 구현
- [x] T046 [US2] backend/src/services/risk_manager.py에 개별 손절 체크 (3-5% 손실 임계값) 추가
- [x] T047 [US2] backend/src/services/risk_manager.py에 일일 손실 한도 체크 및 거래 중단 로직 추가
- [x] T048 [US2] backend/src/services/risk_manager.py에 변동성 감지 (5분 내 3% 초과 변동) 추가
- [x] T049 [US2] backend/src/api/schemas/risk.py에 RiskEvent 및 RiskStatus용 Pydantic 스키마 생성
- [x] T050 [US2] backend/src/api/risk.py에 GET /risk/events 엔드포인트 구현
- [x] T051 [US2] backend/src/api/risk.py에 GET /risk/status 엔드포인트 구현
- [x] T052 [US2] backend/src/api/risk.py에 POST /risk/halt 엔드포인트 구현
- [x] T053 [US2] backend/src/api/risk.py에 POST /risk/resume 엔드포인트 구현
- [x] T054 [US2] backend/src/services/notifier.py에 리스크 알림용 Slack 알림 서비스 구현
- [x] T055 [US2] backend/src/services/risk_manager.py에 모든 리스크 이벤트 로깅 추가

**체크포인트**: 리스크 관리 규칙이 적용되고 거래 중단/재개가 가능

---

## Phase 6: 사용자 스토리 1 - 자동 매매 실행 (우선순위: P1)

**목표**: 리스크 규칙 내에서 AI 신호에 따라 Upbit에서 자동 매수/매도 주문 실행

**독립 테스트**: 테스트 금액으로 AI "Buy" 신호가 Upbit에서 실제 주문 실행을 트리거하는지 확인

**의존**: US3 (시장 데이터), US4 (AI 신호), US2 (리스크 체크)

### 사용자 스토리 1 구현

- [x] T056 [P] [US1] backend/src/models/order.py에 Order SQLAlchemy 모델 생성
- [x] T057 [US1] Order 테이블용 Alembic 마이그레이션 생성
- [x] T058 [US1] backend/src/services/upbit_client.py에 Upbit 주문 실행 (시장가/지정가) 구현
- [x] T059 [US1] backend/src/services/order_executor.py에 리스크 사전 체크가 포함된 OrderExecutor 서비스 구현
- [x] T060 [US1] backend/src/services/order_executor.py에 실패 시 주문 재시도 로직 추가
- [x] T061 [US1] backend/src/services/order_executor.py에 주문 실행 전 잔고 검증 추가
- [x] T062 [US1] backend/src/api/schemas/order.py에 Order용 Pydantic 스키마 생성
- [x] T063 [US1] backend/src/api/trading.py에 GET /trading/orders 엔드포인트 구현
- [x] T064 [US1] backend/src/api/trading.py에 GET /trading/orders/{order_id} 엔드포인트 구현
- [x] T065 [US1] backend/src/api/trading.py에 GET /trading/position 엔드포인트 구현
- [x] T066 [US1] backend/src/api/trading.py에 GET /trading/balance 엔드포인트 구현
- [x] T067 [US1] backend/src/scheduler/jobs.py에 신호 → 리스크 체크 → 주문 실행 플로우 통합
- [x] T068 [US1] backend/src/services/order_executor.py에 주문 실행 후 포지션 업데이트 추가
- [x] T069 [US1] backend/src/services/order_executor.py에 주문 생명주기 종합 로깅 추가

**체크포인트**: 전체 자동 매매 루프 작동 (신호 → 리스크 체크 → 주문 → 포지션 업데이트)

---

## Phase 7: 사용자 스토리 5 - 거래 모니터링 대시보드 (우선순위: P2)

**목표**: 포지션, 거래 내역, 손익, AI 신호를 실시간으로 모니터링하는 웹 대시보드

**독립 테스트**: 대시보드에 접속하여 현재 상태와 거래 내역이 표시되는지 확인

**의존**: US1-4 (거래 운영 데이터 필요)

### 사용자 스토리 5 구현

- [ ] T070 [US5] backend/src/api/dashboard.py에 GET /dashboard/summary 엔드포인트 구현
- [ ] T071 [US5] backend/src/api/schemas/dashboard.py에 DashboardSummary용 Pydantic 스키마 생성
- [ ] T072 [US5] backend/src/api/config.py에 GET /config 엔드포인트 구현
- [ ] T073 [US5] backend/src/api/config.py에 PATCH /config 엔드포인트 구현
- [ ] T074 [P] [US5] frontend/src/pages/Dashboard.tsx에 Dashboard 페이지 컴포넌트 생성
- [ ] T075 [P] [US5] frontend/src/pages/Orders.tsx에 Orders 페이지 컴포넌트 생성
- [ ] T076 [P] [US5] frontend/src/pages/Signals.tsx에 Signals 페이지 컴포넌트 생성
- [ ] T077 [P] [US5] frontend/src/pages/Settings.tsx에 Settings 페이지 컴포넌트 생성
- [ ] T078 [P] [US5] frontend/src/components/PriceChart.tsx에 Recharts로 PriceChart 컴포넌트 생성
- [ ] T079 [P] [US5] frontend/src/components/OrderTable.tsx에 OrderTable 컴포넌트 생성
- [ ] T080 [P] [US5] frontend/src/components/SignalCard.tsx에 SignalCard 컴포넌트 생성
- [ ] T081 [P] [US5] frontend/src/components/RiskStatus.tsx에 RiskStatus 컴포넌트 생성
- [ ] T082 [US5] frontend/src/hooks/useApi.ts에 React Query로 데이터 페칭용 useApi 훅 생성
- [ ] T083 [US5] frontend/src/pages/Dashboard.tsx에 대시보드 데이터 자동 새로고침 (5초 주기) 구현
- [ ] T084 [US5] frontend/src/pages/Dashboard.tsx에 모바일 보기용 반응형 레이아웃 추가

**체크포인트**: 대시보드가 실시간 거래 정보를 표시하고 설정 변경 가능

---

## Phase 8: 사용자 스토리 6 - 백테스팅을 통한 전략 검증 (우선순위: P2)

**목표**: 과거 데이터로 AI 전략을 시뮬레이션하여 수익률, MDD, 승률 계산

**독립 테스트**: 6개월 데이터로 백테스트를 실행하고 지표가 계산되는지 확인

**의존**: US3 (과거 시장 데이터 필요), US4 (신호 생성 로직)

### 사용자 스토리 6 구현

- [ ] T085 [P] [US6] backend/src/models/backtest_result.py에 BacktestResult SQLAlchemy 모델 생성
- [ ] T086 [US6] BacktestResult 테이블용 Alembic 마이그레이션 생성
- [ ] T087 [US6] backend/src/services/backtest_runner.py에 신호 시뮬레이션이 포함된 BacktestRunner 서비스 구현
- [ ] T088 [US6] backend/src/services/backtest_runner.py에 지표 계산 (수익률, MDD, 승률, 손익비) 추가
- [ ] T089 [US6] backend/src/api/schemas/backtest.py에 BacktestRequest 및 BacktestResult용 Pydantic 스키마 생성
- [ ] T090 [US6] backend/src/api/backtest.py에 POST /backtest/run 엔드포인트 구현
- [ ] T091 [US6] backend/src/api/backtest.py에 GET /backtest/results 엔드포인트 구현
- [ ] T092 [US6] backend/src/api/backtest.py에 GET /backtest/results/{result_id} 엔드포인트 구현
- [ ] T093 [P] [US6] frontend/src/pages/Backtest.tsx에 Backtest 페이지 컴포넌트 생성
- [ ] T094 [US6] frontend/src/pages/Backtest.tsx에 백테스트 진행 표시기 및 결과 표시 추가

**체크포인트**: 백테스팅이 실행되고 성과 지표 생성

---

## Phase 9: 마무리 및 공통 관심사

**목적**: 여러 사용자 스토리에 영향을 미치는 개선 사항

- [ ] T095 [P] backend/Dockerfile에 백엔드 Dockerfile 생성
- [ ] T096 [P] frontend/Dockerfile에 Nginx 포함 프론트엔드 Dockerfile 생성
- [ ] T097 backend/src/scheduler/jobs.py에 데이터 보존 정리 작업 (1년 시장 데이터) 구현
- [ ] T098 backend/src/config.py에 로그 내 API 키 마스킹 추가
- [ ] T099 frontend/src/App.tsx에 오류 경계 컴포넌트 추가
- [ ] T100 quickstart.md 검증 실행 (API 연결, 설정, 테스트 거래)

---

## 의존성 및 실행 순서

### Phase 의존성

- **셋업 (Phase 1)**: 의존성 없음 - 즉시 시작 가능
- **기반 구축 (Phase 2)**: 셋업 완료 의존 - 모든 사용자 스토리 차단
- **사용자 스토리 3 (Phase 3)**: 기반 구축 의존 - 첫 번째로 구현할 스토리
- **사용자 스토리 4 (Phase 4)**: US3 의존 (시장 데이터 필요)
- **사용자 스토리 2 (Phase 5)**: 기반 구축만 의존 (US3/US4와 병렬 가능)
- **사용자 스토리 1 (Phase 6)**: US2, US3, US4 의존 (전체 통합)
- **사용자 스토리 5 (Phase 7)**: US1-4 의존 (거래 데이터 필요)
- **사용자 스토리 6 (Phase 8)**: US3, US4 의존 (시장 데이터와 신호 로직 필요)
- **마무리 (Phase 9)**: 모든 원하는 사용자 스토리 완료 의존

### 사용자 스토리 의존성

```
Phase 2: 기반 구축
        ↓
    ┌───┴───┐
    ↓       ↓
  US3 ←── US2 (병렬 실행 가능)
    ↓
  US4
    ↓
┌───┴───┐
↓       ↓
US1     US6
↓
US5
```

- **US3 (시장 데이터)**: 첫 번째 - 모든 것에 데이터 제공
- **US4 (AI 신호)**: US3 시장 데이터 필요
- **US2 (리스크 관리)**: 기반 구축 후 시작 가능 (US3/US4와 독립)
- **US1 (자동 매매)**: US2, US3, US4 모두 완료 필요
- **US5 (대시보드)**: US1-4의 표시할 데이터 필요
- **US6 (백테스팅)**: US3, US4 필요 (시장 데이터 + 신호 로직)

### 각 사용자 스토리 내 순서

- 모델 → 서비스
- 서비스 → 엔드포인트
- 백엔드 엔드포인트 → 프론트엔드 컴포넌트
- 핵심 구현 → 통합

### 병렬 실행 기회

**Phase 1 (셋업)**: T002, T003, T004, T005, T006 모두 병렬

**Phase 2 (기반 구축)**: T007-T009 이후 T010, T011, T014, T015, T016, T017, T018 병렬

**Phase 3 (US3)**: T019 병렬 (모델 생성)

**Phase 4 (US4)**: T028 병렬 (모델 생성)

**Phase 5 (US2)**: T040, T041, T042, T043 모두 병렬 (4개 모델)

**Phase 6 (US1)**: T056 병렬 (모델 생성)

**Phase 7 (US5)**: T074, T075, T076, T077, T078, T079, T080, T081 모두 병렬 (프론트엔드 컴포넌트)

**Phase 8 (US6)**: T085, T093 병렬 (모델 + 프론트엔드 페이지)

**Phase 9 (마무리)**: T095, T096 병렬 (Dockerfile)

---

## 병렬 실행 예시: Phase 2 (기반 구축)

```bash
# 먼저, 순차 설정:
Task T007: "backend/src/config.py에 Pydantic Settings로 설정 관리 생성"
Task T008: "backend/src/database.py에 SQLAlchemy 비동기 엔진 및 세션 팩토리 설정"
Task T009: "backend/alembic/에 Alembic 마이그레이션 프레임워크 초기화"

# 그 다음, 병렬 태스크:
Task T010: "backend/src/models/__init__.py에 기본 SQLAlchemy 모델 클래스 생성"
Task T011: "backend/src/config.py에 loguru 로거 설정 구성"
Task T014: "backend/src/api/health.py에 헬스체크 엔드포인트 구현"
Task T015: "frontend/src/api/client.ts에 axios로 프론트엔드 API 클라이언트 생성"
Task T016: "frontend/src/App.tsx에 페이지 구조가 포함된 React Router 설정"
Task T017: "frontend/tailwind.config.js에 Tailwind CSS 구성"
Task T018: "frontend/src/main.tsx에 React Query 프로바이더 설정"
```

---

## 병렬 실행 예시: 사용자 스토리 5 (대시보드 프론트엔드)

```bash
# 모든 프론트엔드 컴포넌트를 병렬로 빌드 가능:
Task T074: "frontend/src/pages/Dashboard.tsx에 Dashboard 페이지 컴포넌트 생성"
Task T075: "frontend/src/pages/Orders.tsx에 Orders 페이지 컴포넌트 생성"
Task T076: "frontend/src/pages/Signals.tsx에 Signals 페이지 컴포넌트 생성"
Task T077: "frontend/src/pages/Settings.tsx에 Settings 페이지 컴포넌트 생성"
Task T078: "frontend/src/components/PriceChart.tsx에 Recharts로 PriceChart 컴포넌트 생성"
Task T079: "frontend/src/components/OrderTable.tsx에 OrderTable 컴포넌트 생성"
Task T080: "frontend/src/components/SignalCard.tsx에 SignalCard 컴포넌트 생성"
Task T081: "frontend/src/components/RiskStatus.tsx에 RiskStatus 컴포넌트 생성"
```

---

## 구현 전략

### MVP 우선 (전체 자동 매매 루프)

1. Phase 1: 셋업 완료
2. Phase 2: 기반 구축 완료 (중요 - 모든 스토리 차단)
3. Phase 3: US3 (시장 데이터 수집) 완료
4. Phase 4: US4 (AI 신호 생성) 완료
5. Phase 5: US2 (리스크 관리) 완료
6. Phase 6: US1 (자동 매매 실행) 완료
7. **중단 및 검증**: 소액으로 전체 매매 루프 테스트
8. 준비되면 배포/데모

### 점진적 전달

1. 셋업 + 기반 구축 → 기반 준비 완료
2. US3 (시장 데이터) 추가 → Upbit 데이터 수집 작동 확인
3. US4 (AI 신호) 추가 → Gemini API 통합 작동 확인
4. US2 (리스크 관리) 추가 → 리스크 규칙 적용 확인
5. US1 (자동 매매) 추가 → **MVP 완료!** 전체 매매 루프 작동
6. US5 (대시보드) 추가 → 사용자 모니터링 기능
7. US6 (백테스팅) 추가 → 전략 검증 기능

### 권장 MVP 범위

**최소 기능 제품 = Phase 1 + Phase 2 + US3 + US4 + US2 + US1**

이것은 다음을 제공합니다:
- ✅ Upbit에서 데이터 수집
- ✅ Gemini로 AI 신호 생성
- ✅ 리스크 관리 (손절, 일일 한도)
- ✅ 자동 주문 실행
- ❌ 대시보드 (현재는 API/로그 사용)
- ❌ 백테스팅 (소액 실제 거래로 테스트)

---

## 참고 사항

- [P] 태스크 = 다른 파일, 의존성 없음, 병렬 실행 가능
- [Story] 라벨은 추적을 위해 태스크를 특정 사용자 스토리에 매핑
- 각 사용자 스토리는 독립적으로 완료 및 테스트 가능해야 함
- 각 태스크 또는 논리적 그룹 후 커밋
- 스토리를 독립적으로 검증하기 위해 체크포인트에서 중단 가능
- 개발에는 SQLite, 운영에는 PostgreSQL 사용
- Gemini 무료 티어 사용으로 모든 API 비용은 $0이어야 함
