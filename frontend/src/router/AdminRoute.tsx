import { Navigate } from 'react-router-dom'
import { ShieldAlert, LogOut } from 'lucide-react'
import { useAuth } from '@stores/auth.store'
import { LoadingSpinner } from '@core/components/LoadingSpinner'
import { Button } from '@core/components/ui/button'

interface AdminRouteProps {
  children: React.ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { isAuthenticated, isAdmin, isLoading, logout } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // 비관리자: 리다이렉트(무한 루프 위험) 대신 명확한 권한 안내 표시.
  // 이 시스템은 단일 운영자(admin)용이며, 민감 데이터 엔드포인트는 admin 전용이다.
  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background px-6 text-center">
        <ShieldAlert className="h-16 w-16 text-amber-400 mb-4" />
        <h1 className="text-xl font-bold text-foreground mb-2">관리자 전용</h1>
        <p className="text-sm text-muted-foreground mb-6 max-w-sm">
          이 화면은 봇 소유자(관리자) 계정만 접근할 수 있습니다. 관리자 계정으로
          다시 로그인해 주세요.
        </p>
        <Button variant="outline" onClick={() => void logout()}>
          <LogOut className="h-4 w-4 mr-2" />
          로그아웃
        </Button>
      </div>
    )
  }

  return <>{children}</>
}

export default AdminRoute
