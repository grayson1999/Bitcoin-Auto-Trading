import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { Sidebar } from '@core/components/Sidebar'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 min-h-screen">
        <div className="p-4 lg:p-8">
          <div key={location.pathname} className="mx-auto max-w-7xl page-transition">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}

export default MainLayout
