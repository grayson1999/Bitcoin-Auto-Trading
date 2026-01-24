import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardList,
  Settings,
  Wallet,
  Shield,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { cn } from '@core/utils'
import { useAuth } from '@stores/auth.store'
import { Button } from '@core/components/ui/button'
import { useState } from 'react'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'

interface NavItem {
  to: string
  icon: React.ReactNode
  label: string
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={20} />, label: '대시보드' },
  { to: '/portfolio', icon: <Wallet size={20} />, label: '포트폴리오' },
  { to: '/signals', icon: <TrendingUp size={20} />, label: 'AI 신호' },
  { to: '/orders', icon: <ClipboardList size={20} />, label: '주문 내역' },
  { to: '/settings', icon: <Settings size={20} />, label: '설정' },
  { to: '/admin', icon: <Shield size={20} />, label: '관리자', adminOnly: true },
]

export function Sidebar() {
  const { user, isAdmin, logout } = useAuth()
  const { currency } = useTradingConfig()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const filteredNavItems = navItems.filter((item) => !item.adminOnly || isAdmin)

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </Button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen bg-surface border-r border-border transition-transform duration-300',
          'w-64 lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-border">
            <h1 className="text-lg font-bold text-primary">{currency} Trading</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {filteredNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 px-3 py-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-sm font-medium text-primary">
                  {user?.name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name || 'User'}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive"
              onClick={handleLogout}
            >
              <LogOut size={20} />
              로그아웃
            </Button>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
