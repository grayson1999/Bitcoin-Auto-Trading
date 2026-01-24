import type { ReactNode } from 'react'

interface AuthLayoutProps {
  children: ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-primary">BTC Auto Trading</h1>
          <p className="text-muted-foreground mt-2">비트코인 자동 거래 대시보드</p>
        </div>
        {children}
      </div>
    </div>
  )
}

export default AuthLayout
