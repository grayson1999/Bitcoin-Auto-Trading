/**
 * 보호된 라우트 컴포넌트
 *
 * 인증되지 않은 사용자의 접근을 차단하고 로그인 페이지로 리다이렉트합니다.
 * - 인증 상태 확인 중 로딩 스피너 표시
 * - 미인증 시 /login으로 리다이렉트
 * - 인증됨 시 자식 컴포넌트 렌더링
 */

import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // 인증 상태 확인 중 로딩 스피너 표시
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-banana-400"></div>
          <p className="text-dark-text-secondary text-sm">로딩 중...</p>
        </div>
      </div>
    );
  }

  // 미인증 시 로그인 페이지로 리다이렉트
  // 현재 경로를 state로 전달하여 로그인 후 원래 페이지로 복귀
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // 인증됨 - 자식 컴포넌트 렌더링
  return <>{children}</>;
}

export default ProtectedRoute;
