/**
 * React 애플리케이션 진입점
 *
 * 이 파일은 React 앱의 초기화를 담당합니다.
 * - React Query 클라이언트 설정 (데이터 캐싱/페칭)
 * - React Router 라우팅 설정
 * - 루트 컴포넌트 마운트
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./contexts/AuthContext";
import "./index.css";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Orders from "./pages/Orders";
import Settings from "./pages/Settings";
import Signals from "./pages/Signals";

// === React Query 설정 상수 ===
const QUERY_STALE_TIME_MS = 5000; // 데이터 신선도 유지 시간 (5초)
const QUERY_RETRY_COUNT = 2; // 요청 실패 시 재시도 횟수

/**
 * React Query 클라이언트 인스턴스
 *
 * 서버 상태 관리를 위한 설정:
 * - staleTime: 데이터가 오래된 것으로 간주되기 전 시간
 * - retry: 실패한 쿼리 재시도 횟수
 * - refetchOnWindowFocus: 창 포커스 시 자동 재요청 비활성화
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_TIME_MS,
      retry: QUERY_RETRY_COUNT,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * 애플리케이션 라우터 설정
 *
 * 라우팅 구조:
 * - /login: 로그인 페이지 (공개)
 * - / (루트): Dashboard 페이지 (보호됨)
 * - /orders: 주문 내역 페이지 (보호됨)
 * - /signals: AI 신호 페이지 (보호됨)
 * - /settings: 설정 페이지 (보호됨)
 * - /backtest: 백테스트 페이지 (보호됨)
 */
const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true, // 기본 라우트
        element: <Dashboard />,
      },
      {
        path: "orders",
        element: <Orders />,
      },
      {
        path: "signals",
        element: <Signals />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
      {
        path: "backtest",
        element: <Backtest />,
      },
    ],
  },
]);

// React 앱 마운트
// StrictMode: 개발 중 잠재적 문제 감지
// ErrorBoundary: 런타임 오류 포착 및 사용자 친화적 UI 표시
// AuthProvider: 인증 상태 관리
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
);
