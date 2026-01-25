import { apiClient } from '@/core/api/client'

// ============================================================================
// Types
// ============================================================================

/** Config value type (can be string, number, or boolean) */
export type ConfigValue = string | number | boolean

/** Config item with source and metadata */
export interface ConfigItem {
  key: string
  value: ConfigValue
  source: 'db' | 'env' | 'default'
  updated_at: string | null
}

/** Config list response from backend (dictionary format) */
export interface ConfigListResponse {
  configs: Record<string, ConfigValue>
  count: number
}

/** Config batch update request */
export interface ConfigBatchUpdateRequest {
  configs: Record<string, ConfigValue>
}

/** Config batch update response */
export interface ConfigBatchUpdateResponse {
  updated: string[]
  failed: string[]
}

/** Trading status response */
export interface TradingStatusResponse {
  trading_enabled: boolean
  ticker: string
}

/** Risk parameters response */
export interface RiskParamsResponse {
  stop_loss_pct: number
  daily_loss_limit_pct: number
  volatility_threshold_pct: number
  position_size_min_pct: number
  position_size_max_pct: number
}

/** Overridable keys response */
export interface OverridableKeysResponse {
  keys: string[]
}

// ============================================================================
// Config Key Labels (Korean)
// ============================================================================

export const CONFIG_KEY_LABELS: Record<string, string> = {
  position_size_min_pct: '최소 포지션 크기 (%)',
  position_size_max_pct: '최대 포지션 크기 (%)',
  stop_loss_pct: '손절매 비율 (%)',
  daily_loss_limit_pct: '일일 손실 한도 (%)',
  signal_interval_minutes: 'AI 신호 주기 (분)',
  volatility_threshold_pct: '변동성 임계값 (%)',
  ai_model: 'AI 모델',
}

// ============================================================================
// Config Key Descriptions (Korean)
// ============================================================================

export const CONFIG_KEY_DESCRIPTIONS: Record<string, string> = {
  position_size_min_pct: '거래당 최소 투자 비율',
  position_size_max_pct: '거래당 최대 투자 비율',
  stop_loss_pct: '포지션 손절 기준 비율',
  daily_loss_limit_pct: '일일 최대 허용 손실 비율',
  signal_interval_minutes: 'AI 신호 생성 주기',
  volatility_threshold_pct: '거래 중단 변동성 임계값',
  ai_model: '사용할 AI 모델',
}

// ============================================================================
// Config Validation Rules
// ============================================================================

export const CONFIG_VALIDATION_RULES: Record<
  string,
  { min?: number; max?: number; step?: number }
> = {
  position_size_min_pct: { min: 0.1, max: 100, step: 0.1 },
  position_size_max_pct: { min: 0.1, max: 100, step: 0.1 },
  stop_loss_pct: { min: 0.1, max: 50, step: 0.1 },
  daily_loss_limit_pct: { min: 0.1, max: 50, step: 0.1 },
  signal_interval_minutes: { min: 1, max: 1440, step: 1 },
  volatility_threshold_pct: { min: 0.1, max: 100, step: 0.1 },
}

// ============================================================================
// AI Model Options
// ============================================================================

export const AI_MODEL_OPTIONS = [
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
  { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini (Fallback)' },
] as const

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch all configurations
 * Returns merged config values (DB values override env values)
 */
export async function fetchConfigs(): Promise<ConfigListResponse> {
  const response = await apiClient.get<ConfigListResponse>('/config')
  return response.data
}

/**
 * Fetch DB-stored configurations only
 */
export async function fetchDbConfigs(): Promise<ConfigListResponse> {
  const response = await apiClient.get<ConfigListResponse>('/config/db')
  return response.data
}

/**
 * Fetch overridable config keys
 */
export async function fetchOverridableKeys(): Promise<OverridableKeysResponse> {
  const response = await apiClient.get<OverridableKeysResponse>('/config/keys')
  return response.data
}

/**
 * Fetch trading status
 */
export async function fetchTradingStatus(): Promise<TradingStatusResponse> {
  const response = await apiClient.get<TradingStatusResponse>('/config/trading-status')
  return response.data
}

/**
 * Fetch risk parameters
 */
export async function fetchRiskParams(): Promise<RiskParamsResponse> {
  const response = await apiClient.get<RiskParamsResponse>('/config/risk-params')
  return response.data
}

/**
 * Fetch single configuration by key
 */
export async function fetchConfig(key: string): Promise<ConfigItem> {
  const response = await apiClient.get<ConfigItem>(`/config/${encodeURIComponent(key)}`)
  return response.data
}

/**
 * Update single configuration
 */
export async function updateConfig(key: string, value: ConfigValue): Promise<ConfigItem> {
  const response = await apiClient.patch<ConfigItem>(`/config/${encodeURIComponent(key)}`, { value })
  return response.data
}

/**
 * Batch update multiple configurations
 */
export async function batchUpdateConfigs(
  configs: Record<string, ConfigValue>
): Promise<ConfigBatchUpdateResponse> {
  const response = await apiClient.patch<ConfigBatchUpdateResponse>('/config', { configs })
  return response.data
}

/**
 * Delete configuration (reverts to env value)
 */
export async function deleteConfig(key: string): Promise<void> {
  await apiClient.delete(`/config/${encodeURIComponent(key)}`)
}

/**
 * Check if error is a 404 Not Found error
 */
function isNotFoundError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as { response?: { status?: number } }
    return axiosError.response?.status === 404
  }
  return false
}

/**
 * Reset all configurations to default values
 * This deletes all DB-stored configs, reverting to env values
 */
export async function resetAllConfigs(): Promise<ConfigBatchUpdateResponse> {
  // Get all overridable keys first
  const { keys } = await fetchOverridableKeys()

  // Delete each key to reset to env default
  const updated: string[] = []
  const failed: string[] = []

  for (const key of keys) {
    try {
      await deleteConfig(key)
      updated.push(key)
    } catch (error) {
      // 404 means key doesn't exist in DB, which is fine (already at default)
      if (isNotFoundError(error)) {
        updated.push(key)
      } else {
        failed.push(key)
      }
    }
  }

  return { updated, failed }
}

/**
 * Reset specific configurations to default values
 */
export async function resetConfigs(keys: string[]): Promise<ConfigBatchUpdateResponse> {
  const updated: string[] = []
  const failed: string[] = []

  for (const key of keys) {
    try {
      await deleteConfig(key)
      updated.push(key)
    } catch (error) {
      // 404 means key doesn't exist in DB, which is fine (already at default)
      if (isNotFoundError(error)) {
        updated.push(key)
      } else {
        failed.push(key)
      }
    }
  }

  return { updated, failed }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Extract currency symbol from ticker
 * @param ticker "KRW-SOL" -> "SOL"
 */
export function extractCurrencyFromTicker(ticker: string): string {
  const parts = ticker.split('-')
  return parts.length > 1 ? parts[1] : ticker
}

/**
 * Validate config value based on validation rules
 */
export function validateConfigValue(
  key: string,
  value: ConfigValue
): { valid: boolean; error?: string } {
  const rules = CONFIG_VALIDATION_RULES[key]
  if (!rules) return { valid: true }

  if (typeof value !== 'number') {
    return { valid: false, error: '숫자 값이 필요합니다' }
  }

  if (rules.min !== undefined && value < rules.min) {
    return { valid: false, error: `최소값: ${rules.min}` }
  }

  if (rules.max !== undefined && value > rules.max) {
    return { valid: false, error: `최대값: ${rules.max}` }
  }

  return { valid: true }
}
