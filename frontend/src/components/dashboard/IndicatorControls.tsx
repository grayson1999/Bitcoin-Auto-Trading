import { HelpCircle } from 'lucide-react'
import { Switch } from '@/core/components/ui/switch'
import { Label } from '@/core/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/core/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/core/components/ui/tooltip'
import type { ChartInterval, ChartSettings } from '@/core/types'
import { cn } from '@/core/utils/cn'

interface IndicatorControlsProps {
  settings: ChartSettings
  onSettingsChange: (settings: ChartSettings) => void
  className?: string
}

const INTERVAL_OPTIONS: { value: ChartInterval; label: string }[] = [
  { value: '1m', label: '1분' },
  { value: '5m', label: '5분' },
  { value: '15m', label: '15분' },
  { value: '1h', label: '1시간' },
]

export function IndicatorControls({
  settings,
  onSettingsChange,
  className,
}: IndicatorControlsProps) {
  const handleIntervalChange = (value: string) => {
    onSettingsChange({
      ...settings,
      interval: value as ChartInterval,
    })
  }

  const handleToggle = (key: keyof ChartSettings) => {
    if (key === 'interval') return
    onSettingsChange({
      ...settings,
      [key]: !settings[key],
    })
  }

  return (
    <div className={cn('flex flex-wrap items-center gap-4', className)}>
      {/* Interval Selector */}
      <div className="flex items-center gap-2">
        <Label htmlFor="interval" className="text-sm text-gray-400">
          간격
        </Label>
        <Select value={settings.interval} onValueChange={handleIntervalChange}>
          <SelectTrigger id="interval" className="w-24 h-8 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {INTERVAL_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="h-6 w-px bg-gray-700" />

      {/* MA Toggles */}
      <TooltipProvider delayDuration={200}>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Switch
              id="ma20"
              checked={settings.showMA20}
              onCheckedChange={() => handleToggle('showMA20')}
              size="small"
            />
            <Label
              htmlFor="ma20"
              className="text-xs cursor-pointer"
              style={{ color: '#f59e0b' }}
            >
              MA20
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-gray-500 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">20일 이동평균선</p>
                <p className="text-xs text-gray-400">최근 20개 캔들의 평균 가격</p>
                <p className="text-xs text-gray-400">단기 추세 파악에 사용</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-1.5">
            <Switch
              id="ma50"
              checked={settings.showMA50}
              onCheckedChange={() => handleToggle('showMA50')}
              size="small"
            />
            <Label
              htmlFor="ma50"
              className="text-xs cursor-pointer"
              style={{ color: '#3b82f6' }}
            >
              MA50
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-gray-500 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">50일 이동평균선</p>
                <p className="text-xs text-gray-400">최근 50개 캔들의 평균 가격</p>
                <p className="text-xs text-gray-400">중기 추세 파악에 사용</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-1.5">
            <Switch
              id="ma200"
              checked={settings.showMA200}
              onCheckedChange={() => handleToggle('showMA200')}
              size="small"
            />
            <Label
              htmlFor="ma200"
              className="text-xs cursor-pointer"
              style={{ color: '#ef4444' }}
            >
              MA200
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-gray-500 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">200일 이동평균선</p>
                <p className="text-xs text-gray-400">최근 200개 캔들의 평균 가격</p>
                <p className="text-xs text-gray-400">장기 추세 및 지지/저항선으로 사용</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </TooltipProvider>

      <div className="h-6 w-px bg-gray-700" />

      {/* Oscillator Toggles */}
      <TooltipProvider delayDuration={200}>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Switch
              id="rsi"
              checked={settings.showRSI}
              onCheckedChange={() => handleToggle('showRSI')}
              size="small"
            />
            <Label
              htmlFor="rsi"
              className="text-xs cursor-pointer"
              style={{ color: '#8b5cf6' }}
            >
              RSI
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-gray-500 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">상대강도지수 (RSI)</p>
                <p className="text-xs text-gray-400">0~100 범위의 모멘텀 지표</p>
                <p className="text-xs text-gray-400">70 이상: 과매수, 30 이하: 과매도</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-1.5">
            <Switch
              id="macd"
              checked={settings.showMACD}
              onCheckedChange={() => handleToggle('showMACD')}
              size="small"
            />
            <Label htmlFor="macd" className="text-xs text-gray-300 cursor-pointer">
              MACD
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-gray-500 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">이동평균수렴확산 (MACD)</p>
                <p className="text-xs text-gray-400">단기(12) - 장기(26) EMA 차이</p>
                <p className="text-xs text-gray-400">신호선(9) 교차로 매매 타이밍 파악</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </TooltipProvider>
    </div>
  )
}

export default IndicatorControls
