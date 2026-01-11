/**
 * 페이지 레이아웃 컴포넌트
 *
 * 모든 페이지에서 공통으로 사용되는 레이아웃 구조를 제공합니다.
 * - 페이지 제목
 * - 페이지 설명
 * - 콘텐츠 영역 (children 또는 플레이스홀더)
 */

import type { FC, ReactNode } from "react";

/**
 * PageLayout Props 인터페이스
 */
interface PageLayoutProps {
  /** 페이지 제목 */
  title: string;
  /** 페이지 설명 */
  description: string;
  /** 콘텐츠 영역 (없으면 플레이스홀더 표시) */
  children?: ReactNode;
  /** 플레이스홀더 메시지 (children이 없을 때 표시) */
  placeholder?: string;
}

/**
 * PageLayout 컴포넌트
 *
 * 페이지의 공통 레이아웃을 제공합니다.
 * children이 없으면 placeholder 메시지를 표시합니다.
 *
 * @param props - PageLayoutProps
 * @returns JSX.Element 페이지 레이아웃
 */
const PageLayout: FC<PageLayoutProps> = ({
  title,
  description,
  children,
  placeholder,
}) => {
  return (
    <div className="space-y-6">
      {/* 페이지 제목 */}
      <h2 className="text-2xl font-bold text-gray-900">{title}</h2>

      {/* 페이지 설명 */}
      <p className="text-gray-600">{description}</p>

      {/* 콘텐츠 영역 */}
      {children ?? (
        <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
          {placeholder ?? "개발 예정..."}
        </div>
      )}
    </div>
  );
};

export default PageLayout;
