# Data Model: Auth Server 연동

**Feature**: `1-auth-integration`
**Date**: 2026-01-18

---

## 개요

Auth Server 연동 기능은 새로운 데이터베이스 엔티티를 생성하지 않습니다. 대신 Auth Server에서 관리되는 사용자 정보를 런타임에 전달받아 사용합니다.

---

## 1. 외부 엔티티 (Auth Server 제공)

### User (사용자)
Auth Server의 `/api/v1/auth/verify` 응답으로 받는 사용자 정보

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | 사용자 고유 ID |
| email | string | 이메일 주소 |
| name | string | 사용자 이름 |
| role | string | 역할 (admin/user) |

**Source**: Auth Server JWT payload

---

## 2. 백엔드 스키마 (Pydantic)

### AuthUser
`backend/src/api/deps.py` - 인증된 사용자 정보 스키마

```python
from pydantic import BaseModel

class AuthUser(BaseModel):
    """Auth Server에서 검증된 사용자 정보"""
    id: str
    email: str
    name: str
    role: str

    class Config:
        frozen = True  # Immutable
```

### AuthError
`backend/src/services/auth_client.py` - 인증 오류

```python
class AuthError(Exception):
    """Auth Server 관련 오류"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
```

---

## 3. 프론트엔드 타입 (TypeScript)

### AuthState
`frontend/src/contexts/AuthContext.tsx` - 인증 상태

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

### LoginRequest / LoginResponse
`frontend/src/api/auth.ts` - 로그인 API 타입

```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
```

---

## 4. LocalStorage 구조

### 저장 위치
`localStorage.auth`

### 데이터 형식
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "name": "사용자",
    "role": "user"
  },
  "expiresAt": 1705450500000
}
```

---

## 5. 상태 전이도

### 인증 상태 전이

```
[비인증] ──(로그인 성공)──→ [인증됨]
   ↑                           │
   │                           │
(로그아웃/              (토큰 갱신)
 토큰 만료)                    ↓
   │                     [인증됨]
   └───────────────────────────┘
```

### 토큰 갱신 흐름

```
[액세스 토큰 유효] ──(14분 경과)──→ [갱신 필요]
                                       │
                              (refresh API 호출)
                                       ↓
                             [갱신 성공/실패]
                                    │     │
                           (성공)   │     │  (실패)
                                    ↓     ↓
                            [토큰 갱신] [로그아웃]
```

---

## 6. 검증 규칙

### 백엔드

| 규칙 | 구현 위치 | 동작 |
|------|----------|------|
| Authorization 헤더 필수 | `deps.py` | 없으면 401 |
| Bearer 형식 | `deps.py` | 아니면 401 |
| 토큰 유효성 | Auth Server | 무효하면 401 |
| Auth Server 연결 | `auth_client.py` | 실패하면 503 |

### 프론트엔드

| 규칙 | 구현 위치 | 동작 |
|------|----------|------|
| 이메일 형식 | `Login.tsx` | 클라이언트 검증 |
| 비밀번호 8자 이상 | `Login.tsx` | 클라이언트 검증 |
| 토큰 존재 | `ProtectedRoute.tsx` | 없으면 `/login` 이동 |

---

## 7. 관계 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    Bitcoin-Auto-Trading                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐                     ┌─────────────────┐    │
│  │  Frontend   │                     │    Backend      │    │
│  │             │     REST API        │                 │    │
│  │ AuthContext ├────────────────────→│  deps.py        │    │
│  │ ProtectedRoute                    │  (CurrentUser)  │    │
│  │ Login.tsx   │                     │                 │    │
│  └──────┬──────┘                     └────────┬────────┘    │
│         │                                      │            │
│         │  Auth API                            │ Verify     │
│         │  (login/refresh)                     │ Token      │
│         ↓                                      ↓            │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Auth Server (:8001)                 │       │
│  │                                                  │       │
│  │  POST /api/v1/auth/login                         │       │
│  │  POST /api/v1/auth/refresh                       │       │
│  │  POST /api/v1/auth/logout                        │       │
│  │  GET  /api/v1/auth/verify ← Backend 사용         │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 마이그레이션

이 기능은 데이터베이스 변경이 없으므로 마이그레이션이 필요하지 않습니다.
