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
  positive: "#34D399", // emerald-400 (brighter for dark mode)
  negative: "#F87171", // red-400
  neutral: "#9CA3AF", // gray-400
  fill: "#FACC15", // banana-400 (Nano Yellow)
  stroke: "#EAB308", // banana-500
} as const;

const CARD_CLASSES = "rounded-2xl glass-panel p-6";

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
  // Use styling class or inline style with new colors
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
          <h3 className="text-sm font-medium text-dark-text-secondary">XRP/KRW</h3>
          <p className="mt-1 text-3xl font-bold text-white tracking-tight text-glow">
            {formatPrice(currentPrice)}
          </p>
        </div>
        <div className="text-right">
          <span className="block text-sm text-dark-text-secondary">24h</span>
          <p className="text-lg font-medium inline-flex items-center gap-1" style={{ color: changeColor }}>
            {change24h !== null ? `${changeSign}${change24h.toFixed(2)}%` : "-"}
            <span className="relative group">
              <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[10px] text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                ?
              </span>
              <span className="absolute right-0 bottom-full mb-2 px-3 py-2 text-xs font-normal text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                24시간 전 대비 가격 변동률
                <span className="absolute right-3 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
              </span>
            </span>
          </p>
        </div>
      </div>

      {/* 차트 영역 */}
      <div className="h-56 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={CHART_COLORS.fill}
                  stopOpacity={0.4}
                />
                <stop
                  offset="95%"
                  stopColor={CHART_COLORS.fill}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "#94A3B8" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#94A3B8" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${(value / 1).toFixed(0)}`}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0B0E14",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "12px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.5)",
                color: "#F1F5F9"
              }}
              itemStyle={{ color: "#F1F5F9" }}
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
