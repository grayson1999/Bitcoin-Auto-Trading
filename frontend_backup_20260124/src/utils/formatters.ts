export function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

export function formatPrice(price: string | null | undefined): string {
    if (!price) return "-";
    return Number(price).toLocaleString("ko-KR", { maximumFractionDigits: 0 }) + "원";
}

export function getConfidencePercent(confidence: string): number {
    return Math.round(Number(confidence) * 100);
}

export function getBiasLabel(bias: string): { label: string; color: string } {
    const map: Record<string, { label: string; color: string }> = {
        strong_buy: { label: "강력 매수", color: "text-emerald-400" },
        buy: { label: "매수", color: "text-green-400" },
        neutral: { label: "중립", color: "text-gray-400" },
        sell: { label: "매도", color: "text-orange-400" },
        strong_sell: { label: "강력 매도", color: "text-rose-400" },
    };
    return map[bias] || { label: bias, color: "text-gray-400" };
}

export function getTrendLabel(trend: string): { label: string; color: string } {
    const map: Record<string, { label: string; color: string }> = {
        bullish: { label: "상승", color: "text-emerald-400" },
        bearish: { label: "하락", color: "text-rose-400" },
        sideways: { label: "횡보", color: "text-amber-400" },
    };
    return map[trend] || { label: trend, color: "text-gray-400" };
}
