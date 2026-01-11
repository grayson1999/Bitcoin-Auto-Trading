/**
 * 설정 페이지 컴포넌트
 *
 * 거래 파라미터와 위험 관리 설정을 구성합니다.
 * 현재는 플레이스홀더 상태이며, 추후 다음 기능이 구현될 예정:
 * - 거래 파라미터 설정 (포지션 크기, 손절매 등)
 * - API 키 관리
 * - 알림 설정
 * - 위험 관리 옵션
 */

import type { FC } from "react";
import PageLayout from "../components/PageLayout";

/**
 * Settings 컴포넌트
 *
 * 설정 페이지입니다.
 * 거래 시스템의 다양한 설정을 구성할 수 있습니다.
 *
 * @returns JSX.Element 설정 UI
 */
const Settings: FC = () => {
  return (
    <PageLayout
      title="설정"
      description="거래 파라미터와 위험 관리를 설정합니다."
      placeholder="설정 옵션 개발 예정..."
    />
  );
};

export default Settings;
