import type { SystemMetrics, SchedulerJob } from '@core/types'

/**
 * Generate mock scheduler jobs with realistic status
 */
function generateMockSchedulerJobs(): SchedulerJob[] {
  const now = new Date()
  const oneMinuteAgo = new Date(now.getTime() - 60 * 1000)
  const tenSecondsFromNow = new Date(now.getTime() + 10 * 1000)
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
  const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000)

  return [
    {
      name: 'data_collection',
      status: 'running',
      last_run: oneMinuteAgo.toISOString(),
      next_run: tenSecondsFromNow.toISOString(),
    },
    {
      name: 'signal_generation',
      status: 'running',
      last_run: oneHourAgo.toISOString(),
      next_run: oneHourFromNow.toISOString(),
    },
    {
      name: 'order_sync',
      status: 'running',
      last_run: oneMinuteAgo.toISOString(),
      next_run: new Date(now.getTime() + 30 * 1000).toISOString(),
    },
    {
      name: 'position_update',
      status: 'running',
      last_run: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
      next_run: new Date(now.getTime() + 5 * 60 * 1000).toISOString(),
    },
    {
      name: 'risk_check',
      status: 'running',
      last_run: new Date(now.getTime() - 10 * 1000).toISOString(),
      next_run: new Date(now.getTime() + 20 * 1000).toISOString(),
    },
  ]
}

/**
 * Generate mock system metrics with realistic values
 * Simulates slight variations on each call for realistic behavior
 */
export function mockSystemMetrics(): SystemMetrics {
  const baselineCpu = 25
  const baselineMemory = 45
  const baselineDisk = 65

  // Add small random variations
  const cpuVariation = (Math.random() - 0.5) * 10
  const memoryVariation = (Math.random() - 0.5) * 5

  return {
    cpu_percent: Math.max(5, Math.min(95, baselineCpu + cpuVariation)),
    memory_percent: Math.max(20, Math.min(90, baselineMemory + memoryVariation)),
    memory_used_mb: 1024 + Math.floor(Math.random() * 200),
    memory_total_mb: 2048,
    disk_percent: baselineDisk + Math.random() * 2,
    disk_used_gb: 32.5 + Math.random() * 0.5,
    disk_total_gb: 50.0,
    scheduler_jobs: generateMockSchedulerJobs(),
  }
}
