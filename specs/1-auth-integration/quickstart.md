# Quickstart: Auth Server 연동

**Feature**: `1-auth-integration`
**Date**: 2026-01-18

---

## 사전 요구사항

1. **Auth Server 실행 중**
   ```bash
   # Auth Server 디렉토리에서
   cd /home/ubuntu/auth-server
   make dev
   # 또는
   uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **초기 관리자 계정 생성됨**
   - Email: `admin@example.com`
   - Password: `admin123456`
   - Auth Server 첫 실행 시 자동 생성

3. **환경 변수 설정**
   ```bash
   # backend/.env
   AUTH_SERVER_URL=http://localhost:8001

   # frontend/.env
   VITE_API_URL=http://localhost:8000
   VITE_AUTH_API_URL=http://localhost:8001
   ```

---

## 빠른 시작

### 1. Auth Server 헬스체크
```bash
curl http://localhost:8001/api/v1/health
# {"status":"healthy","timestamp":"2026-01-18T12:00:00Z"}
```

### 2. 로그인 테스트
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123456"}' | jq -r '.access_token')

echo $TOKEN
# eyJhbGciOiJIUzI1NiIs...
```

### 3. 백엔드 인증 테스트
```bash
# 토큰 없이 (401 예상)
curl http://localhost:8000/api/v1/dashboard/summary
# {"detail":"Authorization 헤더가 필요합니다"}

# 토큰 포함 (200 예상)
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
# 대시보드 데이터 반환
```

### 4. 프론트엔드 접속
```bash
# 개발 서버 시작
cd frontend && npm run dev

# 브라우저에서 http://localhost:5173 접속
# → 자동으로 /login 페이지로 리다이렉트
# → admin@example.com / admin123456 로그인
# → 대시보드 표시
```

---

## 개발 워크플로우

### 백엔드 개발자

1. **의존성 추가**
   ```python
   # 새 라우터에 인증 추가
   from src.api.deps import CurrentUser

   @router.get("/my-endpoint")
   async def my_endpoint(current_user: CurrentUser):
       # current_user.id, current_user.email, current_user.name, current_user.role 사용 가능
       return {"user": current_user.email}
   ```

2. **테스트 시 인증 모킹**
   ```python
   # tests/conftest.py
   @pytest.fixture
   def mock_current_user():
       async def override():
           return AuthUser(id="test", email="test@test.com", name="Test", role="user")
       app.dependency_overrides[get_current_user] = override
       yield
       app.dependency_overrides.clear()

   def test_my_endpoint(mock_current_user):
       response = client.get("/api/v1/my-endpoint")
       assert response.status_code == 200
   ```

### 프론트엔드 개발자

1. **인증 상태 사용**
   ```tsx
   import { useAuth } from '../contexts/AuthContext';

   function MyComponent() {
       const { user, isAuthenticated, logout } = useAuth();

       if (!isAuthenticated) {
           return <Navigate to="/login" />;
       }

       return (
           <div>
               <p>안녕하세요, {user.name}님</p>
               <button onClick={logout}>로그아웃</button>
           </div>
       );
   }
   ```

2. **API 호출 (토큰 자동 포함)**
   ```tsx
   import { api } from '../api/client';

   // Authorization 헤더가 자동으로 추가됨
   const data = await api.get('/dashboard/summary');
   ```

---

## 주요 파일 위치

### 백엔드
| 파일 | 설명 |
|------|------|
| `backend/src/config.py` | AUTH_SERVER_URL 설정 |
| `backend/src/services/auth_client.py` | Auth Server HTTP 클라이언트 |
| `backend/src/api/deps.py` | `get_current_user` 의존성 |
| `backend/src/api/*.py` | 각 라우터에 `CurrentUser` 적용 |

### 프론트엔드
| 파일 | 설명 |
|------|------|
| `frontend/src/contexts/AuthContext.tsx` | 인증 상태 관리 |
| `frontend/src/components/ProtectedRoute.tsx` | 라우트 보호 |
| `frontend/src/pages/Login.tsx` | 로그인 페이지 |
| `frontend/src/api/client.ts` | 토큰 인터셉터 |
| `frontend/src/components/Sidebar.tsx` | 사용자 정보 표시 |

---

## 문제 해결

### 401 Unauthorized
1. 토큰이 만료됨 → 자동 갱신 확인, 실패 시 재로그인
2. Auth Server 다운 → `curl http://localhost:8001/health` 확인

### 503 Service Unavailable
1. Auth Server 연결 불가 → Auth Server 실행 상태 확인
2. 네트워크 문제 → `AUTH_SERVER_URL` 환경변수 확인

### 로그인 실패
1. 잘못된 자격증명 → 이메일/비밀번호 확인
2. 계정 잠김 (5회 실패) → 15분 대기 후 재시도
