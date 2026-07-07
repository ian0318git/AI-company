import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

export interface TaskMetrics {
  total_tasks_tracked: number
  today_minutes: number
  completed_count: number
  average_completion_minutes: number | null
  active_count: number
  slow_count: number
  slow_tasks: { id: string; title: string; elapsed_minutes: number }[]
  active_tasks: { id: string; title: string; elapsed_minutes: number; is_slow: boolean }[]
  agent_breakdown: { agent: string; minutes: number }[]
  status_counts: Record<string, number>
}

export function useTaskMetrics(pollInterval = 60_000) {
  const [metrics, setMetrics] = useState<TaskMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    try {
      const data = await api.tasks.metrics()
      setMetrics(data)
    } catch (e) {
      console.warn('[useTaskMetrics]', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    if (pollInterval > 0) {
      const id = setInterval(fetch, pollInterval)
      return () => clearInterval(id)
    }
  }, [fetch, pollInterval])

  return { metrics, loading, refresh: fetch }
}
