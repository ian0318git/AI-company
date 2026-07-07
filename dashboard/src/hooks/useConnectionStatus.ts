import { useState, useEffect, useCallback } from 'react'

type ConnectionState = 'connecting' | 'connected' | 'disconnected'

export function useConnectionStatus(pollInterval = 15_000) {
  const [state, setState] = useState<ConnectionState>('connecting')

  const check = useCallback(async () => {
    try {
      const res = await fetch('/status')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setState(data.api === 'running' ? 'connected' : 'disconnected')
    } catch {
      setState('disconnected')
    }
  }, [])

  useEffect(() => {
    check()
    const id = setInterval(check, pollInterval)
    return () => clearInterval(id)
  }, [check, pollInterval])

  return state
}
