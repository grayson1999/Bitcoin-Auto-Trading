import { type FC, type SVGProps, type ComponentType, useEffect } from "react";
import type { TradingSignal } from "../hooks/useApi";
import {
    ArrowTrendingUpIcon,
    HandRaisedIcon,
    ArrowTrendingDownIcon,
    CpuChipIcon,
    CheckCircleIcon,
    XCircleIcon,
    ClockIcon,
    XMarkIcon
} from "@heroicons/react/24/outline";
import {
    formatDate,
    formatPrice,
    getConfidencePercent,
    getBiasLabel,
    getTrendLabel
} from "../utils/formatters";

type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

interface SignalDetailModalProps {
    signal: TradingSignal;
    onClose: () => void;
}

const SIGNAL_STYLES: Record<string, { bg: string; text: string; label: string; icon: HeroIcon; gradient: string }> = {
    BUY: {
        bg: "bg-emerald-50",
        text: "text-emerald-700",
        label: "매수",
        icon: ArrowTrendingUpIcon,
        gradient: "from-emerald-500 to-teal-500"
    },
    HOLD: {
        bg: "bg-amber-50",
        text: "text-amber-700",
        label: "관망",
        icon: HandRaisedIcon,
        gradient: "from-amber-400 to-orange-400"
    },
    SELL: {
        bg: "bg-rose-50",
        text: "text-rose-700",
        label: "매도",
        icon: ArrowTrendingDownIcon,
        gradient: "from-rose-500 to-pink-500"
    },
};

const SignalDetailModal: FC<SignalDetailModalProps> = ({ signal, onClose }) => {
    const style = SIGNAL_STYLES[signal.signal_type] || SIGNAL_STYLES.HOLD;
    const confidencePercent = getConfidencePercent(signal.confidence);
    const Icon = style.icon;

    // Prevent background scrolling when modal is open
    useEffect(() => {
        document.body.style.overflow = "hidden";
        return () => {
            document.body.style.overflow = "unset";
        };
    }, []);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl glass-panel border border-white/10 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
                {/* Decorative gradient background opacity */}
                <div className={`absolute top-0 right-0 -mt-12 -mr-12 h-40 w-40 rounded-full opacity-10 blur-3xl bg-gradient-to-br ${style.gradient}`} />

                {/* Header */}
                <div className="sticky top-0 z-20 flex items-center justify-between p-6 border-b border-white/5 bg-dark-bg/80 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        <span
                            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold text-white shadow-lg bg-gradient-to-r ${style.gradient}`}
                        >
                            <Icon className="w-4 h-4" />
                            {style.label}
                        </span>
                        <span className="text-sm text-dark-text-secondary">
                            #{signal.id}
                        </span>
                    </div>
                    <button
                        onClick={onClose}
                        className="rounded-full p-2 text-dark-text-muted hover:bg-white/10 hover:text-white transition-colors"
                    >
                        <XMarkIcon className="w-6 h-6" />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Main Info */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold text-white">AI 신호 상세 정보</h3>
                            <p className="text-sm text-dark-text-muted">생성 일시: {formatDate(signal.created_at)}</p>
                        </div>

                        {/* Confidence */}
                        <div className="flex items-center gap-3 bg-white/5 rounded-xl px-4 py-2 border border-white/5">
                            <div className="text-right">
                                <p className="text-xs text-dark-text-muted">신뢰도</p>
                                <p className="text-lg font-bold text-white text-glow">{confidencePercent}%</p>
                            </div>
                            <div className="relative h-10 w-10">
                                <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
                                    <path
                                        className="text-white/10"
                                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                    <path
                                        className={`${style.text}`}
                                        strokeDasharray={`${confidencePercent}, 100`}
                                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* AI Analysis Reasoning */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-dark-text-secondary flex items-center gap-2">
                            <CpuChipIcon className="w-4 h-4 text-banana-400" />
                            AI 분석 근거
                        </h4>
                        <div className="bg-white/5 rounded-xl p-4 border border-white/5 text-sm leading-relaxed text-white/90">
                            {signal.reasoning}
                        </div>
                    </div>

                    {/* Technical Snapshot */}
                    {signal.technical_snapshot && (
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-dark-text-secondary">기술적 분석</h4>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {/* Confluence Score */}
                                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                                    <span className="text-xs text-dark-text-muted">기술적 종합 점수</span>
                                    <p className="text-xl font-bold text-banana-400 mt-1">
                                        {(signal.technical_snapshot.confluence_score * 100).toFixed(0)}%
                                    </p>
                                </div>
                                {/* Overall Bias */}
                                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                                    <span className="text-xs text-dark-text-muted">시장 방향성</span>
                                    <p className={`text-xl font-bold mt-1 ${getBiasLabel(signal.technical_snapshot.overall_bias).color}`}>
                                        {getBiasLabel(signal.technical_snapshot.overall_bias).label}
                                    </p>
                                </div>
                            </div>

                            {/* Timeframes */}
                            {signal.technical_snapshot.timeframes && (
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                                    {Object.entries(signal.technical_snapshot.timeframes).map(([tf, data]) => (
                                        <div key={tf} className="bg-white/5 rounded-xl p-3 border border-white/5">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs font-bold text-dark-text-secondary uppercase">{tf}</span>
                                                <span className={`text-xs font-medium ${getTrendLabel(data.trend).color}`}>
                                                    {getTrendLabel(data.trend).label}
                                                </span>
                                            </div>
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-dark-text-muted">강도</span>
                                                    <span className="text-white">{(data.strength * 100).toFixed(0)}%</span>
                                                </div>
                                                {data.indicators && (
                                                    <div className="flex justify-between text-xs">
                                                        <span className="text-dark-text-muted">RSI</span>
                                                        <span className="text-white">{data.indicators.rsi_14?.toFixed(0) ?? '-'}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Performance Tracking */}
                    {signal.price_at_signal && (
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-dark-text-secondary flex items-center gap-2">
                                <ClockIcon className="w-4 h-4" />
                                성과 추적
                                {signal.outcome_evaluated && (
                                    signal.outcome_correct ? (
                                        <span className="text-emerald-400 text-xs flex items-center gap-1 bg-emerald-400/10 px-2 py-0.5 rounded ml-2">
                                            <CheckCircleIcon className="w-3 h-3" /> 적중
                                        </span>
                                    ) : (
                                        <span className="text-rose-400 text-xs flex items-center gap-1 bg-rose-400/10 px-2 py-0.5 rounded ml-2">
                                            <XCircleIcon className="w-3 h-3" /> 실패
                                        </span>
                                    )
                                )}
                            </h4>
                            <div className="bg-white/5 rounded-xl border border-white/5 overflow-hidden">
                                <div className="grid grid-cols-3 divide-x divide-white/5">
                                    <div className="p-4 text-center">
                                        <span className="text-xs text-dark-text-muted block mb-1">진입가</span>
                                        <span className="text-sm font-bold text-white">{formatPrice(signal.price_at_signal)}</span>
                                    </div>
                                    <div className="p-4 text-center">
                                        <span className="text-xs text-dark-text-muted block mb-1">4시간 후</span>
                                        <span className="text-sm font-bold text-white">{formatPrice(signal.price_after_4h)}</span>
                                    </div>
                                    <div className="p-4 text-center">
                                        <span className="text-xs text-dark-text-muted block mb-1">24시간 후</span>
                                        <span className="text-sm font-bold text-white">{formatPrice(signal.price_after_24h)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Footer Meta */}
                    <div className="pt-4 border-t border-white/5 flex flex-wrap gap-4 text-xs text-dark-text-muted">
                        <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/5">모델</span>
                            {signal.model_name}
                        </div>
                        <span>입력 토큰: {signal.input_tokens}</span>
                        <span>출력 토큰: {signal.output_tokens}</span>
                        <span className="ml-auto">ID: {signal.id}</span>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default SignalDetailModal;
