import { useState } from 'react'
import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { Sidebar } from '@core/components/Sidebar'
import { Menu } from 'lucide-react'
import { Button } from '@core/components/ui/button'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation()
  const { currency } = useTradingConfig()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-background/80 backdrop-blur-md border-b border-border z-30 px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSidebarOpen(true)}
            className="-ml-2 text-muted-foreground hover:text-foreground"
          >
            <Menu size={24} />
          </Button>
          <h1 className="text-lg font-bold tracking-tight text-foreground font-heading">
            {currency} <span className="text-muted-foreground font-normal">Trading</span>
          </h1>
        </div>
      </header>

      {/* Sidebar (Passed Props) */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content */}
      <main className="lg:ml-64 min-h-screen pt-16 lg:pt-0 transition-all duration-300">
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
