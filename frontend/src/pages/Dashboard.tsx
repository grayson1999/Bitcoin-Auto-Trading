/**
 * 대시보드 페이지 컴포넌트
 *
 * 거래 활동, 포지션, 성과 지표의 개요를 표시합니다.
 * 현재는 플레이스홀더 상태이며, 추후 다음 기능이 구현될 예정:
 * - 실시간 시세 차트
 * - 포지션 현황
 * - 수익률 통계
 * - 최근 거래 내역
 */

import type { FC } from "react";
import PageLayout from "../components/PageLayout";

/**
 * Dashboard 컴포넌트
 *
 * 메인 대시보드 페이지입니다.
 * 거래 시스템의 전반적인 상태와 성과를 한눈에 볼 수 있습니다.
 *
 * @returns JSX.Element 대시보드 UI
 */
const Dashboard: FC = () => {
  return (
    <PageLayout
      title="대시보드"
      description="거래 활동, 포지션, 성과 지표의 개요를 확인합니다."
      placeholder="대시보드 컴포넌트 개발 예정..."
    />
  );
};

export default Dashboard;
