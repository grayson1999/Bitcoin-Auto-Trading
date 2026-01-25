import { CommonCard } from '@core/components/CommonCard'
import { Badge } from '@core/components/ui/badge'
import type { HealthDetail } from '@core/types'
import { formatDateTime } from '@core/utils/formatters'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Database,
  Cloud,
  Brain,
  Clock,
  Zap,
  ShoppingCart,
} from 'lucide-react'

interface SystemHealthOverviewProps {
  health: HealthDetail
}

function getStatusIcon(status: 'healthy' | 'unhealthy') {
  return status === 'healthy' ? (
    <CheckCircle className="w-4 h-4 text-up" />
  ) : (
    <XCircle className="w-4 h-4 text-down" />
  )
}

function getOverallStatusBadge(status: HealthDetail['status']) {
  switch (status) {
    case 'healthy':
      return (
        <Badge variant="outline" className="bg-up/10 text-up border-up/30">
          <CheckCircle className="w-3 h-3 mr-1" />
          정상
        </Badge>
      )
    case 'degraded':
      return (
        <Badge variant="outline" className="bg-neutral/10 text-neutral border-neutral/30">
          <AlertTriangle className="w-3 h-3 mr-1" />
          일부 저하
        </Badge>
      )
    case 'unhealthy':
      return (
        <Badge variant="outline" className="bg-down/10 text-down border-down/30">
          <XCircle className="w-3 h-3 mr-1" />
          비정상
        </Badge>
      )
    default:
      return null
  }
}

const componentConfig = [
  { key: 'database', label: '데이터베이스', icon: Database },
  { key: 'upbit_api', label: 'Upbit API', icon: Cloud },
  { key: 'gemini_api', label: 'Gemini AI', icon: Brain },
  { key: 'scheduler', label: '스케줄러', icon: Clock },
  { key: 'recent_signal', label: '최근 신호', icon: Zap },
  { key: 'recent_order', label: '최근 주문', icon: ShoppingCart },
] as const

export function SystemHealthOverview({ health }: SystemHealthOverviewProps) {
  const healthyCount = Object.values(health.components).filter(
    (c) => c.status === 'healthy'
  ).length
  const totalCount = Object.keys(health.components).length

  return (
    <CommonCard
      title="시스템 상태"
      description={`${healthyCount}/${totalCount} 구성요소 정상`}
      headerAction={getOverallStatusBadge(health.status)}
    >
      <div className="space-y-4">
        {/* Version and timestamp */}
        <div className="flex items-center justify-between text-sm text-muted-foreground pb-2 border-b border-border">
          <span>버전: {health.version}</span>
          <span>업데이트: {formatDateTime(health.timestamp)}</span>
        </div>

        {/* Components grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {componentConfig.map(({ key, label, icon: Icon }) => {
            const component = health.components[key as keyof typeof health.components]
            const isHealthy = component.status === 'healthy'

            return (
              <div
                key={key}
                className={`flex items-center gap-2 p-3 rounded-lg border ${
                  isHealthy ? 'bg-up/5 border-up/20' : 'bg-down/5 border-down/20'
                }`}
              >
                <Icon className={`w-4 h-4 ${isHealthy ? 'text-up' : 'text-down'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="text-sm font-medium truncate">{label}</span>
                    {getStatusIcon(component.status)}
                  </div>
                  {component.latency_ms !== undefined && (
                    <span className="text-xs text-muted-foreground">
                      {component.latency_ms.toFixed(0)}ms
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </CommonCard>
  )
}

export default SystemHealthOverview
