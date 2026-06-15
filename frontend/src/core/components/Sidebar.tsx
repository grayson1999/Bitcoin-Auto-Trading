import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardList,
  Settings,
  Wallet,
  Shield,
  AlertTriangle,
  LogOut,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { cn } from '@core/utils'
import { useAuth } from '@stores/auth.store'
import { Button } from '@core/components/ui/button'
import { useTradingConfig } from '@/core/contexts/TradingConfigContext'
import { fetchDashboardSummary } from '@/api/dashboard.api'
import { getHealthDetail } from '@/api/health.api'
import { formatRelativeTime } from '@/core/utils/formatters'

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
  { to: '/risk', icon: <AlertTriangle size={20} />, label: '리스크', adminOnly: true },
  { to: '/settings', icon: <Settings size={20} />, label: '설정' },
  { to: '/admin', icon: <Shield size={20} />, label: '관리자', adminOnly: true },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user, isAdmin, logout } = useAuth()
  const { currency } = useTradingConfig()
  const navigate = useNavigate()

  // 마지막 AI 신호 시각용 (대시보드는 admin 전용이므로 admin만 폴링)
  const { data: dashboard, isError: isStatusError } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: fetchDashboardSummary,
    refetchInterval: 5000,
    enabled: isAdmin,
  })

  // 봇 생존 진실 판단: 헬스체크의 scheduler·recent_signal 상태 기반
  // (dashboard.updated_at은 매 응답마다 now라 가짜 생존신호 → 사용 안 함)
  const { data: health, isError: isHealthError } = useQuery({
    queryKey: ['healthDetail'],
    queryFn: getHealthDetail,
    refetchInterval: 10000,
    enabled: isAdmin,
  })

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const filteredNavItems = navItems.filter((item) => !item.adminOnly || isAdmin)

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen w-64 transition-transform duration-300',
          'bg-black/20 backdrop-blur-xl border-r border-white/5', // Matte Glass Style
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-white/5">
            <img src="/logo.png" alt="Nano Banana" className="w-8 h-8 mr-3 rounded-full object-cover shadow-lg shadow-primary/20" />
            <h1 className="text-lg font-bold tracking-tight text-foreground font-heading">
              {currency} <span className="text-muted-foreground font-normal">Trading</span>
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
            {filteredNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-primary/10 text-primary shadow-[inset_3px_0_0_0_hsl(var(--primary))]' // Subtle active indicator
                      : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                  )
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Bot status indicator (admin only) - 헬스체크 기반 진짜 생존 신호 */}
          {isAdmin &&
            (() => {
              const schedulerStatus = health?.components?.scheduler?.status
              const signalStatus = health?.components?.recent_signal?.status
              const lastSignalAt = dashboard?.latest_signal?.created_at

              // 연결 끊김 > 스케줄러 정지(빨강) > 신호 지연(노랑) > 정상(초록)
              let dot = 'bg-emerald-400'
              let label = '봇 정상'
              if (isHealthError || isStatusError) {
                dot = 'bg-rose-500 animate-pulse'
                label = '연결 끊김'
              } else if (schedulerStatus === 'unhealthy') {
                dot = 'bg-rose-500 animate-pulse'
                label = '봇 정지'
              } else if (signalStatus === 'warning' || signalStatus === 'unhealthy') {
                dot = 'bg-amber-400'
                label = '신호 지연'
              }

              return (
                <div className="px-4 pt-3">
                  <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/5 border border-white/5 text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className={cn('w-2 h-2 rounded-full', dot)} />
                      <span className="text-muted-foreground">{label}</span>
                    </div>
                    {lastSignalAt && !isHealthError && (
                      <span
                        className="text-muted-foreground/70 font-mono"
                        title="마지막 AI 신호 시각"
                      >
                        {formatRelativeTime(lastSignalAt)}
                      </span>
                    )}
                  </div>
                </div>
              )
            })()}

          {/* User section */}
          <div className="p-4 border-t border-white/5">
            <div className="flex items-center gap-3 px-3 py-3 mb-2 rounded-lg bg-white/5 border border-white/5">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center ring-1 ring-white/10">
                <span className="text-sm font-bold text-primary">
                  {user?.name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-foreground">{user?.name || 'User'}</p>
                <p className="text-xs text-muted-foreground truncate font-mono">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              onClick={handleLogout}
            >
              <LogOut size={18} />
              로그아웃
            </Button>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
