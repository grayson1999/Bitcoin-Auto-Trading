# Implementation Plan: Auth Server 연동 및 로그인 기능 통합

**Branch**: `1-auth-integration` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Auth Server 연동 요청

---

## Summary

Bitcoin-Auto-Trading 시스템에 Auth Server(http://localhost:8001)를 연동하여 전반적인 로그인 기능을 구현합니다. 비로그인 사용자의 대시보드/API 접근을 차단하고, 로그인/로그아웃 UI를 제공하며, 자동 토큰 갱신으로 끊김 없는 사용 경험을 보장합니다.

---

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.0+ (Frontend)
**Primary Dependencies**: FastAPI, httpx, React, Axios
**Storage**: PostgreSQL (변경 없음)
**Testing**: pytest (Backend), Vitest (Frontend)
**Target Platform**: Linux Server (Docker)
**Project Type**: Monorepo (Backend + Frontend)
**Performance Goals**: 토큰 검증 100ms 이내, 로그인 3초 이내
**Constraints**: Auth Server 의존성, OCI Free Tier 운영
**Scale/Scope**: 단일 사용자 → 10명 이내

---

## Research Summary

[Full research at research.md](./research.md)

### 핵심 결정사항

| 영역 | 결정 | 근거 |
|------|------|------|
| 토큰 검증 | HTTP Introspection | 보안성, 즉시 폐기 반영 |
| 인증 패턴 | FastAPI Depends | 네이티브 패턴, 테스트 용이 |
| 토큰 저장 | localStorage | 탭 간 공유, 새로고침 유지 |
| 상태 관리 | React Context | 충분한 기능, 추가 의존성 불필요 |
| 토큰 갱신 | 14분 타이머 + 401 재시도 | 끊김 없는 경험 |

---

## Constitution Check

Constitution이 템플릿 상태이므로 기본 원칙 적용:
- [x] 독립적 테스트 가능한 모듈 구조
- [x] 명확한 API 계약 정의
- [x] 로깅 및 관찰 가능성 확보
- [x] 단순성 우선 (YAGNI)

---

## Project Structure

### 신규 생성 파일 (5개)

```text
backend/src/
├── services/
│   └── auth_client.py          # Auth Server HTTP 클라이언트 (신규)
└── api/
    └── deps.py                  # 인증 의존성 (신규)

frontend/src/
├── contexts/
│   └── AuthContext.tsx         # 인증 상태 Context (신규)
├── components/
│   └── ProtectedRoute.tsx      # 라우트 보호 (신규)
└── pages/
    └── Login.tsx               # 로그인 페이지 (신규)
```

### 수정 파일 (10개)

```text
backend/src/
├── config.py                   # auth_server_url 추가
├── main.py                     # Auth Client 정리
└── api/
    ├── dashboard.py            # CurrentUser 의존성
    ├── signals.py              # CurrentUser 의존성
    ├── trading.py              # CurrentUser 의존성
    ├── config.py               # CurrentUser 의존성
    ├── risk.py                 # CurrentUser 의존성
    └── backtest.py             # CurrentUser 의존성

frontend/src/
├── main.tsx                    # AuthProvider, 라우터 변경
├── api/client.ts               # 토큰 인터셉터
└── components/Sidebar.tsx      # 동적 사용자, 로그아웃
```

---

## Key Design Decisions

### 1. HTTP Introspection 방식 토큰 검증

**선택**: Auth Server `/api/v1/auth/verify` 호출

**근거**:
- JWT Secret 공유 불필요 (보안 향상)
- 토큰 폐기 시 즉시 반영
- Auth Server 중앙 집중 관리 유지

**트레이드오프**:
- 매 요청마다 네트워크 호출 (latency 증가)
- Auth Server 의존성 (가용성 연동)

### 2. React Context 상태 관리

**선택**: AuthContext + localStorage

**근거**:
- 추가 라이브러리 없이 충분한 기능
- 브라우저 탭 간 토큰 공유
- 새로고침 시 상태 복원

**트레이드오프**:
- XSS 취약점 가능성 (CSP로 완화)
- Redux 대비 DevTools 지원 약함

### 3. 14분 타이머 기반 토큰 갱신

**선택**: 로그인 시 14분 타이머 설정, 만료 1분 전 갱신

**근거**:
- 사용자 경험 끊김 방지
- 네트워크 지연 대비 1분 여유
- 401 발생 시 추가 재시도 로직

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | 현재 복잡성 위반 없음 | - |

---

## External Dependencies

### APIs

| API | 용도 | 인증 |
|-----|------|------|
| Auth Server /api/v1/auth/login | 로그인 | 없음 |
| Auth Server /api/v1/auth/refresh | 토큰 갱신 | Refresh Token |
| Auth Server /api/v1/auth/logout | 로그아웃 | Access Token |
| Auth Server /api/v1/auth/verify | 토큰 검증 | Access Token |

### 추가 라이브러리

**없음** - 기존 의존성(httpx, axios)으로 구현 가능

---

## Implementation Phases

### Phase 1: 백엔드 기반 (신규 모듈)

#### 1.1 환경 변수 추가
**파일**: `backend/src/config.py`
```python
auth_server_url: str = Field(
    default="http://localhost:8001",
    description="Auth Server URL"
)
```

#### 1.2 Auth Client 서비스 생성
**파일**: `backend/src/services/auth_client.py` (신규)
- Auth Server와 통신하는 비동기 HTTP 클라이언트
- `verify_token(token)` → `AuthUser` 반환
- 연결 실패 시 `AuthError(503)` 발생

#### 1.3 인증 의존성 생성
**파일**: `backend/src/api/deps.py` (신규)
- `get_current_user()` 의존성 함수
- Authorization 헤더에서 Bearer 토큰 추출
- Auth Server `/api/v1/auth/verify` 호출
- 실패 시 401/503 HTTP 예외

---

### Phase 2: 백엔드 라우터 보호

각 라우터에 `CurrentUser` 의존성 추가:

| 파일 | 엔드포인트 수 |
|------|-------------|
| `backend/src/api/dashboard.py` | 5개 |
| `backend/src/api/signals.py` | 3개 |
| `backend/src/api/trading.py` | 5개 |
| `backend/src/api/config.py` | 2개 |
| `backend/src/api/risk.py` | 4개 |
| `backend/src/api/backtest.py` | 3개 |
| `backend/src/api/health.py` | 공개 유지 |

**적용 예시**:
```python
from src.api.deps import CurrentUser

@router.get("/summary")
async def get_dashboard_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,  # 추가
) -> DashboardSummaryResponse:
```

#### 2.1 main.py 라이프사이클 정리
**파일**: `backend/src/main.py`
- 종료 시 Auth Client 연결 해제

---

### Phase 3: 프론트엔드 기반 (신규 모듈)

#### 3.1 Auth Context
**파일**: `frontend/src/contexts/AuthContext.tsx` (신규)
- `user`, `isAuthenticated`, `isLoading` 상태 관리
- `login(email, password)`, `logout()` 함수
- 토큰 localStorage 저장/복원
- 14분마다 자동 토큰 갱신

#### 3.2 ProtectedRoute
**파일**: `frontend/src/components/ProtectedRoute.tsx` (신규)
- 미인증 사용자 → `/login` 리다이렉트
- 로딩 중 스피너 표시

#### 3.3 로그인 페이지
**파일**: `frontend/src/pages/Login.tsx` (신규)
- 심플 디자인 (중앙 정렬 폼, 사이드바 없음)
- 에러 메시지 처리 (401, 423, 429)
- 로그인 후 원래 페이지로 이동

---

### Phase 4: 프론트엔드 통합

#### 4.1 API 클라이언트 토큰 관리
**파일**: `frontend/src/api/client.ts`
- 요청 인터셉터: Authorization 헤더 자동 추가
- 응답 인터셉터: 401 시 토큰 갱신 → 재요청

#### 4.2 라우터 재구성
**파일**: `frontend/src/main.tsx`
```tsx
<AuthProvider>
  <RouterProvider router={router} />
</AuthProvider>

// 라우트 구조
/login           → Login (공개)
/                → ProtectedRoute > App > Dashboard
/orders          → ProtectedRoute > App > Orders
...
```

#### 4.3 Sidebar 업데이트
**파일**: `frontend/src/components/Sidebar.tsx`
- 하드코딩된 사용자 → `useAuth()` 훅으로 동적 표시
- 하단에 로그아웃 버튼 추가

---

## Testing Strategy

### 백엔드 테스트

```python
# conftest.py에서 Auth 의존성 오버라이드
@pytest.fixture
def mock_auth():
    async def override_get_current_user():
        return AuthUser(id="test", email="test@test.com", name="Test", role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()
```

### 프론트엔드 테스트

```typescript
// Mock AuthContext Provider
const MockAuthProvider = ({ children }) => (
  <AuthContext.Provider value={{
    user: { id: 'test', email: 'test@test.com', name: 'Test' },
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn()
  }}>
    {children}
  </AuthContext.Provider>
)
```

---

## Verification Plan

### 테스트 시나리오

| 시나리오 | 테스트 내용 | 예상 결과 |
|---------|------------|----------|
| **P1-1** | 비로그인으로 `/` 접근 | `/login` 리다이렉트 |
| **P1-2** | 올바른 자격증명 로그인 | 대시보드 표시 |
| **P1-3** | 잘못된 비밀번호 | 오류 메시지 |
| **P1-4** | 토큰 없이 API 호출 | 401 응답 |
| **P2-1** | 15분 후 API 호출 | 자동 갱신 후 성공 |
| **P2-2** | 로그아웃 클릭 | `/login` 이동 |
| **P3-1** | 로그인 후 사이드바 | 사용자 이름 표시 |

### 수동 테스트 절차

1. **Auth Server 실행 확인**
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

2. **백엔드 인증 테스트**
   ```bash
   # 토큰 없이 호출 - 401 예상
   curl http://localhost:8000/api/v1/dashboard/summary

   # 로그인 후 토큰으로 호출 - 200 예상
   TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"admin123456"}' | jq -r '.access_token')

   curl http://localhost:8000/api/v1/dashboard/summary \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **프론트엔드 E2E 테스트**
   - 브라우저에서 `http://localhost:3000` 접근
   - 로그인 페이지 표시 확인
   - 로그인 → 대시보드 이동 확인
   - 사이드바 사용자 정보 확인
   - 로그아웃 → 로그인 페이지 이동 확인

---

## Environment Variables

### Backend (.env)
```bash
AUTH_SERVER_URL=http://localhost:8001
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_AUTH_API_URL=http://localhost:8001
```

---

## Next Steps

`/speckit.tasks` 명령으로 구현 태스크 생성
