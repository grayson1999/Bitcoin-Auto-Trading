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
const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  PENDING: { bg: "bg-banana-500/10", text: "text-banana-400", dot: "bg-banana-500" },
  EXECUTED: { bg: "bg-emerald-500/10", text: "text-emerald-400", dot: "bg-emerald-500" },
  CANCELLED: { bg: "bg-white/5", text: "text-dark-text-muted", dot: "bg-slate-500" },
  FAILED: { bg: "bg-rose-500/10", text: "text-rose-400", dot: "bg-rose-500" },
};

const SIDE_STYLES: Record<string, { bg: string; text: string }> = {
  BUY: { bg: "bg-banana-500/10", text: "text-banana-400" },
  SELL: { bg: "bg-rose-500/10", text: "text-rose-400" },
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

const CARD_CLASSES = "rounded-xl glass-panel overflow-hidden";

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
        <div className="p-12 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-banana-500 border-t-transparent"></div>
          <p className="mt-4 text-sm font-medium text-dark-text-muted">데이터를 불러오는 중입니다...</p>
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className={CARD_CLASSES}>
        <div className="p-12 text-center text-dark-text-muted font-medium">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={CARD_CLASSES}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-dark-border">
          <thead className="bg-white/5">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                시간
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                방향
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                타입
              </th>
              <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                금액
              </th>
              <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                체결가
              </th>
              <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-dark-text-secondary">
                상태
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border bg-transparent">
            {orders.map((order) => {
              const statusStyle = STATUS_STYLES[order.status] || STATUS_STYLES.PENDING;
              const sideStyle = SIDE_STYLES[order.side] || SIDE_STYLES.BUY;

              return (
                <tr key={order.id} className="hover:bg-white/5 transition-colors">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-white font-medium">
                    {formatDate(order.created_at)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${sideStyle.bg} ${sideStyle.text} ring-current/10`}
                    >
                      {SIDE_LABELS[order.side]}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-dark-text-secondary font-medium">
                    {order.order_type === "MARKET" ? "시장가" : "지정가"}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-white font-semibold courier">
                    {formatAmount(order.amount)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-white font-semibold courier">
                    {order.executed_price ? formatAmount(order.executed_price) : "-"}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                    <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${statusStyle.bg} border border-transparent`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${statusStyle.dot}`} />
                      <span className={`text-xs font-semibold ${statusStyle.text}`}>
                        {STATUS_LABELS[order.status]}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrderTable;
