/** Threshold constants for resource usage */
export const USAGE_THRESHOLDS = {
  WARNING: 70,
  CRITICAL: 90,
} as const

/**
 * Get text color class based on usage percentage
 * @param percent - Usage percentage (0-100)
 * @returns Tailwind text color class
 */
export function getUsageColor(percent: number): string {
  if (percent >= USAGE_THRESHOLDS.CRITICAL) return 'text-down'
  if (percent >= USAGE_THRESHOLDS.WARNING) return 'text-neutral'
  return 'text-up'
}

/**
 * Get progress bar color class based on usage percentage
 * @param percent - Usage percentage (0-100)
 * @returns Tailwind background color class
 */
export function getProgressColor(percent: number): string {
  if (percent >= USAGE_THRESHOLDS.CRITICAL) return 'bg-down'
  if (percent >= USAGE_THRESHOLDS.WARNING) return 'bg-neutral'
  return 'bg-up'
}
