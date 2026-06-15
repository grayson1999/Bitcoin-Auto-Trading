import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
import { MainLayout } from '@core/layouts/MainLayout'
import { AuthLayout } from '@core/layouts/AuthLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { AdminRoute } from './AdminRoute'

// Lazy load views for code splitting
const DashboardView = lazy(() => import('@views/DashboardView'))
const PortfolioView = lazy(() => import('@views/PortfolioView'))
const SignalsView = lazy(() => import('@views/SignalsView'))
const OrdersView = lazy(() => import('@views/OrdersView'))
const SettingsView = lazy(() => import('@views/SettingsView'))
const AdminView = lazy(() => import('@views/AdminView'))
const RiskView = lazy(() => import('@views/RiskView'))
const LoginView = lazy(() => import('@views/LoginView'))

export const routes: RouteObject[] = [
  // Auth routes (no layout)
  {
    path: '/login',
    element: (
      <AuthLayout>
        <LoginView />
      </AuthLayout>
    ),
  },
  // 소유자(admin) 전용 - 민감 금융 데이터(잔고/포지션/주문/대시보드) 노출 화면
  {
    path: '/',
    element: (
      <AdminRoute>
        <MainLayout>
          <DashboardView />
        </MainLayout>
      </AdminRoute>
    ),
  },
  {
    path: '/portfolio',
    element: (
      <AdminRoute>
        <MainLayout>
          <PortfolioView />
        </MainLayout>
      </AdminRoute>
    ),
  },
  {
    path: '/signals',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <SignalsView />
        </MainLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/orders',
    element: (
      <AdminRoute>
        <MainLayout>
          <OrdersView />
        </MainLayout>
      </AdminRoute>
    ),
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <SettingsView />
        </MainLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/risk',
    element: (
      <AdminRoute>
        <MainLayout>
          <RiskView />
        </MainLayout>
      </AdminRoute>
    ),
  },
  // Admin only routes
  {
    path: '/admin',
    element: (
      <AdminRoute>
        <MainLayout>
          <AdminView />
        </MainLayout>
      </AdminRoute>
    ),
  },
]

export default routes
