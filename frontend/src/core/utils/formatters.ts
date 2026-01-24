/** Format number as Korean Won currency */
export function formatCurrency(value: number | null | undefined, options?: { showSign?: boolean }): string {
  // Null/undefined/NaN safety check
  if (value == null || isNaN(value)) {
    return '-'
  }

  const formatted = new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(Math.abs(value))

  if (options?.showSign && value !== 0) {
    return value > 0 ? `+${formatted}` : `-${formatted.replace('₩', '₩')}`
  }

  return value < 0 ? `-${formatted}` : formatted
}

/** Format number with commas */
export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/** Format BTC amount */
export function formatBTC(value: number): string {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: 8,
    maximumFractionDigits: 8,
  }).format(value)
}

/** Format percentage */
export function formatPercent(value: number, options?: { showSign?: boolean; decimals?: number }): string {
  const decimals = options?.decimals ?? 2
  const formatted = `${Math.abs(value).toFixed(decimals)}%`

  if (options?.showSign && value !== 0) {
    return value > 0 ? `+${formatted}` : `-${formatted}`
  }

  return value < 0 ? `-${formatted}` : formatted
}

/** Format date as YYYY-MM-DD */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).replace(/\. /g, '-').replace('.', '')
}

/** Format date and time */
export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/** Format time only */
export function formatTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/** Format relative time (e.g., "3분 전") */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return '방금 전'
  if (diffMin < 60) return `${diffMin}분 전`
  if (diffHour < 24) return `${diffHour}시간 전`
  if (diffDay < 7) return `${diffDay}일 전`

  return formatDate(d)
}

/** Format bytes to human readable size */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}
