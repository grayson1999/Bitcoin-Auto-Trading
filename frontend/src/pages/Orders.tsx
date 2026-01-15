/**
 * 주문 내역 페이지 컴포넌트 (T075)
 *
 * 거래 주문 내역을 조회하고 관리합니다.
 * - 주문 내역 테이블
 * - 주문 상태 필터링
 * - 페이지네이션
 */

import { useState, type FC } from "react";
import { useOrders } from "../hooks/useApi";
import OrderTable from "../components/OrderTable";

// === 상수 ===
const STATUS_OPTIONS = [
  { value: "all", label: "전체" },
  { value: "pending", label: "대기" },
  { value: "executed", label: "체결" },
  { value: "cancelled", label: "취소" },
  { value: "failed", label: "실패" },
];

const PAGE_SIZE = 20;

/**
 * Orders 컴포넌트
 */
const Orders: FC = () => {
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(0);

  const { data, isLoading, error } = useOrders(status, PAGE_SIZE, page * PAGE_SIZE);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">주문 내역</h2>
          <p className="text-gray-600">거래 주문을 조회하고 관리합니다.</p>
        </div>

        {/* 필터 */}
        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-sm text-gray-600">
            상태:
          </label>
          <select
            id="status-filter"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(0); // 필터 변경시 첫 페이지로
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-center text-red-600">
          주문 내역을 불러올 수 없습니다. 백엔드 서버를 확인하세요.
        </div>
      )}

      {/* 주문 테이블 */}
      <OrderTable
        orders={data?.items ?? []}
        isLoading={isLoading}
        emptyMessage="주문 내역이 없습니다."
      />

      {/* 페이지네이션 */}
      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-between border-t pt-4">
          <p className="text-sm text-gray-600">
            총 {data.total}건 중 {page * PAGE_SIZE + 1}-
            {Math.min((page + 1) * PAGE_SIZE, data.total)}건
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              이전
            </button>
            <span className="px-3 py-1 text-sm text-gray-600">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
