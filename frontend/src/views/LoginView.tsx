import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@stores/auth.store'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@core/components/ui/card'
import { Input } from '@core/components/ui/input'
import { CommonButton } from '@core/components/CommonButton'
import { Alert, AlertDescription } from '@core/components/ui/alert'
import { AlertCircle, Mail, Lock } from 'lucide-react'

export function LoginView() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoading } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('이메일과 비밀번호를 입력해 주세요.')
      return
    }

    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError('로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요.')
    }
  }

  return (
    <Card className="bg-surface border-border">
      <CardHeader className="space-y-1">
        <CardTitle className="text-xl">로그인</CardTitle>
        <CardDescription>계정에 로그인하여 대시보드에 접속하세요</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive" className="bg-destructive/10 border-destructive/50">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              이메일
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10 bg-background"
                autoComplete="email"
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              비밀번호
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 bg-background"
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>
          </div>

          <CommonButton type="submit" className="w-full" isLoading={isLoading}>
            로그인
          </CommonButton>
        </form>
      </CardContent>
    </Card>
  )
}

export default LoginView
