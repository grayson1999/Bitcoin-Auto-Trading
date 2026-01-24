import { Suspense } from 'react'
import { useRoutes } from 'react-router-dom'
import { routes } from './routes'
import { LoadingSpinner } from '@core/components/LoadingSpinner'

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <LoadingSpinner size="lg" text="로딩 중..." />
    </div>
  )
}

export function AppRouter() {
  const element = useRoutes(routes)

  return <Suspense fallback={<PageLoader />}>{element}</Suspense>
}

export default AppRouter
