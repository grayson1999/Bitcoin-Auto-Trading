import { useState, useEffect } from 'react'
import { Input } from '@/core/components/ui/input'
import { Label } from '@/core/components/ui/label'
import { Slider } from '@/core/components/ui/slider'
import { Skeleton } from '@/core/components/ui/skeleton'
import { SettingsSection } from './SettingsSection'
import {
  type ConfigValue,
  CONFIG_KEY_LABELS,
  CONFIG_KEY_DESCRIPTIONS,
  CONFIG_VALIDATION_RULES,
  validateConfigValue,
} from '@/api/config.api'
import { cn } from '@/core/utils'

// Trading-related config keys (defined outside component for stable reference)
const TRADING_CONFIG_KEYS = [
  'position_size_min_pct',
  'position_size_max_pct',
  'stop_loss_pct',
  'daily_loss_limit_pct',
  'volatility_threshold_pct',
] as const

interface TradingSettingsFormProps {
  configs: Record<string, ConfigValue>
  isLoading?: boolean
  onConfigChange: (key: string, value: ConfigValue) => void
  errors?: Record<string, string>
}

interface SettingFieldProps {
  configKey: string
  value: number
  onChange: (value: number) => void
  error?: string
  disabled?: boolean
}

function SettingField({ configKey, value, onChange, error, disabled }: SettingFieldProps) {
  const rules = CONFIG_VALIDATION_RULES[configKey] || {}
  const label = CONFIG_KEY_LABELS[configKey] || configKey
  const description = CONFIG_KEY_DESCRIPTIONS[configKey]

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value)
    if (!isNaN(newValue)) {
      onChange(newValue)
    }
  }

  const handleSliderChange = (values: number[]) => {
    onChange(values[0])
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor={configKey} className="text-sm font-medium text-gray-200">
            {label}
          </Label>
          {description && (
            <p className="text-xs text-gray-400 mt-0.5">{description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Input
            id={configKey}
            type="number"
            value={value}
            onChange={handleInputChange}
            min={rules.min}
            max={rules.max}
            step={rules.step || 0.1}
            disabled={disabled}
            className={cn(
              'w-24 text-right bg-gray-800/50 border-gray-700',
              error && 'border-red-500 focus:ring-red-500'
            )}
          />
        </div>
      </div>
      <Slider
        value={[value]}
        onValueChange={handleSliderChange}
        min={rules.min || 0}
        max={rules.max || 100}
        step={rules.step || 0.1}
        disabled={disabled}
        className="w-full"
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

export function TradingSettingsForm({
  configs,
  isLoading,
  onConfigChange,
  errors = {},
}: TradingSettingsFormProps) {
  // Local state for form values
  const [localValues, setLocalValues] = useState<Record<string, number>>({})

  // Sync local values with props
  useEffect(() => {
    const newValues: Record<string, number> = {}
    for (const key of TRADING_CONFIG_KEYS) {
      const value = configs[key]
      if (typeof value === 'number') {
        newValues[key] = value
      } else if (typeof value === 'string') {
        newValues[key] = parseFloat(value) || 0
      } else {
        newValues[key] = 0
      }
    }
    setLocalValues(newValues)
  }, [configs])

  const handleValueChange = (key: string, value: number) => {
    setLocalValues((prev) => ({ ...prev, [key]: value }))

    // Validate and propagate change
    const validation = validateConfigValue(key, value)
    if (validation.valid) {
      onConfigChange(key, value)
    }
  }

  if (isLoading) {
    return (
      <SettingsSection title="거래 설정" description="거래 파라미터를 설정합니다">
        <div className="space-y-6">
          {TRADING_CONFIG_KEYS.map((key) => (
            <div key={key} className="space-y-3">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-2 w-full" />
            </div>
          ))}
        </div>
      </SettingsSection>
    )
  }

  return (
    <SettingsSection title="거래 설정" description="거래 파라미터를 설정합니다">
      <div className="space-y-6">
        {/* Position Size Section */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-300 border-b border-gray-700 pb-2">
            포지션 크기
          </h4>
          <SettingField
            configKey="position_size_min_pct"
            value={localValues.position_size_min_pct || 0}
            onChange={(v) => handleValueChange('position_size_min_pct', v)}
            error={errors.position_size_min_pct}
          />
          <SettingField
            configKey="position_size_max_pct"
            value={localValues.position_size_max_pct || 0}
            onChange={(v) => handleValueChange('position_size_max_pct', v)}
            error={errors.position_size_max_pct}
          />
        </div>

        {/* Risk Management Section */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-300 border-b border-gray-700 pb-2">
            리스크 관리
          </h4>
          <SettingField
            configKey="stop_loss_pct"
            value={localValues.stop_loss_pct || 0}
            onChange={(v) => handleValueChange('stop_loss_pct', v)}
            error={errors.stop_loss_pct}
          />
          <SettingField
            configKey="daily_loss_limit_pct"
            value={localValues.daily_loss_limit_pct || 0}
            onChange={(v) => handleValueChange('daily_loss_limit_pct', v)}
            error={errors.daily_loss_limit_pct}
          />
          <SettingField
            configKey="volatility_threshold_pct"
            value={localValues.volatility_threshold_pct || 0}
            onChange={(v) => handleValueChange('volatility_threshold_pct', v)}
            error={errors.volatility_threshold_pct}
          />
        </div>
      </div>
    </SettingsSection>
  )
}
