import { Suspense, useState, useEffect } from 'react'
import { useRoutes } from 'react-router-dom'
import { routes } from './routes'
import { LoadingSpinner } from '@core/components/LoadingSpinner'
import { AlertCircle } from 'lucide-react'

const LOADING_TIMEOUT_MS = 5000

function PageLoader() {
  const [isTimeout, setIsTimeout] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsTimeout(true)
    }, LOADING_TIMEOUT_MS)

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      <LoadingSpinner size="lg" text="로딩 중..." />
      {isTimeout && (
        <div className="mt-6 flex items-center gap-2 text-yellow-400 animate-fade-in">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">로딩이 예상보다 오래 걸리고 있습니다...</span>
        </div>
      )}
    </div>
  )
}

export function AppRouter() {
  const element = useRoutes(routes)

  return <Suspense fallback={<PageLoader />}>{element}</Suspense>
}

export default AppRouter
