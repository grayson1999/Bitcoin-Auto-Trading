import { Switch } from '@/core/components/ui/switch'
import { Label } from '@/core/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/core/components/ui/select'
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
        </div>
      </div>

      <div className="h-6 w-px bg-gray-700" />

      {/* Oscillator Toggles */}
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
        </div>
      </div>
    </div>
  )
}

export default IndicatorControls
