# Tasks: Auth Server 연동 및 로그인 기능 통합

**입력**: `/specs/1-auth-integration/` 설계 문서
**필수 조건**: plan.md (필수), spec.md (사용자 스토리용 필수), research.md, data-model.md, contracts/

**테스트**: 기능 명세에서 테스트가 명시적으로 요청되지 않았으므로 테스트 태스크는 제외됨

**구성**: 각 사용자 스토리별로 독립적인 구현 및 테스트가 가능하도록 태스크를 그룹화

## 형식: `[ID] [P?] [Story] 설명`

- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- **[Story]**: 해당 태스크가 속한 사용자 스토리 (예: US1, US2, US3, US4, US5)
- 설명에 정확한 파일 경로 포함

## 경로 규칙

- **웹 앱 (모노레포)**: `backend/src/`, `frontend/src/`

---

## Phase 1: 설정 (공유 인프라)

**목적**: 프로젝트 초기화 및 환경 설정

- [X] T001 backend/src/config.py에 AUTH_SERVER_URL 환경 변수 추가
- [X] T002 [P] frontend/.env.example에 VITE_AUTH_API_URL 환경 변수 예시 추가
- [X] T003 [P] frontend/src/contexts/ 디렉토리 생성

---

## Phase 2: 기반 구축 (필수 선행 조건)

**목적**: 모든 사용자 스토리 구현 전에 반드시 완료해야 하는 핵심 인증 인프라

**⚠️ 중요**: 이 단계가 완료될 때까지 사용자 스토리 작업을 시작할 수 없음

### 백엔드 인증 인프라

- [X] T004 backend/src/services/auth_client.py에 AuthError 예외 클래스 생성
- [X] T005 backend/src/services/auth_client.py에 AuthUser Pydantic 스키마 생성
- [X] T006 backend/src/services/auth_client.py에 verify_token 메서드를 포함한 AuthClient 클래스 구현
- [X] T007 backend/src/services/auth_client.py에 AuthClient 싱글톤 팩토리 함수 (get_auth_client) 추가
- [X] T008 backend/src/api/deps.py에 get_current_user 의존성 함수 생성
- [X] T009 backend/src/api/deps.py에 CurrentUser 타입 별칭 생성
- [X] T010 backend/src/main.py 라이프사이클에서 AuthClient 초기화 및 종료 처리

### 프론트엔드 인증 인프라

- [X] T011 frontend/src/contexts/AuthContext.tsx에 user, tokens, isAuthenticated, isLoading 상태를 포함한 AuthContext 생성
- [X] T012 frontend/src/contexts/AuthContext.tsx에 localStorage 영속성을 갖춘 AuthProvider 컴포넌트 구현
- [X] T013 frontend/src/contexts/AuthContext.tsx에 Auth Server API를 호출하는 login 함수 구현
- [X] T014 frontend/src/contexts/AuthContext.tsx에 토큰을 삭제하는 logout 함수 구현
- [X] T015 frontend/src/contexts/AuthContext.tsx에 인증 컨텍스트에 접근하는 useAuth 훅 생성
- [X] T016 frontend/src/contexts/AuthContext.tsx에 14분 자동 토큰 갱신 타이머 구현

**체크포인트**: 기반 준비 완료 - 이제 사용자 스토리 구현 시작 가능

---

## Phase 3: 사용자 스토리 1 & 4 - 로그인하여 대시보드 접근 + API 보호 (우선순위: P1) 🎯 MVP

**목표**: 사용자가 로그인 페이지에서 자격 증명을 입력하여 대시보드에 접근. 백엔드 API는 인증 없이 접근 불가.

**독립 테스트**:
- 비로그인 상태에서 `/` 접근 시 `/login`으로 리다이렉트
- 올바른 자격 증명 입력 시 대시보드 표시
- 토큰 없이 API 호출 시 401 응답

### 백엔드 API 보호 (US4)

- [ ] T017 [P] [US4] backend/src/api/dashboard.py의 get_dashboard_summary 엔드포인트에 CurrentUser 의존성 추가
- [ ] T018 [P] [US4] backend/src/api/dashboard.py의 get_current_market 엔드포인트에 CurrentUser 의존성 추가
- [ ] T019 [P] [US4] backend/src/api/dashboard.py의 get_market_history 엔드포인트에 CurrentUser 의존성 추가
- [ ] T020 [P] [US4] backend/src/api/dashboard.py의 get_market_summary 엔드포인트에 CurrentUser 의존성 추가
- [ ] T021 [P] [US4] backend/src/api/dashboard.py의 get_latest_market_data 엔드포인트에 CurrentUser 의존성 추가
- [ ] T022 [P] [US4] backend/src/api/dashboard.py의 get_collector_stats 엔드포인트에 CurrentUser 의존성 추가
- [ ] T023 [P] [US4] backend/src/api/signals.py의 모든 엔드포인트(3개)에 CurrentUser 의존성 추가
- [ ] T024 [P] [US4] backend/src/api/trading.py의 모든 엔드포인트(5개)에 CurrentUser 의존성 추가
- [ ] T025 [P] [US4] backend/src/api/config.py의 모든 엔드포인트(2개)에 CurrentUser 의존성 추가
- [ ] T026 [P] [US4] backend/src/api/risk.py의 모든 엔드포인트(4개)에 CurrentUser 의존성 추가
- [ ] T027 [P] [US4] backend/src/api/backtest.py의 모든 엔드포인트(3개)에 CurrentUser 의존성 추가

### 프론트엔드 로그인 UI (US1)

- [ ] T028 [US1] frontend/src/pages/Login.tsx에 이메일/비밀번호 폼이 있는 Login.tsx 페이지 생성
- [ ] T029 [US1] frontend/src/pages/Login.tsx에 폼 유효성 검사 구현 (이메일 형식, 비밀번호 8자 이상)
- [ ] T030 [US1] frontend/src/pages/Login.tsx에 useAuth().login()을 호출하는 로그인 폼 제출 구현
- [ ] T031 [US1] frontend/src/pages/Login.tsx에 401, 423, 429 응답에 대한 오류 메시지 표시 추가
- [ ] T032 [US1] frontend/src/pages/Login.tsx에 Tailwind로 로그인 페이지 스타일링 (중앙 정렬 폼, 사이드바 없음)

### 프론트엔드 라우트 보호 (US1)

- [ ] T033 [US1] frontend/src/components/ProtectedRoute.tsx에 isAuthenticated를 확인하는 ProtectedRoute 컴포넌트 생성
- [ ] T034 [US1] frontend/src/components/ProtectedRoute.tsx에 미인증 시 /login으로 리다이렉트 구현
- [ ] T035 [US1] frontend/src/components/ProtectedRoute.tsx에 인증 상태 확인 중 로딩 스피너 추가
- [ ] T036 [US1] frontend/src/main.tsx에서 보호된 라우트를 ProtectedRoute로 래핑하도록 라우터 업데이트
- [ ] T037 [US1] frontend/src/main.tsx의 라우터 설정에 /login 라우트 추가
- [ ] T038 [US1] frontend/src/main.tsx에서 RouterProvider를 AuthProvider로 래핑

### 프론트엔드 API 클라이언트 통합 (US1)

- [ ] T039 [US1] frontend/src/api/client.ts에 Authorization 헤더를 포함하는 요청 인터셉터 추가
- [ ] T040 [US1] frontend/src/api/client.ts에 401을 처리하고 로그아웃을 트리거하는 응답 인터셉터 추가

**체크포인트**: 이 시점에서 US1과 US4가 완전히 동작해야 함 - 로그인 작동 및 API 보호됨

---

## Phase 4: 사용자 스토리 2 - 로그인 상태 유지 및 자동 토큰 갱신 (우선순위: P2)

**목표**: 로그인한 사용자가 15분 후에도 재로그인 없이 계속 사용 가능. 토큰 자동 갱신.

**독립 테스트**: 로그인 후 15분 경과해도 API 호출 성공

### 토큰 갱신 구현

- [ ] T041 [US2] frontend/src/contexts/AuthContext.tsx에 리프레시 토큰 API 호출 함수 구현
- [ ] T042 [US2] frontend/src/contexts/AuthContext.tsx에 갱신 실패 시 사용자 로그아웃 처리
- [ ] T043 [US2] frontend/src/contexts/AuthContext.tsx에 앱 로드 시 localStorage에서 인증 상태 복원

### API 클라이언트 갱신 로직

- [ ] T044 [US2] frontend/src/api/client.ts에 토큰 갱신 재시도를 포함한 401 응답 인터셉터 구현
- [ ] T045 [US2] frontend/src/api/client.ts에 토큰 갱신 중 대기 요청 큐잉 처리

**체크포인트**: 이 시점에서 US1, US2, US4가 작동해야 함 - 끊김 없는 토큰 갱신

---

## Phase 5: 사용자 스토리 3 - 로그아웃 (우선순위: P2)

**목표**: 사용자가 로그아웃 버튼 클릭 시 세션 종료 및 로그인 페이지 이동

**독립 테스트**: 로그아웃 클릭 후 `/login`으로 이동, 뒤로가기 시 다시 `/login`

### 로그아웃 구현

- [ ] T046 [US3] frontend/src/contexts/AuthContext.tsx에 Auth Server로 로그아웃 API 호출 구현
- [ ] T047 [US3] frontend/src/contexts/AuthContext.tsx에 로그아웃 시 localStorage 삭제

### 사이드바 로그아웃 버튼

- [ ] T048 [US3] frontend/src/components/Sidebar.tsx의 사용자 프로필 섹션에 로그아웃 버튼 추가
- [ ] T049 [US3] frontend/src/components/Sidebar.tsx에서 로그아웃 버튼을 useAuth().logout()에 연결
- [ ] T050 [US3] frontend/src/components/Sidebar.tsx에서 Tailwind로 로그아웃 버튼 스타일링

**체크포인트**: 이 시점에서 US1-4가 작동해야 함 - 전체 로그인/로그아웃 흐름 완성

---

## Phase 6: 사용자 스토리 5 - 로그인 사용자 정보 표시 (우선순위: P3)

**목표**: 로그인한 사용자의 이름/이메일이 사이드바에 표시

**독립 테스트**: 로그인 후 사이드바에서 사용자 이름 확인 가능

### 동적 사용자 표시

- [ ] T051 [US5] frontend/src/components/Sidebar.tsx에서 하드코딩된 사용자를 useAuth().user로 교체
- [ ] T052 [US5] frontend/src/components/Sidebar.tsx의 프로필 섹션에 user.name과 user.email 표시
- [ ] T053 [US5] frontend/src/components/Sidebar.tsx에서 user.name으로부터 아바타 이니셜 생성

**체크포인트**: 모든 사용자 스토리가 독립적으로 동작해야 함

---

## Phase 7: 마무리 및 공통 관심사

**목적**: 여러 사용자 스토리에 영향을 미치는 개선 사항

- [ ] T054 [P] frontend/src/contexts/AuthContext.tsx에 사용자 친화적 메시지와 함께 Auth Server 연결 오류 처리 추가
- [ ] T055 [P] frontend/src/api/client.ts에 503 서비스 불가 응답 처리 추가
- [ ] T056 quickstart.md 테스트 시나리오에 따른 수동 검증 실행
- [ ] T057 backend/tests/conftest.py에 테스트용 mock_auth 픽스처 업데이트

---

## 의존성 및 실행 순서

### 단계별 의존성

- **설정 (Phase 1)**: 의존성 없음 - 즉시 시작 가능
- **기반 구축 (Phase 2)**: 설정 완료에 의존 - 모든 사용자 스토리를 차단
- **사용자 스토리 (Phase 3-6)**: 모두 기반 구축 단계 완료에 의존
  - US1+US4를 먼저 완료 (MVP)
  - US2, US3, US5는 US1+US4 이후 병렬 진행 가능
- **마무리 (Phase 7)**: 원하는 모든 사용자 스토리 완료에 의존

### 사용자 스토리 의존성

- **사용자 스토리 1+4 (P1)**: 기반 구축 (Phase 2) 이후 시작 가능 - MVP 핵심
- **사용자 스토리 2 (P2)**: US1 로그인 흐름 완료에 의존
- **사용자 스토리 3 (P2)**: US1 로그인 흐름 완료에 의존
- **사용자 스토리 5 (P3)**: US1 AuthContext 완료에 의존

### 각 사용자 스토리 내부

- 백엔드 보호 (US4)와 프론트엔드 로그인 (US1)은 병렬 실행 가능
- 모든 백엔드 라우터 보호 태스크 (T017-T027)는 병렬 실행 가능
- API 클라이언트 통합은 AuthContext 이후에 진행

### 병렬 실행 기회

**Phase 1 (설정)**:
```bash
# 모든 설정 태스크 병렬 실행
태스크 T001, T002, T003 - 모두 병렬
```

**Phase 2 (기반 구축)**:
```bash
# 백엔드와 프론트엔드 기반을 병렬로 실행 가능
백엔드: T004-T010
프론트엔드: T011-T016
```

**Phase 3 (US1+US4)**:
```bash
# 모든 백엔드 보호 태스크 병렬 실행
태스크 T017-T027 - 모두 병렬 (다른 파일)

# 프론트엔드 로그인 태스크는 대부분 순차적
태스크 T028-T040 - 순서대로 진행
```

---

## 병렬 예시: Phase 3 백엔드 보호

```bash
# 모든 백엔드 라우터 보호 태스크를 함께 실행:
태스크: "dashboard.py 엔드포인트에 CurrentUser 의존성 추가" (T017-T022)
태스크: "signals.py 엔드포인트에 CurrentUser 의존성 추가" (T023)
태스크: "trading.py 엔드포인트에 CurrentUser 의존성 추가" (T024)
태스크: "config.py 엔드포인트에 CurrentUser 의존성 추가" (T025)
태스크: "risk.py 엔드포인트에 CurrentUser 의존성 추가" (T026)
태스크: "backtest.py 엔드포인트에 CurrentUser 의존성 추가" (T027)
```

---

## 구현 전략

### MVP 우선 (사용자 스토리 1 + 4만)

1. Phase 1: 설정 완료
2. Phase 2: 기반 구축 완료 (중요 - 모든 스토리 차단)
3. Phase 3: 사용자 스토리 1 + 4 완료
4. **중단 및 검증**: 로그인 흐름과 API 보호를 독립적으로 테스트
5. 준비되면 배포/데모

### 점진적 배포

1. 설정 + 기반 구축 완료 → 기반 준비됨
2. 사용자 스토리 1+4 추가 → 독립 테스트 → 배포/데모 (MVP!)
3. 사용자 스토리 2 추가 → 토큰 갱신 테스트 → 배포/데모
4. 사용자 스토리 3 추가 → 로그아웃 테스트 → 배포/데모
5. 사용자 스토리 5 추가 → 사용자 표시 테스트 → 배포/데모
6. 각 스토리는 이전 스토리를 깨뜨리지 않으면서 가치를 추가

### 권장 MVP 범위

**MVP = Phase 1 + Phase 2 + Phase 3 (사용자 스토리 1 + 4)**

이것으로 제공되는 기능:
- 로그인 페이지 동작
- 모든 API 보호됨 (토큰 없이 401)
- 기본 인증 흐름 작동

---

## 요약

| 항목 | 개수 |
|------|------|
| 전체 태스크 | 57 |
| 설정 단계 | 3 |
| 기반 구축 단계 | 13 |
| US1+US4 (MVP) | 24 |
| US2 (토큰 갱신) | 5 |
| US3 (로그아웃) | 5 |
| US5 (사용자 표시) | 3 |
| 마무리 | 4 |
| 병렬 실행 기회 | 15+ 태스크 |

---

## 참고 사항

- [P] 태스크 = 다른 파일, 의존성 없음
- [Story] 라벨은 태스크를 특정 사용자 스토리에 매핑하여 추적 가능
- 각 사용자 스토리는 독립적으로 완료 및 테스트 가능해야 함
- 각 태스크 또는 논리적 그룹 후에 커밋
- 체크포인트에서 멈춰서 스토리를 독립적으로 검증
- US1과 US4는 둘 다 P1이고 상호 의존적이므로 (로그인 UI + API 보호) 결합됨
