import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSignals, generateSignal, fetchSignalPerformance } from '@/api/signals.api'
import { isAxiosError } from 'axios'
import { SignalCard } from '@/components/signals/SignalCard'
import { SignalTimeline } from '@/components/signals/SignalTimeline'
import { SignalDetailModal } from '@/components/signals/SignalDetailModal'
import { SignalTypeFilter } from '@/components/signals/SignalTypeFilter'
import { ViewToggle, type ViewMode } from '@/components/signals/ViewToggle'
import { CommonCard } from '@core/components/CommonCard'
import { EmptyState } from '@core/components/EmptyState'
import { ErrorMessage } from '@core/components/ErrorMessage'
import { Button } from '@core/components/ui/button'
import { Skeleton } from '@core/components/ui/skeleton'
import { cn } from '@core/utils'
import { formatPercent } from '@core/utils/formatters'
import type { TradingSignal, SignalType } from '@/core/types'
import { Activity, ChevronLeft, ChevronRight, RefreshCw, Sparkles, AlertCircle } from 'lucide-react'

const PAGE_SIZE = 20

/** Client-side outcome filter options */
type OutcomeFilter = 'all' | 'hit' | 'miss'

const OUTCOME_FILTERS: { value: OutcomeFilter; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'hit', label: '적중만' },
  { value: 'miss', label: '실패만' },
]

/** Accuracy color based on threshold (>=60 emerald, 40-60 amber, <40 rose) */
function accuracyColor(pct: number): string {
  if (pct >= 60) return 'text-emerald-400'
  if (pct >= 40) return 'text-amber-400'
  return 'text-rose-400'
}

export function SignalsView() {
  const [selectedSignal, setSelectedSignal] = useState<TradingSignal | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filterType, setFilterType] = useState<SignalType | 'all'>('all')
  const [outcomeFilter, setOutcomeFilter] = useState<OutcomeFilter>('all')
  const [page, setPage] = useState(0)
  const [generateError, setGenerateError] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // Fetch signals with filter and pagination
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['signals', filterType, page],
    queryFn: () => fetchSignals({
      type: filterType,
      limit: PAGE_SIZE,
      page: page + 1,
    }),
    staleTime: 30000, // 30 seconds
  })

  // AI performance summary (admin-only; hide panel on error)
  const {
    data: performance,
    isLoading: isPerformanceLoading,
    isError: isPerformanceError,
  } = useQuery({
    queryKey: ['signalPerformance'],
    queryFn: fetchSignalPerformance,
    staleTime: 60000,
  })

  const signals = data?.items ?? []
  // Client-side outcome filter (only filters the already-fetched page)
  const filteredSignals = signals.filter((s) => {
    if (outcomeFilter === 'hit') return s.outcome_correct === true
    if (outcomeFilter === 'miss') return s.outcome_correct === false
    return true
  })
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const hasNextPage = page < totalPages - 1
  const hasPrevPage = page > 0

  // Generate signal mutation
  const generateMutation = useMutation({
    mutationFn: generateSignal,
    onSuccess: () => {
      setGenerateError(null)
      queryClient.invalidateQueries({ queryKey: ['signals'] })
    },
    onError: (error) => {
      if (isAxiosError(error)) {
        const status = error.response?.status
        const detail = error.response?.data?.detail
        if (status === 429) {
          setGenerateError(detail || '5분 내 재시도 불가합니다.')
        } else if (status === 503) {
          setGenerateError(detail || 'AI 서비스 오류가 발생했습니다.')
        } else {
          setGenerateError(detail || '신호 생성에 실패했습니다.')
        }
      } else {
        setGenerateError('신호 생성에 실패했습니다.')
      }
    },
  })

  const handleGenerateSignal = () => {
    setGenerateError(null)
    generateMutation.mutate()
  }

  // Handle signal click
  const handleSignalClick = (signal: TradingSignal) => {
    setSelectedSignal(signal)
    setIsModalOpen(true)
  }

  // Handle filter change - reset to first page
  const handleFilterChange = (newFilter: SignalType | 'all') => {
    setFilterType(newFilter)
    setPage(0)
  }

  // Pagination handlers
  const handlePrevPage = () => {
    if (hasPrevPage) {
      setPage(p => p - 1)
    }
  }

  const handleNextPage = () => {
    if (hasNextPage) {
      setPage(p => p + 1)
    }
  }

  // Loading skeleton
  const renderSkeleton = () => (
    <div className="space-y-4">
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-4 rounded-lg border border-border">
              <div className="flex items-center justify-between mb-3">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-5 w-12" />
              </div>
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-4 w-1/2 mb-3" />
              <div className="flex justify-between">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="pl-10 pr-4 py-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Skeleton className="h-5 w-16" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-2/3 mt-1" />
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Skeleton className="h-5 w-12" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // Error state
  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">AI 신호</h1>
        </div>
        <ErrorMessage
          title="신호 데이터 로딩 실패"
          message={error instanceof Error ? error.message : '신호 데이터를 불러오는 중 오류가 발생했습니다.'}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">AI 신호</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI가 생성한 매매 신호를 확인하고 분석합니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={handleGenerateSignal}
            disabled={generateMutation.isPending}
          >
            <Sparkles className={`h-4 w-4 mr-2 ${generateMutation.isPending ? 'animate-pulse' : ''}`} />
            {generateMutation.isPending ? '생성 중...' : '신호 생성'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </div>

      {/* Generate Error Message */}
      {generateError && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{generateError}</span>
          <button
            onClick={() => setGenerateError(null)}
            className="ml-auto text-xs hover:underline"
          >
            닫기
          </button>
        </div>
      )}

      {/* AI Performance Panel (admin-only; hidden on error) */}
      {!isPerformanceError && !isPerformanceLoading && performance && (
        <CommonCard title="AI 성과 요약">
          {performance.total_signals === 0 ? (
            <p className="text-sm text-muted-foreground">
              평가된 신호가 아직 없습니다 (4시간+ 경과 필요)
            </p>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">매수 정확도</p>
                  <p className={cn('text-lg font-semibold font-mono-num', accuracyColor(performance.buy_accuracy))}>
                    {formatPercent(performance.buy_accuracy, { decimals: 0 })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">매도 정확도</p>
                  <p className={cn('text-lg font-semibold font-mono-num', accuracyColor(performance.sell_accuracy))}>
                    {formatPercent(performance.sell_accuracy, { decimals: 0 })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">평균 신뢰도</p>
                  <p className="text-lg font-semibold font-mono-num text-zinc-200">
                    {formatPercent(performance.avg_confidence, { decimals: 0 })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">평균 24h 수익률</p>
                  <p
                    className={cn(
                      'text-lg font-semibold font-mono-num',
                      performance.avg_pnl_24h > 0
                        ? 'text-emerald-400'
                        : performance.avg_pnl_24h < 0
                          ? 'text-rose-400'
                          : 'text-zinc-200'
                    )}
                  >
                    {formatPercent(performance.avg_pnl_24h, { showSign: true, decimals: 2 })}
                  </p>
                </div>
              </div>
              {performance.feedback_summary && (
                <p className="text-sm text-zinc-400 leading-relaxed border-t border-white/5 pt-3">
                  {performance.feedback_summary}
                </p>
              )}
            </div>
          )}
        </CommonCard>
      )}

      {/* Filters and View Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <SignalTypeFilter value={filterType} onChange={handleFilterChange} />
          {/* Outcome filter (client-side, current page) */}
          <div className="inline-flex items-center rounded-lg border border-border bg-black/20 p-0.5">
            {OUTCOME_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setOutcomeFilter(f.value)}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded-md transition-colors',
                  outcomeFilter === f.value
                    ? 'bg-zinc-700 text-zinc-100'
                    : 'text-zinc-400 hover:text-zinc-200'
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
        <ViewToggle value={viewMode} onChange={setViewMode} />
      </div>

      {/* Content */}
      <CommonCard noPadding className="p-4">
        {isLoading ? (
          renderSkeleton()
        ) : filteredSignals.length === 0 ? (
          <EmptyState
            icon={<Activity className="h-8 w-8 text-muted-foreground" />}
            title={
              outcomeFilter !== 'all'
                ? `${OUTCOME_FILTERS.find((f) => f.value === outcomeFilter)?.label ?? ''} 신호 없음`
                : filterType === 'all'
                  ? '신호 없음'
                  : `${filterType} 신호 없음`
            }
            description={
              outcomeFilter !== 'all'
                ? '현재 페이지에 해당 결과의 신호가 없습니다. 다른 결과 필터를 시도해 보세요.'
                : filterType === 'all'
                  ? '아직 생성된 AI 신호가 없습니다.'
                  : `${filterType} 타입의 신호가 없습니다. 다른 필터를 시도해 보세요.`
            }
            action={
              outcomeFilter !== 'all' ? (
                <Button variant="outline" size="sm" onClick={() => setOutcomeFilter('all')}>
                  전체 결과 보기
                </Button>
              ) : (
                filterType !== 'all' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange('all')}
                  >
                    전체 신호 보기
                  </Button>
                )
              )
            }
          />
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSignals.map((signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onClick={() => handleSignalClick(signal)}
              />
            ))}
          </div>
        ) : (
          <SignalTimeline
            signals={filteredSignals}
            onSignalClick={handleSignalClick}
          />
        )}
      </CommonCard>

      {/* Pagination */}
      {!isLoading && signals.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            전체 {total}개 중 {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, total)}개 표시
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevPage}
              disabled={!hasPrevPage}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              이전
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page + 1} / {totalPages || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={!hasNextPage}
            >
              다음
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Signal Detail Modal */}
      <SignalDetailModal
        signal={selectedSignal}
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
      />
    </div>
  )
}

export default SignalsView
