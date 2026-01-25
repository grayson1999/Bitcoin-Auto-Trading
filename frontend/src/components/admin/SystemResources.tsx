import { CommonCard } from '@core/components/CommonCard'
import { Progress } from '@core/components/ui/progress'
import { formatNumber } from '@core/utils/formatters'
import { getUsageColor, getProgressColor } from '@core/utils/resourceColors'
import { Cpu, MemoryStick } from 'lucide-react'

interface SystemResourcesProps {
  cpuPercent: number
  memoryPercent: number
  memoryUsedMb: number
  memoryTotalMb: number
}

export function SystemResources({
  cpuPercent,
  memoryPercent,
  memoryUsedMb,
  memoryTotalMb,
}: SystemResourcesProps) {
  return (
    <CommonCard title="시스템 리소스">
      <div className="space-y-6">
        {/* CPU */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">CPU</span>
            </div>
            <span className={`text-lg font-bold ${getUsageColor(cpuPercent)}`}>
              {cpuPercent.toFixed(1)}%
            </span>
          </div>
          <div className="relative">
            <Progress value={cpuPercent} className="h-2" />
            <div
              className={`absolute top-0 left-0 h-2 rounded-full transition-all duration-300 ${getProgressColor(cpuPercent)}`}
              style={{ width: `${Math.min(cpuPercent, 100)}%` }}
            />
          </div>
        </div>

        {/* Memory */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MemoryStick className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">메모리</span>
            </div>
            <div className="text-right">
              <span className={`text-lg font-bold ${getUsageColor(memoryPercent)}`}>
                {memoryPercent.toFixed(1)}%
              </span>
              <span className="text-xs text-muted-foreground ml-2">
                {formatNumber(memoryUsedMb)} / {formatNumber(memoryTotalMb)} MB
              </span>
            </div>
          </div>
          <div className="relative">
            <Progress value={memoryPercent} className="h-2" />
            <div
              className={`absolute top-0 left-0 h-2 rounded-full transition-all duration-300 ${getProgressColor(memoryPercent)}`}
              style={{ width: `${Math.min(memoryPercent, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </CommonCard>
  )
}

export default SystemResources
