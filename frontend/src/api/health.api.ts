import apiClient from '@core/api/client'
import type { HealthDetail, ComponentHealth } from '@core/types'

/** Raw API response with components as array */
interface HealthDetailRaw {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  components: Array<{
    name: string
    status: 'healthy' | 'unhealthy'
    latency_ms: number | null
    message: string | null
  }>
}

/**
 * Fetch simple health status
 */
export async function getHealthStatus(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>('/health')
  return response.data
}

/**
 * Fetch detailed health status including all components
 * Transforms array response to object format expected by frontend
 */
export async function getHealthDetail(): Promise<HealthDetail> {
  const response = await apiClient.get<HealthDetailRaw>('/health/detail')

  // Transform array to object
  const componentsObj = response.data.components.reduce(
    (acc, comp) => {
      acc[comp.name] = {
        status: comp.status,
        latency_ms: comp.latency_ms ?? undefined,
        message: comp.message ?? undefined,
      }
      return acc
    },
    {} as Record<string, ComponentHealth>
  )

  return {
    status: response.data.status,
    timestamp: response.data.timestamp,
    version: response.data.version,
    components: componentsObj as HealthDetail['components'],
  }
}
