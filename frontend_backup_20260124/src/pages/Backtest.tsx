/**
 * 백테스트 페이지 컴포넌트 (T093, T094)
 *
 * 과거 데이터로 AI 전략을 시뮬레이션하여 성과를 분석합니다.
 * - 백테스트 실행 폼
 * - 진행 표시기
 * - 결과 목록 및 상세 보기
 */

import { useState, type FC } from "react";
import {
  useBacktestResults,
  useBacktestResult,
  useRunBacktest,
  type BacktestResult,
  type TradeRecord,
} from "../hooks/useApi";

// === 상수 ===
const DEFAULT_INITIAL_CAPITAL = 1000000; // 기본 초기 자본금 (100만원)

/**
 * 금액 포맷
 */
function formatKRW(amount: string | number): string {
  const num = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * 퍼센트 포맷
 */
function formatPercent(value: string | number | null, decimals = 2): string {
  if (value === null) return "-";
  const num = typeof value === "string" ? Number(value) : value;
  return `${num >= 0 ? "+" : ""}${num.toFixed(decimals)}%`;
}

/**
 * 날짜 포맷
 */
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

/**
 * 날짜/시간 포맷
 */
function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * 상태 배지 컴포넌트
 */
const StatusBadge: FC<{ status: BacktestResult["status"] }> = ({ status }) => {
  const statusConfig = {
    PENDING: { color: "bg-yellow-500/10 text-yellow-400 ring-yellow-500/20", text: "대기중" },
    RUNNING: { color: "bg-blue-500/10 text-blue-400 ring-blue-500/20", text: "실행중" },
    COMPLETED: { color: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20", text: "완료" },
    FAILED: { color: "bg-rose-500/10 text-rose-400 ring-rose-500/20", text: "실패" },
  };

  const config = statusConfig[status];

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${config.color}`}>
      {status === "RUNNING" && (
        <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse"></span>
      )}
      {config.text}
    </span>
  );
};

/**
 * 백테스트 결과 카드 컴포넌트
 */
const ResultCard: FC<{
  result: BacktestResult;
  onSelect: () => void;
  isSelected: boolean;
}> = ({ result, onSelect, isSelected }) => {
  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-xl cursor-pointer transition-all ${isSelected
          ? "bg-blue-500/10 border-2 border-blue-500/50"
          : "bg-white/5 border border-white/10 hover:bg-white/10"
        }`}
    >
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="min-w-0 flex-1">
          <h4 className="font-medium text-white truncate text-sm sm:text-base" title={result.name}>
            {result.name}
          </h4>
          <p className="text-xs text-dark-text-muted mt-1 truncate">
            {formatDate(result.start_date)} ~ {formatDate(result.end_date)}
          </p>
        </div>
        <div className="flex-shrink-0">
          <StatusBadge status={result.status} />
        </div>
      </div>

      {result.status === "COMPLETED" && (
        <div className="grid grid-cols-2 gap-x-2 gap-y-3 mt-3">
          <div>
            <p className="text-[10px] text-dark-text-muted">수익률</p>
            <p className={`text-sm font-bold courier ${Number(result.total_return_pct) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}>
              {formatPercent(result.total_return_pct)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-dark-text-muted">MDD</p>
            <p className="text-sm font-bold courier text-rose-400">
              -{Number(result.max_drawdown_pct || 0).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-[10px] text-dark-text-muted">승률</p>
            <p className="text-sm font-bold courier text-white">
              {Number(result.win_rate_pct || 0).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-[10px] text-dark-text-muted">거래</p>
            <p className="text-sm font-bold courier text-white">
              {result.total_trades || 0}회
            </p>
          </div>
        </div>
      )}

      {result.status === "FAILED" && result.error_message && (
        <p className="text-xs text-rose-400 mt-2 line-clamp-2">
          {result.error_message}
        </p>
      )}
    </div>
  );
};

/**
 * 백테스트 실행 폼 컴포넌트
 */
const BacktestForm: FC<{
  onSubmit: (data: { name: string; start_date: string; end_date: string; initial_capital: number }) => void;
  isLoading: boolean;
}> = ({ onSubmit, isLoading }) => {
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [initialCapital, setInitialCapital] = useState(DEFAULT_INITIAL_CAPITAL);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !startDate || !endDate) return;

    onSubmit({
      name,
      start_date: new Date(startDate).toISOString(),
      end_date: new Date(endDate).toISOString(),
      initial_capital: initialCapital,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-dark-text-secondary mb-1">
          백테스트 이름
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="예: 6개월 전략 테스트"
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-dark-text-secondary mb-1">
            시작 날짜
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text-secondary mb-1">
            종료 날짜
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-secondary mb-1">
          초기 자본금 (KRW)
        </label>
        <input
          type="number"
          value={initialCapital}
          onChange={(e) => setInitialCapital(Number(e.target.value))}
          min={100000}
          max={1000000000}
          step={100000}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          required
        />
        <p className="text-xs text-dark-text-muted mt-1">
          {formatKRW(initialCapital)}
        </p>
      </div>

      <button
        type="submit"
        disabled={isLoading || !name || !startDate || !endDate}
        className="w-full py-2.5 px-4 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            실행 중...
          </>
        ) : (
          "백테스트 실행"
        )}
      </button>
    </form>
  );
};

/**
 * 백테스트 결과 상세 컴포넌트
 */
const ResultDetail: FC<{ resultId: number }> = ({ resultId }) => {
  const { data: result, isLoading } = useBacktestResult(resultId);

  if (isLoading || !result) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">{result.name}</h3>
          <p className="text-sm text-dark-text-muted mt-1">
            {formatDate(result.start_date)} ~ {formatDate(result.end_date)}
          </p>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {/* 성과 지표 그리드 */}
      {result.status === "COMPLETED" && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-dark-text-muted mb-1">총 수익률</p>
              <p className={`text-xl font-bold courier ${Number(result.total_return_pct) >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}>
                {formatPercent(result.total_return_pct)}
              </p>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-dark-text-muted mb-1">최대 낙폭 (MDD)</p>
              <p className="text-xl font-bold courier text-rose-400">
                -{Number(result.max_drawdown_pct || 0).toFixed(2)}%
              </p>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-dark-text-muted mb-1">승률</p>
              <p className="text-xl font-bold courier text-white">
                {Number(result.win_rate_pct || 0).toFixed(1)}%
              </p>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-dark-text-muted mb-1">손익비</p>
              <p className="text-xl font-bold courier text-white">
                {Number(result.profit_factor || 0).toFixed(2)}
              </p>
            </div>
          </div>

          {/* 추가 지표 */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-white/5 rounded-lg">
              <p className="text-xs text-dark-text-muted">초기 자본</p>
              <p className="text-sm font-medium text-white courier">
                {formatKRW(result.initial_capital)}
              </p>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <p className="text-xs text-dark-text-muted">최종 자본</p>
              <p className="text-sm font-medium text-white courier">
                {result.final_capital ? formatKRW(result.final_capital) : "-"}
              </p>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <p className="text-xs text-dark-text-muted">샤프 비율</p>
              <p className="text-sm font-medium text-white courier">
                {Number(result.sharpe_ratio || 0).toFixed(2)}
              </p>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <p className="text-xs text-dark-text-muted">총 거래</p>
              <p className="text-sm font-medium text-white">
                {result.total_trades || 0}회
                ({result.winning_trades || 0}승 / {result.losing_trades || 0}패)
              </p>
            </div>
          </div>

          {/* 거래 내역 */}
          {result.trade_history && result.trade_history.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-dark-text-secondary mb-3">
                거래 내역 ({result.trade_history.length}건)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-dark-text-muted border-b border-white/10">
                      <th className="pb-2 font-medium">시간</th>
                      <th className="pb-2 font-medium">타입</th>
                      <th className="pb-2 font-medium text-right">가격</th>
                      <th className="pb-2 font-medium text-right">수량</th>
                      <th className="pb-2 font-medium text-right">손익</th>
                      <th className="pb-2 font-medium text-right">잔고</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trade_history.slice(0, 20).map((trade: TradeRecord, index: number) => (
                      <tr key={index} className="border-b border-white/5">
                        <td className="py-2 text-dark-text-secondary">
                          {formatDateTime(trade.timestamp)}
                        </td>
                        <td className="py-2">
                          <span className={`font-medium ${trade.signal_type === "BUY" ? "text-emerald-400" : "text-rose-400"
                            }`}>
                            {trade.signal_type === "BUY" ? "매수" : "매도"}
                          </span>
                        </td>
                        <td className="py-2 text-right text-white courier">
                          {formatKRW(trade.price)}
                        </td>
                        <td className="py-2 text-right text-white courier">
                          {trade.quantity.toFixed(4)}
                        </td>
                        <td className={`py-2 text-right courier ${trade.pnl >= 0 ? "text-emerald-400" : "text-rose-400"
                          }`}>
                          {trade.signal_type === "SELL" ? (
                            <>
                              {formatKRW(trade.pnl)}
                              <span className="text-xs ml-1">
                                ({formatPercent(trade.pnl_pct)})
                              </span>
                            </>
                          ) : "-"}
                        </td>
                        <td className="py-2 text-right text-white courier">
                          {formatKRW(trade.balance_after)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {result.trade_history.length > 20 && (
                  <p className="text-center text-dark-text-muted text-xs mt-2">
                    ... 외 {result.trade_history.length - 20}건 더 있음
                  </p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* 오류 메시지 */}
      {result.status === "FAILED" && result.error_message && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl">
          <p className="text-rose-400 text-sm">{result.error_message}</p>
        </div>
      )}

      {/* 메타 정보 */}
      <div className="text-xs text-dark-text-muted pt-4 border-t border-white/10">
        <p>생성: {formatDateTime(result.created_at)}</p>
        {result.completed_at && (
          <p>완료: {formatDateTime(result.completed_at)}</p>
        )}
      </div>
    </div>
  );
};

/**
 * Backtest 페이지 컴포넌트
 */
const Backtest: FC = () => {
  const [selectedResultId, setSelectedResultId] = useState<number | null>(null);
  const { data: results, isLoading, error } = useBacktestResults(20);
  const runBacktest = useRunBacktest();

  const handleRunBacktest = async (data: {
    name: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
  }) => {
    try {
      const response = await runBacktest.mutateAsync(data);
      setSelectedResultId(response.result.id);
    } catch (err) {
      console.error("백테스트 실행 실패:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-3 text-gray-500">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-6 text-center">
        <p className="text-red-600">
          데이터를 불러올 수 없습니다. 백엔드 서버를 확인하세요.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white text-glow">백테스트</h2>
        <p className="text-dark-text-secondary mt-1">
          과거 데이터로 AI 전략을 시뮬레이션하여 성과를 분석합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 실행 폼 + 결과 목록 */}
        <div className="space-y-6">
          {/* 백테스트 실행 폼 */}
          <div className="rounded-2xl glass-panel p-6">
            <h3 className="text-lg font-bold text-white mb-4">새 백테스트</h3>
            <BacktestForm
              onSubmit={handleRunBacktest}
              isLoading={runBacktest.isPending}
            />
            {runBacktest.error && (
              <p className="mt-3 text-sm text-rose-400">
                오류: {runBacktest.error.message}
              </p>
            )}
          </div>

          {/* 결과 목록 */}
          <div className="rounded-2xl glass-panel p-6">
            <h3 className="text-lg font-bold text-white mb-4">
              이전 결과
              {results && results.total > 0 && (
                <span className="ml-2 text-sm font-normal text-dark-text-muted">
                  ({results.total}건)
                </span>
              )}
            </h3>
            {results && results.items.length > 0 ? (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {results.items.map((result) => (
                  <ResultCard
                    key={result.id}
                    result={result}
                    onSelect={() => setSelectedResultId(result.id)}
                    isSelected={selectedResultId === result.id}
                  />
                ))}
              </div>
            ) : (
              <p className="text-center py-8 text-dark-text-muted">
                아직 백테스트 결과가 없습니다
              </p>
            )}
          </div>
        </div>

        {/* 오른쪽: 결과 상세 */}
        <div className="lg:col-span-2">
          <div className="rounded-2xl glass-panel p-6 min-h-[400px]">
            {selectedResultId ? (
              <ResultDetail resultId={selectedResultId} />
            ) : (
              <div className="flex items-center justify-center h-64 text-dark-text-muted">
                <div className="text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-dark-text-muted mb-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  <p>백테스트를 실행하거나 결과를 선택하세요</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Backtest;
