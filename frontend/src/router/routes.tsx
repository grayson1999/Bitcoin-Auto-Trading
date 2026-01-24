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
  // Protected routes (with main layout)
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <DashboardView />
        </MainLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/portfolio',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <PortfolioView />
        </MainLayout>
      </ProtectedRoute>
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
      <ProtectedRoute>
        <MainLayout>
          <OrdersView />
        </MainLayout>
      </ProtectedRoute>
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
