import { CommonCard } from '@core/components/CommonCard'
import { Progress } from '@core/components/ui/progress'
import { Alert, AlertDescription } from '@core/components/ui/alert'
import { getUsageColor, getProgressColor, USAGE_THRESHOLDS } from '@core/utils/resourceColors'
import { HardDrive, AlertTriangle } from 'lucide-react'

interface DiskUsageProps {
  diskPercent: number
  diskUsedGb: number
  diskTotalGb: number
}

export function DiskUsage({ diskPercent, diskUsedGb, diskTotalGb }: DiskUsageProps) {
  const showWarning = diskPercent >= USAGE_THRESHOLDS.WARNING

  return (
    <CommonCard
      title="디스크 사용량"
      headerAction={
        showWarning && (
          <AlertTriangle
            className={`w-5 h-5 ${diskPercent >= USAGE_THRESHOLDS.CRITICAL ? 'text-down' : 'text-neutral'}`}
          />
        )
      }
    >
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-background/50">
            <HardDrive className={`w-8 h-8 ${getUsageColor(diskPercent)}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-muted-foreground">사용 중</span>
              <span className={`text-lg font-bold ${getUsageColor(diskPercent)}`}>
                {diskPercent.toFixed(1)}%
              </span>
            </div>
            <div className="relative">
              <Progress value={diskPercent} className="h-3" />
              <div
                className={`absolute top-0 left-0 h-3 rounded-full transition-all duration-300 ${getProgressColor(diskPercent)}`}
                style={{ width: `${Math.min(diskPercent, 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>{diskUsedGb.toFixed(1)} GB 사용</span>
              <span>{diskTotalGb.toFixed(1)} GB 전체</span>
            </div>
          </div>
        </div>

        {showWarning && (
          <Alert
            variant="destructive"
            className={
              diskPercent >= USAGE_THRESHOLDS.CRITICAL
                ? 'bg-down/10 border-down/30 text-down'
                : 'bg-neutral/10 border-neutral/30 text-neutral'
            }
          >
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {diskPercent >= USAGE_THRESHOLDS.CRITICAL
                ? '디스크 공간이 거의 다 찼습니다. 즉시 정리가 필요합니다.'
                : '디스크 사용량이 70%를 초과했습니다. 공간 확보를 권장합니다.'}
            </AlertDescription>
          </Alert>
        )}
      </div>
    </CommonCard>
  )
}

export default DiskUsage
