# Research Summary: Auth Server 연동

**Feature**: `1-auth-integration`
**Date**: 2026-01-18

---

## 1. Auth Server API 분석

### 결정: Auth Server API 연동 방식

**Decision**: HTTP Client를 통한 토큰 검증 (Introspection 방식)

**Rationale**:
- Auth Server가 이미 `/api/v1/auth/verify` 엔드포인트 제공
- JWT Secret 공유 없이 토큰 검증 가능 (보안상 장점)
- Auth Server에서 토큰 폐기 시 즉시 반영

**Alternatives Considered**:
1. JWT Secret 공유 방식 (로컬 검증)
   - 장점: 네트워크 호출 불필요, 더 빠름
   - 단점: 토큰 폐기 시 즉시 반영 불가, Secret 관리 필요
   - 기각 이유: 보안 및 관리 복잡성

2. API Gateway 도입
   - 장점: 중앙화된 인증 처리
   - 단점: 인프라 복잡도 증가, OCI Free Tier 제약
   - 기각 이유: 현재 규모에서 과도함

---

## 2. 백엔드 인증 패턴

### 결정: FastAPI Dependency Injection 패턴

**Decision**: `Depends(get_current_user)` 의존성 함수로 모든 보호 라우터에 인증 적용

**Rationale**:
- FastAPI 네이티브 패턴
- 기존 코드 구조와 일관성
- 테스트 용이성 (의존성 오버라이드)

**구현 패턴**:
```python
from typing import Annotated
from fastapi import Depends

CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

@router.get("/summary")
async def get_summary(current_user: CurrentUser):
    ...
```

**Alternatives Considered**:
1. Middleware 방식
   - 장점: 한 곳에서 모든 요청 처리
   - 단점: 엔드포인트별 세밀한 제어 어려움, 공개 API 제외 로직 복잡
   - 기각 이유: 세밀한 제어 필요

2. Decorator 방식
   - 장점: 명시적
   - 단점: FastAPI 표준 아님, 의존성 오버라이드 어려움
   - 기각 이유: FastAPI 패턴과 불일치

---

## 3. 프론트엔드 토큰 관리

### 결정: localStorage + React Context

**Decision**: 토큰은 localStorage에 저장, 상태는 React Context로 관리

**Rationale**:
- 브라우저 탭 간 토큰 공유 (Spec 요구사항)
- 페이지 새로고침 시 토큰 유지
- React 컴포넌트에서 일관된 접근

**토큰 저장 구조**:
```typescript
localStorage.setItem('auth', JSON.stringify({
  accessToken: string,
  refreshToken: string,
  user: { id, email, name, role }
}))
```

**Alternatives Considered**:
1. HttpOnly Cookie
   - 장점: XSS 공격에 더 안전
   - 단점: 백엔드 쿠키 설정 필요, CORS 복잡도 증가
   - 기각 이유: Auth Server가 이미 완료된 상태, 변경 최소화

2. Memory Only (sessionStorage)
   - 장점: 가장 안전
   - 단점: 탭 간 공유 불가, 새로고침 시 재로그인
   - 기각 이유: 사용자 경험 저하

3. Redux/Zustand
   - 장점: 더 강력한 상태 관리
   - 단점: 추가 의존성
   - 기각 이유: Context만으로 충분

---

## 4. 토큰 자동 갱신 전략

### 결정: 만료 1분 전 타이머 갱신 + 401 응답 시 재시도

**Decision**:
1. 로그인 시 14분 타이머 설정 (15분 토큰 - 1분 여유)
2. 401 응답 수신 시 토큰 갱신 후 원 요청 재시도

**Rationale**:
- 사용자 경험 끊김 없음
- 네트워크 지연으로 인한 실패 복구

**구현 흐름**:
```
[로그인 성공]
    ↓
[14분 타이머 시작]
    ↓
[타이머 만료] → [refresh API 호출] → [새 토큰 저장] → [타이머 재설정]
    ↓
[401 응답] → [refresh 시도] → [성공: 재요청] / [실패: 로그아웃]
```

**Alternatives Considered**:
1. 요청 전 항상 토큰 만료 시간 확인
   - 장점: 더 정확한 갱신
   - 단점: 매 요청마다 오버헤드
   - 기각 이유: 불필요한 복잡도

---

## 5. 에러 처리 전략

### 결정: 상태 코드별 분기 처리

**Decision**:
| 상태 코드 | 의미 | 처리 |
|----------|------|------|
| 401 | 토큰 만료/무효 | 갱신 시도 → 실패 시 로그아웃 |
| 403 | 권한 없음 | 에러 메시지 표시 |
| 423 | 계정 잠김 | "계정이 잠겼습니다" 메시지 |
| 429 | Rate Limit | "잠시 후 다시 시도" 메시지 |
| 503 | Auth Server 다운 | "인증 서버 연결 불가" 메시지 |

**Rationale**:
- 사용자에게 명확한 피드백
- Auth Server 장애 시 적절한 대응

---

## 6. 라우터 보호 전략

### 결정: ProtectedRoute 래퍼 컴포넌트

**Decision**: 보호가 필요한 라우트를 `ProtectedRoute` 컴포넌트로 래핑

**Rationale**:
- React Router v6 표준 패턴
- 선언적 라우트 보호
- 기존 라우터 구조 최소 변경

**구현**:
```tsx
<Routes>
  <Route path="/login" element={<Login />} />
  <Route element={<ProtectedRoute><App /></ProtectedRoute>}>
    <Route index element={<Dashboard />} />
    <Route path="orders" element={<Orders />} />
  </Route>
</Routes>
```

---

## 7. Auth Client HTTP 클라이언트 설계

### 결정: 싱글톤 httpx.AsyncClient

**Decision**: 애플리케이션 시작 시 생성하고 종료 시 닫는 싱글톤 클라이언트

**Rationale**:
- 연결 풀 재사용으로 성능 최적화
- FastAPI lifespan과 연동

**구현**:
```python
class AuthClient:
    _instance: ClassVar["AuthClient | None"] = None

    def __init__(self, base_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=5.0
        )

    async def verify_token(self, token: str) -> AuthUser:
        ...

    async def close(self):
        await self._client.aclose()
```

---

## 8. 보호 대상 엔드포인트 목록

| 라우터 | 파일 | 엔드포인트 수 | 보호 적용 |
|--------|------|--------------|-----------|
| dashboard | `api/dashboard.py` | 5 | 전체 |
| signals | `api/signals.py` | 3 | 전체 |
| trading | `api/trading.py` | 5 | 전체 |
| config | `api/config.py` | 2 | 전체 |
| risk | `api/risk.py` | 4 | 전체 |
| backtest | `api/backtest.py` | 3 | 전체 |
| health | `api/health.py` | 1 | **공개 유지** |

**총**: 22개 엔드포인트 보호, 1개 공개

---

## 9. 테스트 전략

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

## 10. 환경 변수 정리

### Backend (.env)
```bash
AUTH_SERVER_URL=http://localhost:8001
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_AUTH_API_URL=http://localhost:8001
```
