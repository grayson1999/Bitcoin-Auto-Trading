import { CommonCard } from '@core/components/CommonCard'
import { Badge } from '@core/components/ui/badge'
import type { ComponentHealth } from '@core/types'
import { Database, CheckCircle, XCircle, Clock } from 'lucide-react'

interface DatabaseStatusProps {
  health: ComponentHealth
}

export function DatabaseStatus({ health }: DatabaseStatusProps) {
  const isHealthy = health.status === 'healthy'

  return (
    <CommonCard
      title="데이터베이스"
      headerAction={
        <Badge
          variant="outline"
          className={isHealthy ? 'bg-up/10 text-up border-up/30' : 'bg-down/10 text-down border-down/30'}
        >
          {isHealthy ? (
            <>
              <CheckCircle className="w-3 h-3 mr-1" />
              정상
            </>
          ) : (
            <>
              <XCircle className="w-3 h-3 mr-1" />
              오류
            </>
          )}
        </Badge>
      }
    >
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-lg bg-background/50">
          <Database className={`w-8 h-8 ${isHealthy ? 'text-up' : 'text-down'}`} />
        </div>
        <div className="flex-1">
          <div className="text-sm text-muted-foreground">PostgreSQL</div>
          {health.latency_ms !== undefined && (
            <div className="flex items-center gap-1 text-sm">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="font-medium">{health.latency_ms.toFixed(0)}ms</span>
              <span className="text-muted-foreground">응답 시간</span>
            </div>
          )}
          {health.message && (
            <div className="text-xs text-muted-foreground mt-1">{health.message}</div>
          )}
        </div>
      </div>
    </CommonCard>
  )
}

export default DatabaseStatus
