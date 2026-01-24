import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSignals } from '@/api/signals.api'
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
import type { TradingSignal, SignalType } from '@/core/types'
import { Activity, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'

const PAGE_SIZE = 20

export function SignalsView() {
  const [selectedSignal, setSelectedSignal] = useState<TradingSignal | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filterType, setFilterType] = useState<SignalType | 'all'>('all')
  const [page, setPage] = useState(0)

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
      offset: page * PAGE_SIZE,
    }),
    staleTime: 30000, // 30 seconds
  })

  const signals = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const hasNextPage = page < totalPages - 1
  const hasPrevPage = page > 0

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

      {/* Filters and View Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <SignalTypeFilter value={filterType} onChange={handleFilterChange} />
        <ViewToggle value={viewMode} onChange={setViewMode} />
      </div>

      {/* Content */}
      <CommonCard noPadding className="p-4">
        {isLoading ? (
          renderSkeleton()
        ) : signals.length === 0 ? (
          <EmptyState
            icon={<Activity className="h-8 w-8 text-muted-foreground" />}
            title={filterType === 'all' ? '신호 없음' : `${filterType} 신호 없음`}
            description={
              filterType === 'all'
                ? '아직 생성된 AI 신호가 없습니다.'
                : `${filterType} 타입의 신호가 없습니다. 다른 필터를 시도해 보세요.`
            }
            action={
              filterType !== 'all' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleFilterChange('all')}
                >
                  전체 신호 보기
                </Button>
              )
            }
          />
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {signals.map((signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onClick={() => handleSignalClick(signal)}
              />
            ))}
          </div>
        ) : (
          <SignalTimeline
            signals={signals}
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
