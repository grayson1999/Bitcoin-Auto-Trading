/**
 * 주문 테이블 컴포넌트 (T079)
 *
 * 주문 내역을 테이블 형태로 표시합니다.
 * - 주문 상태별 색상 구분
 * - 매수/매도 방향 구분
 * - 시간/금액 포맷팅
 */

import type { FC } from "react";
import type { Order } from "../hooks/useApi";

// === 타입 정의 ===
interface OrderTableProps {
  /** 주문 목록 */
  orders: Order[];
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 빈 목록 메시지 */
  emptyMessage?: string;
}

// === 상수 ===
const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  PENDING: { bg: "bg-yellow-100", text: "text-yellow-800" },
  EXECUTED: { bg: "bg-green-100", text: "text-green-800" },
  CANCELLED: { bg: "bg-gray-100", text: "text-gray-800" },
  FAILED: { bg: "bg-red-100", text: "text-red-800" },
};

const SIDE_STYLES: Record<string, { bg: string; text: string }> = {
  BUY: { bg: "bg-blue-100", text: "text-blue-800" },
  SELL: { bg: "bg-red-100", text: "text-red-800" },
};

const STATUS_LABELS: Record<string, string> = {
  PENDING: "대기",
  EXECUTED: "체결",
  CANCELLED: "취소",
  FAILED: "실패",
};

const SIDE_LABELS: Record<string, string> = {
  BUY: "매수",
  SELL: "매도",
};

const CARD_CLASSES = "rounded-lg bg-white shadow overflow-hidden";

/**
 * 금액 포맷
 */
function formatAmount(amount: string): string {
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2,
  }).format(Number(amount));
}

/**
 * 날짜 포맷
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/**
 * OrderTable 컴포넌트
 */
const OrderTable: FC<OrderTableProps> = ({
  orders,
  isLoading = false,
  emptyMessage = "주문 내역이 없습니다.",
}) => {
  if (isLoading) {
    return (
      <div className={CARD_CLASSES}>
        <div className="p-8 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-2 text-gray-500">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className={CARD_CLASSES}>
        <div className="p-8 text-center text-gray-500">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={CARD_CLASSES}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              시간
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              방향
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              타입
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              금액
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              체결가
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
              상태
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {orders.map((order) => {
            const statusStyle = STATUS_STYLES[order.status] || STATUS_STYLES.PENDING;
            const sideStyle = SIDE_STYLES[order.side] || SIDE_STYLES.BUY;

            return (
              <tr key={order.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                  {formatDate(order.created_at)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  <span
                    className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${sideStyle.bg} ${sideStyle.text}`}
                  >
                    {SIDE_LABELS[order.side]}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                  {order.order_type === "MARKET" ? "시장가" : "지정가"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                  {formatAmount(order.amount)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                  {order.executed_price ? formatAmount(order.executed_price) : "-"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-center text-sm">
                  <span
                    className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${statusStyle.bg} ${statusStyle.text}`}
                  >
                    {STATUS_LABELS[order.status]}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default OrderTable;
