import { CommonCard } from '@core/components/CommonCard'
import { Badge } from '@core/components/ui/badge'
import { formatRelativeTime } from '@core/utils/formatters'
import type { SchedulerJob } from '@core/types'
import { Clock, PlayCircle, AlertCircle, StopCircle } from 'lucide-react'

interface SchedulerStatusProps {
  jobs: SchedulerJob[]
}

function getStatusBadge(status: SchedulerJob['status']) {
  switch (status) {
    case 'running':
      return (
        <Badge variant="outline" className="bg-up/10 text-up border-up/30">
          <PlayCircle className="w-3 h-3 mr-1" />
          실행 중
        </Badge>
      )
    case 'stopped':
      return (
        <Badge variant="outline" className="bg-neutral/10 text-neutral border-neutral/30">
          <StopCircle className="w-3 h-3 mr-1" />
          중지됨
        </Badge>
      )
    case 'error':
      return (
        <Badge variant="outline" className="bg-down/10 text-down border-down/30">
          <AlertCircle className="w-3 h-3 mr-1" />
          오류
        </Badge>
      )
    default:
      return null
  }
}

function getJobDisplayName(name: string): string {
  const names: Record<string, string> = {
    data_collection: '시세 수집',
    signal_generation: 'AI 신호 생성',
    order_sync: '주문 동기화',
    position_update: '포지션 업데이트',
    risk_check: '리스크 체크',
  }
  return names[name] || name
}

export function SchedulerStatus({ jobs }: SchedulerStatusProps) {
  const runningCount = jobs.filter((j) => j.status === 'running').length
  const errorCount = jobs.filter((j) => j.status === 'error').length

  return (
    <CommonCard
      title="스케줄러 상태"
      description={`${jobs.length}개 작업 중 ${runningCount}개 실행 중`}
      headerAction={
        errorCount > 0 && (
          <Badge variant="destructive" className="bg-down text-white">
            {errorCount}개 오류
          </Badge>
        )
      }
    >
      <div className="space-y-3">
        {jobs.map((job) => (
          <div
            key={job.name}
            className="flex items-center justify-between p-3 rounded-lg bg-background/50 border border-border"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{getJobDisplayName(job.name)}</span>
                {getStatusBadge(job.status)}
              </div>
              <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                {job.last_run && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    마지막 실행: {formatRelativeTime(job.last_run)}
                  </span>
                )}
                {job.next_run && (
                  <span className="flex items-center gap-1">
                    다음 실행: {formatRelativeTime(job.next_run)}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}

        {jobs.length === 0 && (
          <div className="text-center text-muted-foreground py-4">스케줄러 작업 없음</div>
        )}
      </div>
    </CommonCard>
  )
}

export default SchedulerStatus
