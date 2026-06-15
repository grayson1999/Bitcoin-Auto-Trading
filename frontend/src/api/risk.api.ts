import { apiClient } from '@/core/api/client'
import type { RiskStatus, RiskEventListResponse } from '@/core/types'

/** Fetch current risk status */
export async function fetchRiskStatus(): Promise<RiskStatus> {
  const response = await apiClient.get<RiskStatus>('/risk/status')
  return response.data
}

/** Fetch risk events */
export async function fetchRiskEvents(
  params: { limit?: number; event_type?: string } = {}
): Promise<RiskEventListResponse> {
  const response = await apiClient.get<RiskEventListResponse>('/risk/events', { params })
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
