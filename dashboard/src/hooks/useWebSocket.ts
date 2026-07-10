import { useState, useEffect, useRef, useCallback } from 'react'

type ConnectionState = 'connecting' | 'connected' | 'disconnected'

export interface AgentTelemetry {
  agent: string
  task_title: string
  task_id: string
  elapsed_seconds: number
  tokens_used: number
}

export interface WsSnapshot {
  type: 'snapshot' | 'pong'
  db_available: boolean
  timestamp: number
  tasks: {
    by_status: Record<string, number>
    running_count: number
    total_tokens: number
    total: number
  }
  ideas: {
    total: number
    by_status: Record<string, number>
  }
  pipelines: {
    total: number
    by_phase: Record<string, number>
  }
  /** Per-agent telemetry for currently running agents (empty array when idle). */
  agents: AgentTelemetry[]
  /** Per-agent token burn totals for currently running agents. */
  agent_token_burn: Record<string, number>
}

export interface UseWebSocketResult {
  /** Latest snapshot from the server (null until first message arrives). */
  snapshot: WsSnapshot | null
  /** Connection state for UI indicators. */
  connectionState: ConnectionState
  /** Manually reconnect (e.g. after a long disconnect). */
  reconnect: () => void
}

/**
 * Connect to the dashboard WebSocket at /ws/dashboard.
 *
 * Automatically reconnects on disconnect with exponential backoff
 * (1s → 2s → 4s → capped at 30s). Resets to 1s on successful connect.
 */
export function useWebSocket(): UseWebSocketResult {
  const [snapshot, setSnapshot] = useState<WsSnapshot | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    // Close existing socket cleanly
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.onerror = null
      wsRef.current.onmessage = null
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close()
      }
    }

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/dashboard`

    setConnectionState('connecting')
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return }
      setConnectionState('connected')
      retryRef.current = 0 // reset backoff on successful connect
    }

    ws.onmessage = (event: MessageEvent) => {
      if (!mountedRef.current) return
      try {
        const data = JSON.parse(event.data) as WsSnapshot
        if (data.type === 'snapshot') {
          setSnapshot(data)
        }
        // 'pong' messages are ignored — they're just keepalive responses
      } catch {
        // Ignore unparseable messages
      }
    }

    ws.onerror = () => {
      // onclose will fire next, so we handle reconnect there
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      setConnectionState('disconnected')

      // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (cap)
      const delay = Math.min(1000 * Math.pow(2, retryRef.current), 30_000)
      retryRef.current += 1

      timerRef.current = setTimeout(() => {
        if (mountedRef.current) connect()
      }, delay)
    }
  }, [])

  const reconnect = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    retryRef.current = 0
    connect()
  }, [connect])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      if (timerRef.current) clearTimeout(timerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect loop on unmount
        wsRef.current.close()
      }
    }
  }, [connect])

  return { snapshot, connectionState, reconnect }
}
