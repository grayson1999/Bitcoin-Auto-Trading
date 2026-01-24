
import { useState, type FC } from "react";

// === Mock Data Types ===
interface BacktestResult {
  id: number;
  name: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  start_date: string;
  end_date: string;
  initial_capital: string;
  final_capital: string | null;
  total_return_pct: string | null;
  max_drawdown_pct: string | null;
  win_rate_pct: string | null;
  total_trades: number | null;
  profit_factor: string | null;
  sharpe_ratio: string | null;
  winning_trades: number | null;
  losing_trades: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  trade_history?: any[];
}

const MOCK_RESULTS: BacktestResult[] = [
  {
    id: 1,
    name: "Golden Channel Strategy (Optimized)",
    status: "COMPLETED",
    start_date: "2023-01-01T00:00:00Z",
    end_date: "2023-06-30T23:59:59Z",
    initial_capital: "10000000",
    final_capital: "12543000",
    total_return_pct: "25.43",
    max_drawdown_pct: "5.21",
    win_rate_pct: "65.4",
    total_trades: 42,
    profit_factor: "2.1",
    sharpe_ratio: "1.8",
    winning_trades: 27,
    losing_trades: 15,
    error_message: null,
    created_at: "2023-07-01T10:00:00Z",
    completed_at: "2023-07-01T10:05:00Z",
    trade_history: [],
  },
  {
    id: 2,
    name: "RSI Reversal Short-term",
    status: "COMPLETED",
    start_date: "2023-06-01T00:00:00Z",
    end_date: "2023-06-30T23:59:59Z",
    initial_capital: "5000000",
    final_capital: "4850000",
    total_return_pct: "-3.00",
    max_drawdown_pct: "8.50",
    win_rate_pct: "40.0",
    total_trades: 15,
    profit_factor: "0.85",
    sharpe_ratio: "-0.5",
    winning_trades: 6,
    losing_trades: 9,
    error_message: null,
    created_at: "2023-07-01T11:00:00Z",
    completed_at: "2023-07-01T11:02:00Z",
    trade_history: [],
  },
  {
    id: 3,
    name: "Trend Follow V2",
    status: "RUNNING",
    start_date: "2023-01-01T00:00:00Z",
    end_date: "2023-12-31T23:59:59Z",
    initial_capital: "20000000",
    final_capital: null,
    total_return_pct: null,
    max_drawdown_pct: null,
    win_rate_pct: null,
    total_trades: null,
    profit_factor: null,
    sharpe_ratio: null,
    winning_trades: null,
    losing_trades: null,
    error_message: null,
    created_at: "2023-07-01T12:00:00Z",
    completed_at: null,
    trade_history: [],
  },
  {
    id: 4,
    name: "High Volatility Breakout",
    status: "FAILED",
    start_date: "2023-05-01T00:00:00Z",
    end_date: "2023-05-31T23:59:59Z",
    initial_capital: "1000000",
    final_capital: null,
    total_return_pct: null,
    max_drawdown_pct: null,
    win_rate_pct: null,
    total_trades: null,
    profit_factor: null,
    sharpe_ratio: null,
    winning_trades: null,
    losing_trades: null,
    error_message: "Insufficient data for the requested period.",
    created_at: "2023-07-01T13:00:00Z",
    completed_at: "2023-07-01T13:00:05Z",
    trade_history: [],
  },
  {
    id: 5,
    name: "A very very long name Strategy used to test layout issues when the name is extremely long and wraps multiple lines",
    status: "COMPLETED",
    start_date: "2023-01-01T00:00:00Z",
    end_date: "2023-06-30T23:59:59Z",
    initial_capital: "10000000",
    final_capital: "12543000",
    total_return_pct: "12345.67",
    max_drawdown_pct: "5.21",
    win_rate_pct: "65.4",
    total_trades: 9999,
    profit_factor: "2.1",
    sharpe_ratio: "1.8",
    winning_trades: 27,
    losing_trades: 15,
    error_message: null,
    created_at: "2023-07-01T10:00:00Z",
    completed_at: "2023-07-01T10:05:00Z",
    trade_history: [],
  },
];

// === 상수 ===
const DEFAULT_INITIAL_CAPITAL = 1000000;

function formatKRW(amount: string | number): string {
  const num = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(num);
}

function formatPercent(value: string | number | null, decimals = 2): string {
  if (value === null) return "-";
  const num = typeof value === "string" ? Number(value) : value;
  return `${num >= 0 ? "+" : ""}${num.toFixed(decimals)}%`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-white">{result.name}</h4>
          <p className="text-xs text-dark-text-muted mt-1">
            {formatDate(result.start_date)} ~ {formatDate(result.end_date)}
          </p>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {result.status === "COMPLETED" && (
        <div className="grid grid-cols-2 gap-3 mt-3">
          <div>
            <p className="text-xs text-dark-text-muted">수익률</p>
            <p className={`text-sm font-bold courier ${Number(result.total_return_pct) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}>
              {formatPercent(result.total_return_pct)}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted">MDD</p>
            <p className="text-sm font-bold courier text-rose-400">
              -{Number(result.max_drawdown_pct || 0).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted">승률</p>
            <p className="text-sm font-bold courier text-white">
              {Number(result.win_rate_pct || 0).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted">거래 횟수</p>
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

const ResultDetail: FC<{ resultId: number }> = ({ resultId }) => {
  const result = MOCK_RESULTS.find(r => r.id === resultId);

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64">
        <p>결과를 찾을 수 없습니다.</p>
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

          <div className="text-center py-8 text-dark-text-muted">
            (거래 내역 생략)
          </div>
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

const BacktestMock: FC = () => {
  const [selectedResultId, setSelectedResultId] = useState<number | null>(null);

  const handleRunBacktest = async (data: any) => {
    alert("This is a mock version. Backtest would start: " + JSON.stringify(data));
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
      {/* 페이지 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white text-glow">백테스트 (MOCK)</h2>
        <p className="text-dark-text-secondary mt-1">
          과거 데이터로 AI 전략을 시뮬레이션하여 성과를 분석합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 실행 폼 + 결과 목록 */}
        <div className="space-y-6">
          {/* 백테스트 실행 폼 */}
          <div className="rounded-2xl glass-panel p-6 bg-gray-900 border border-gray-800">
            <h3 className="text-lg font-bold text-white mb-4">새 백테스트</h3>
            <BacktestForm
              onSubmit={handleRunBacktest}
              isLoading={false}
            />
          </div>

          {/* 결과 목록 */}
          <div className="rounded-2xl glass-panel p-6 bg-gray-900 border border-gray-800">
            <h3 className="text-lg font-bold text-white mb-4">
              이전 결과
              <span className="ml-2 text-sm font-normal text-dark-text-muted">
                ({MOCK_RESULTS.length}건)
              </span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar">
              {MOCK_RESULTS.map((result) => (
                <ResultCard
                  key={result.id}
                  result={result as any}
                  onSelect={() => setSelectedResultId(result.id)}
                  isSelected={selectedResultId === result.id}
                />
              ))}
            </div>
          </div>
        </div>

        {/* 오른쪽: 결과 상세 */}
        <div className="lg:col-span-2">
          <div className="rounded-2xl glass-panel p-6 min-h-[400px] bg-gray-900 border border-gray-800">
            {selectedResultId ? (
              <ResultDetail resultId={selectedResultId} />
            ) : (
              <div className="flex items-center justify-center h-64 text-dark-text-muted">
                <div className="text-center">
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

export default BacktestMock;
