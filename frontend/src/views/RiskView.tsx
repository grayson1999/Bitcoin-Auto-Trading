import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchRiskEvents } from '@/api/risk.api'
import { RiskEventTimeline } from '@/components/risk/RiskEventTimeline'
import { CommonCard } from '@core/components/CommonCard'
import { ErrorMessage } from '@core/components/ErrorMessage'
import { Button } from '@core/components/ui/button'
import { cn } from '@core/utils'
import { RefreshCw } from 'lucide-react'

const EVENT_LIMIT = 100

interface FilterOption {
  value: string
  label: string
}

const FILTER_OPTIONS: FilterOption[] = [
  { value: '', label: '전체' },
  { value: 'STOP_LOSS', label: 'STOP_LOSS' },
  { value: 'DAILY_LIMIT', label: 'DAILY_LIMIT' },
  { value: 'VOLATILITY_HALT', label: 'VOLATILITY_HALT' },
]

export function RiskView() {
  const [eventTypeFilter, setEventTypeFilter] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['riskEvents', eventTypeFilter],
    queryFn: () =>
      fetchRiskEvents({ limit: EVENT_LIMIT, event_type: eventTypeFilter || undefined }),
    staleTime: 30000,
  })

  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">리스크 이벤트</h1>
        </div>
        <ErrorMessage
          title="리스크 이벤트 로딩 실패"
          message={
            error instanceof Error
              ? error.message
              : '리스크 이벤트를 불러오는 중 오류가 발생했습니다.'
          }
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const events = data?.items ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">리스크 이벤트</h1>
          <p className="text-sm text-muted-foreground mt-1">
            손절, 손실 한도, 변동성 중단 등 리스크 관리 이벤트 타임라인입니다
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn('h-4 w-4 mr-2', isFetching && 'animate-spin')} />
          새로고침
        </Button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2 flex-wrap">
        {FILTER_OPTIONS.map((option) => (
          <Button
            key={option.value || 'all'}
            variant={eventTypeFilter === option.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setEventTypeFilter(option.value)}
          >
            {option.label}
          </Button>
        ))}
      </div>

      {/* Content */}
      <CommonCard noPadding className="overflow-hidden">
        <div className="p-4">
          <RiskEventTimeline events={events} isLoading={isLoading} />
        </div>
      </CommonCard>
    </div>
  )
}

export default RiskView
