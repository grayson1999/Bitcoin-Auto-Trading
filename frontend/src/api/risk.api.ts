import { apiClient } from '@/core/api/client'
import type { RiskStatus, RiskEvent, PaginatedResponse } from '@/core/types'

interface RiskEventParams {
  page?: number
  limit?: number
  severity?: 'low' | 'medium' | 'high' | 'critical'
}

/** Fetch current risk status */
export async function fetchRiskStatus(): Promise<RiskStatus> {
  const response = await apiClient.get<RiskStatus>('/risk/status')
  return response.data
}

/** Fetch risk events with pagination */
export async function fetchRiskEvents(
  params: RiskEventParams = {}
): Promise<PaginatedResponse<RiskEvent>> {
  const { page = 1, limit = 20, severity } = params
  const response = await apiClient.get<PaginatedResponse<RiskEvent>>('/risk/events', {
    params: {
      page,
      limit,
      severity,
    },
  })
  return response.data
}

/** Halt trading */
export async function haltTrading(reason: string): Promise<{ success: boolean }> {
  const response = await apiClient.post('/risk/halt', { reason })
  return response.data
}

/** Resume trading */
export async function resumeTrading(): Promise<{ success: boolean }> {
  const response = await apiClient.post('/risk/resume')
  return response.data
}
