import { useState, useEffect } from 'react'
import { Input } from '@/core/components/ui/input'
import { Label } from '@/core/components/ui/label'
import { Skeleton } from '@/core/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/core/components/ui/select'
import { SettingsSection } from './SettingsSection'
import {
  type ConfigValue,
  CONFIG_KEY_LABELS,
  CONFIG_KEY_DESCRIPTIONS,
  CONFIG_VALIDATION_RULES,
  AI_MODEL_OPTIONS,
  validateConfigValue,
} from '@/api/config.api'
import { cn } from '@/core/utils'
import { Bot, Clock } from 'lucide-react'

// Signal interval preset options (in minutes)
const SIGNAL_INTERVAL_PRESETS = [
  { value: 15, label: '15분' },
  { value: 30, label: '30분' },
  { value: 60, label: '1시간' },
  { value: 120, label: '2시간' },
  { value: 240, label: '4시간' },
] as const

interface AISettingsFormProps {
  configs: Record<string, ConfigValue>
  isLoading?: boolean
  onConfigChange: (key: string, value: ConfigValue) => void
  errors?: Record<string, string>
}

export function AISettingsForm({
  configs,
  isLoading,
  onConfigChange,
  errors = {},
}: AISettingsFormProps) {
  // Local state for form values
  const [aiModel, setAiModel] = useState<string>('')
  const [signalInterval, setSignalInterval] = useState<number>(60)

  // Sync local values with props
  useEffect(() => {
    if (typeof configs.ai_model === 'string') {
      setAiModel(configs.ai_model)
    }
    if (typeof configs.signal_interval_minutes === 'number') {
      setSignalInterval(configs.signal_interval_minutes)
    } else if (typeof configs.signal_interval_minutes === 'string') {
      setSignalInterval(parseInt(configs.signal_interval_minutes) || 60)
    }
  }, [configs])

  const handleModelChange = (value: string) => {
    setAiModel(value)
    onConfigChange('ai_model', value)
  }

  const handleIntervalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value)
    if (!isNaN(value)) {
      setSignalInterval(value)
      const validation = validateConfigValue('signal_interval_minutes', value)
      if (validation.valid) {
        onConfigChange('signal_interval_minutes', value)
      }
    }
  }

  if (isLoading) {
    return (
      <SettingsSection title="AI 설정" description="AI 모델 및 신호 생성 설정">
        <div className="space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="space-y-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>
      </SettingsSection>
    )
  }

  const rules = CONFIG_VALIDATION_RULES.signal_interval_minutes || {}

  return (
    <SettingsSection title="AI 설정" description="AI 모델 및 신호 생성 설정">
      <div className="space-y-6">
        {/* AI Model Selection */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-gray-400" />
            <Label htmlFor="ai_model" className="text-sm font-medium text-gray-200">
              {CONFIG_KEY_LABELS.ai_model}
            </Label>
          </div>
          <p className="text-xs text-gray-400">{CONFIG_KEY_DESCRIPTIONS.ai_model}</p>
          <Select value={aiModel} onValueChange={handleModelChange}>
            <SelectTrigger
              id="ai_model"
              className={cn(
                'bg-gray-800/50 border-gray-700',
                errors.ai_model && 'border-red-500'
              )}
            >
              <SelectValue placeholder="모델 선택" />
            </SelectTrigger>
            <SelectContent>
              {AI_MODEL_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.ai_model && <p className="text-xs text-red-400">{errors.ai_model}</p>}
        </div>

        {/* Signal Interval */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-400" />
            <Label htmlFor="signal_interval" className="text-sm font-medium text-gray-200">
              {CONFIG_KEY_LABELS.signal_interval_minutes}
            </Label>
          </div>
          <p className="text-xs text-gray-400">
            {CONFIG_KEY_DESCRIPTIONS.signal_interval_minutes}
          </p>
          <div className="flex items-center gap-2">
            <Input
              id="signal_interval"
              type="number"
              value={signalInterval}
              onChange={handleIntervalChange}
              min={rules.min || 1}
              max={rules.max || 1440}
              step={rules.step || 1}
              className={cn(
                'w-32 bg-gray-800/50 border-gray-700',
                errors.signal_interval_minutes && 'border-red-500 focus:ring-red-500'
              )}
            />
            <span className="text-sm text-gray-400">분</span>
          </div>
          {errors.signal_interval_minutes && (
            <p className="text-xs text-red-400">{errors.signal_interval_minutes}</p>
          )}

          {/* Interval Preview */}
          <div className="flex flex-wrap gap-2 mt-2">
            {SIGNAL_INTERVAL_PRESETS.map((preset) => (
              <button
                key={preset.value}
                type="button"
                onClick={() => {
                  setSignalInterval(preset.value)
                  onConfigChange('signal_interval_minutes', preset.value)
                }}
                className={cn(
                  'px-3 py-1 text-xs rounded-full transition-colors',
                  signalInterval === preset.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </SettingsSection>
  )
}
