import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchOrders, syncPendingOrders } from '@/api/trading.api'
import { OrderTable } from '@/components/trading/OrderTable'
import { OrderStatusFilter } from '@/components/trading/OrderStatusFilter'
import { ORDER_STATUS_LABELS } from '@/components/trading/OrderStatusBadge'
import { Pagination } from '@core/components/Pagination'
import { CommonCard } from '@core/components/CommonCard'
import { EmptyState } from '@core/components/EmptyState'
import { ErrorMessage } from '@core/components/ErrorMessage'
import { Button } from '@core/components/ui/button'
import { Skeleton } from '@core/components/ui/skeleton'
import type { OrderStatus } from '@/core/types'
import { FileText, RefreshCw, RotateCcw } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

const PAGE_SIZE = 20

export function OrdersView() {
  const [filterStatus, setFilterStatus] = useState<OrderStatus | 'all'>('all')
  const [page, setPage] = useState(0)

  const queryClient = useQueryClient()

  // Fetch orders with filter and pagination
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['orders', filterStatus, page],
    queryFn: () => fetchOrders({
      status: filterStatus,
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
    staleTime: 30000, // 30 seconds
  })

  // Sync pending orders mutation
  const syncMutation = useMutation({
    mutationFn: syncPendingOrders,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })

  const orders = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  // Handle filter change - reset to first page
  const handleFilterChange = (newFilter: OrderStatus | 'all') => {
    setFilterStatus(newFilter)
    setPage(0)
  }

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  // Loading skeleton for table
  const renderSkeleton = () => (
    <div className="space-y-2">
      {/* Table header skeleton */}
      <div className="h-12 bg-muted/50 rounded-t-lg" />
      {/* Table rows skeleton */}
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-border">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-4 w-28 ml-auto" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-4 w-32" />
        </div>
      ))}
    </div>
  )

  // Error state
  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">주문 내역</h1>
        </div>
        <ErrorMessage
          title="주문 데이터 로딩 실패"
          message={error instanceof Error ? error.message : '주문 데이터를 불러오는 중 오류가 발생했습니다.'}
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
          <h1 className="text-2xl font-bold">주문 내역</h1>
          <p className="text-sm text-muted-foreground mt-1">
            거래 주문 내역을 확인하고 상태별로 필터링합니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RotateCcw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            대기 주문 동기화
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

      {/* Filter */}
      <div className="flex items-center justify-between">
        <OrderStatusFilter value={filterStatus} onChange={handleFilterChange} />
      </div>

      {/* Content */}
      <CommonCard noPadding className="overflow-hidden">
        {isLoading ? (
          <div className="p-4">
            {renderSkeleton()}
          </div>
        ) : orders.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={<FileText className="h-8 w-8 text-muted-foreground" />}
              title={filterStatus === 'all' ? '주문 내역 없음' : `${getStatusLabel(filterStatus)} 주문 없음`}
              description={
                filterStatus === 'all'
                  ? '아직 거래 주문 내역이 없습니다.'
                  : `${getStatusLabel(filterStatus)} 상태의 주문이 없습니다. 다른 필터를 시도해 보세요.`
              }
              action={
                filterStatus !== 'all' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange('all')}
                  >
                    전체 주문 보기
                  </Button>
                )
              }
            />
          </div>
        ) : (
          <OrderTable orders={orders} />
        )}
      </CommonCard>

      {/* Pagination */}
      {!isLoading && orders.length > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={total}
          pageSize={PAGE_SIZE}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  )
}

// Helper function to get Korean label for status
function getStatusLabel(status: OrderStatus): string {
  return ORDER_STATUS_LABELS[status]
}

export default OrdersView
