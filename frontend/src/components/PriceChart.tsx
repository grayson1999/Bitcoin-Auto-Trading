/**
 * 가격 차트 컴포넌트 (T078)
 *
 * Recharts를 사용하여 XRP 가격 추이를 표시합니다.
 * - 현재가 및 24시간 변동률
 * - 영역 차트로 가격 추이 시각화
 */

import type { FC } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// === 타입 정의 ===
interface PriceChartProps {
  /** 현재 가격 */
  currentPrice: number;
  /** 24시간 변동률 (%) */
  change24h: number | null;
  /** 차트 데이터 (선택) */
  data?: Array<{
    time: string;
    price: number;
  }>;
}

// === 상수 ===
const CHART_COLORS = {
  positive: "#10B981", // green-500
  negative: "#EF4444", // red-500
  neutral: "#6B7280", // gray-500
  fill: "#3B82F6", // blue-500
  stroke: "#2563EB", // blue-600
} as const;

const CARD_CLASSES = "rounded-lg bg-white p-6 shadow";

/**
 * 가격 포맷 헬퍼
 */
function formatPrice(price: number): string {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(price);
}

/**
 * 변동률 색상 결정
 */
function getChangeColor(change: number | null): string {
  if (change === null) return CHART_COLORS.neutral;
  return change >= 0 ? CHART_COLORS.positive : CHART_COLORS.negative;
}

/**
 * PriceChart 컴포넌트
 */
const PriceChart: FC<PriceChartProps> = ({ currentPrice, change24h, data }) => {
  const changeColor = getChangeColor(change24h);
  const changeSign = change24h !== null && change24h >= 0 ? "+" : "";

  // 임시 샘플 데이터 (실제 데이터가 없을 경우)
  const chartData =
    data && data.length > 0
      ? data
      : Array.from({ length: 24 }, (_, i) => ({
          time: `${i}:00`,
          price: currentPrice * (1 + (Math.random() - 0.5) * 0.02),
        }));

  return (
    <div className={CARD_CLASSES}>
      {/* 헤더: 현재가 및 변동률 */}
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-500">XRP/KRW</h3>
          <p className="mt-1 text-3xl font-semibold text-gray-900">
            {formatPrice(currentPrice)}
          </p>
        </div>
        <div className="text-right">
          <span className="text-sm text-gray-500">24h</span>
          <p className="text-lg font-medium" style={{ color: changeColor }}>
            {change24h !== null ? `${changeSign}${change24h.toFixed(2)}%` : "-"}
          </p>
        </div>
      </div>

      {/* 차트 영역 */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={CHART_COLORS.fill}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={CHART_COLORS.fill}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "#6B7280" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6B7280" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${(value / 1).toFixed(0)}`}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #E5E7EB",
                borderRadius: "8px",
              }}
              formatter={(value: number) => [formatPrice(value), "가격"]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={CHART_COLORS.stroke}
              fill="url(#priceGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PriceChart;
