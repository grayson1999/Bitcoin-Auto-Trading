import { useQuery } from '@tanstack/react-query'
import { RefreshCw, AlertCircle, Shield } from 'lucide-react'
import { getSystemMetrics } from '@/api/admin.api'
import { getHealthDetail } from '@/api/health.api'
import { CommonButton } from '@/core/components/CommonButton'
import { Skeleton } from '@/core/components/ui/skeleton'
import { SchedulerStatus } from '@/components/admin/SchedulerStatus'
import { DatabaseStatus } from '@/components/admin/DatabaseStatus'
import { SystemResources } from '@/components/admin/SystemResources'
import { DiskUsage } from '@/components/admin/DiskUsage'
import { SystemHealthOverview } from '@/components/admin/SystemHealthOverview'

function AdminViewSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>

      {/* System Health skeleton */}
      <Skeleton className="h-64 w-full rounded-lg" />

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Skeleton className="h-48 rounded-lg" />
        <Skeleton className="h-48 rounded-lg" />
      </div>

      {/* Scheduler skeleton */}
      <Skeleton className="h-80 w-full rounded-lg" />
    </div>
  )
}

export function AdminView() {
  // System metrics query with 10s auto-refresh
  const {
    data: metrics,
    isLoading: isMetricsLoading,
    isError: isMetricsError,
    error: metricsError,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ['systemMetrics'],
    queryFn: getSystemMetrics,
    refetchInterval: 10000, // 10 seconds
    staleTime: 9000,
  })

  // Health detail query with 10s auto-refresh
  const {
    data: health,
    isLoading: isHealthLoading,
    isError: isHealthError,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['healthDetail'],
    queryFn: getHealthDetail,
    refetchInterval: 10000, // 10 seconds
    staleTime: 9000,
  })

  const isLoading = isMetricsLoading || isHealthLoading
  const isError = isMetricsError || isHealthError
  const error = metricsError || healthError

  const handleRefresh = () => {
    refetchMetrics()
    refetchHealth()
  }

  // Loading state
  if (isLoading && !metrics && !health) {
    return <AdminViewSkeleton />
  }

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">
          시스템 정보를 불러올 수 없습니다
        </h2>
        <p className="text-gray-400 mb-4">
          {error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다'}
        </p>
        <CommonButton onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          다시 시도
        </CommonButton>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-accent" />
            <h1 className="text-2xl font-bold text-white">관리자 대시보드</h1>
          </div>
          <p className="text-sm text-gray-400 mt-1">서버 상태 및 시스템 모니터링</p>
        </div>
        <CommonButton
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          새로고침
        </CommonButton>
      </div>

      {/* System Health Overview */}
      {health && <SystemHealthOverview health={health} />}

      {/* Resources Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* System Resources (CPU, Memory) */}
        {metrics && (
          <SystemResources
            cpuPercent={metrics.cpu_percent}
            memoryPercent={metrics.memory_percent}
            memoryUsedMb={metrics.memory_used_mb}
            memoryTotalMb={metrics.memory_total_mb}
          />
        )}

        {/* Disk Usage */}
        {metrics && (
          <DiskUsage
            diskPercent={metrics.disk_percent}
            diskUsedGb={metrics.disk_used_gb}
            diskTotalGb={metrics.disk_total_gb}
          />
        )}
      </div>

      {/* Database Status */}
      {health && <DatabaseStatus health={health.components.database} />}

      {/* Scheduler Status */}
      {metrics && <SchedulerStatus jobs={metrics.scheduler_jobs} />}
    </div>
  )
}

export default AdminView
