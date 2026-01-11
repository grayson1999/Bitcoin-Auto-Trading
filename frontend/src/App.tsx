/**
 * 루트 레이아웃 컴포넌트
 *
 * 애플리케이션의 공통 레이아웃을 정의합니다.
 * - 헤더: 앱 제목 및 네비게이션 메뉴
 * - 메인: 페이지별 콘텐츠 영역 (Outlet)
 */

import type { FC } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

// === 상수 ===
const APP_TITLE = "Bitcoin Auto-Trading";

// === 스타일 상수 ===
const NAV_STYLES = {
  active: "bg-gray-900 text-white",
  inactive: "text-gray-700 hover:bg-gray-200",
} as const;

/**
 * 네비게이션 메뉴 항목 인터페이스
 */
interface NavItem {
  /** URL 경로 */
  path: string;
  /** 표시될 메뉴 이름 */
  label: string;
}

/**
 * 네비게이션 메뉴 항목 목록
 */
const navItems: NavItem[] = [
  { path: "/", label: "Dashboard" }, // 대시보드
  { path: "/orders", label: "Orders" }, // 주문 내역
  { path: "/signals", label: "Signals" }, // AI 신호
  { path: "/settings", label: "Settings" }, // 설정
];

/**
 * App 컴포넌트
 *
 * 모든 페이지에서 공유되는 레이아웃 컴포넌트입니다.
 * - 상단 네비게이션 바
 * - 페이지 콘텐츠 영역
 *
 * @returns JSX.Element 앱 레이아웃
 */
const App: FC = () => {
  // 현재 경로 확인 (활성 메뉴 표시용)
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 헤더 - 앱 제목 및 네비게이션 */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            {/* 앱 제목 */}
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">
              {APP_TITLE}
            </h1>

            {/* 네비게이션 메뉴 */}
            <nav className="flex space-x-4">
              {navItems.map((navItem) => (
                <Link
                  key={navItem.path}
                  to={navItem.path}
                  className={`rounded-md px-3 py-2 text-sm font-medium ${
                    // 현재 경로와 일치하면 활성 스타일 적용
                    location.pathname === navItem.path
                      ? NAV_STYLES.active
                      : NAV_STYLES.inactive
                  }`}
                >
                  {navItem.label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 영역 */}
      <main>
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {/* Outlet: 중첩 라우트의 자식 컴포넌트가 렌더링되는 위치 */}
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default App;
