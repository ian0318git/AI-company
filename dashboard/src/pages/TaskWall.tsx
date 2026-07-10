import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api/client'

const COLUMNS = ['todo', 'in_progress', 'blocked', 'review', 'done'] as const
const COLORS: Record<string, string> = {
  todo: 'bg-gray-600',
  in_progress: 'bg-blue-600',
  blocked: 'bg-red-600',
  review: 'bg-yellow-600',
  done: 'bg-green-600',
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatMinutesShort(m: number): string {
  if (m < 1) return '<1m'
  if (m < 60) return `${Math.round(m)}m`
  return `${Math.floor(m / 60)}h ${Math.round(m % 60)}m`
}

function taskTimeDisplay(t: any) {
  const started = t.started_at ? new Date(t.started_at) : null
  const completed = t.completed_at ? new Date(t.completed_at) : null
  const pausedSecs = t.paused_seconds || 0
  const estimated = t.estimated_minutes || null

  if (!started) return { label: '', isSlow: false, isPaused: false }

  const now = new Date()
  const end = completed || now
  let pausedMs = pausedSecs * 1000
  if (t.last_paused_at && !completed) {
    pausedMs += (now.getTime() - new Date(t.last_paused_at).getTime())
  }
  const elapsedTotal = end.getTime() - started.getTime()
  const elapsedWork = Math.max(0, elapsedTotal - pausedMs)
  const elapsedMin = elapsedWork / 60000

  let isSlow = false
  if (t.status === 'in_progress' && estimated) {
    isSlow = elapsedMin > estimated * 2
  }
  const isPaused = !!t.last_paused_at && !completed

  return {
    label: formatMinutesShort(elapsedMin),
    isSlow,
    isPaused,
  }
}

/** Build a stable key for a task ID -> status mapping. */
function statusMapKey(t: any): string {
  return `${t.id}::${t.status}`
}

// ── Component ──────────────────────────────────────────────────────────────

export default function TaskWall() {
  const [tasks, setTasks] = useState<Record<string, any[]>>(
    { todo: [], in_progress: [], blocked: [], review: [], done: [] }
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Track previous statuses so we can detect newly completed tasks
  const prevStatusesRef = useRef<Set<string>>(new Set())

  // Track IDs of tasks that just completed (for animation)
  const [completedAnimations, setCompletedAnimations] = useState<Set<string>>(new Set())

  const POLL_INTERVAL_MS = 5_000

  const fetchTasks = useCallback(async () => {
    try {
      setError(null)
      const data = await api.tasks.list()
      const grouped: Record<string, any[]> = {
        todo: [], in_progress: [], blocked: [], review: [], done: [],
      }

      if (Array.isArray(data)) {
        const newStatusKeys = new Set<string>()

        for (const t of data) {
          const s = t.status || 'todo'
          if (grouped[s]) grouped[s].push(t)
          const key = statusMapKey(t)
          newStatusKeys.add(key)
        }

        // Detect tasks that just transitioned to 'done'
        const justCompleted: string[] = []
        for (const t of (grouped.done || [])) {
          const prevKey = `${t.id}::todo`    // was anything but done
          const prevKeyIp = `${t.id}::in_progress`
          const prevKeyRv = `${t.id}::review`
          const prevKeyBl = `${t.id}::blocked`
          if (
            prevStatusesRef.current.has(prevKey) ||
            prevStatusesRef.current.has(prevKeyIp) ||
            prevStatusesRef.current.has(prevKeyRv) ||
            prevStatusesRef.current.has(prevKeyBl)
          ) {
            justCompleted.push(t.id)
          }
        }

        if (justCompleted.length > 0) {
          setCompletedAnimations(prev => {
            const next = new Set(prev)
            for (const id of justCompleted) next.add(id)
            return next
          })
          // Clear animation flags after 3 seconds
          setTimeout(() => {
            setCompletedAnimations(prev => {
              const next = new Set(prev)
              for (const id of justCompleted) next.delete(id)
              return next
            })
          }, 3000)
        }

        prevStatusesRef.current = newStatusKeys
      }

      setTasks(grouped)
      setLoading(false)
    } catch (e: any) {
      console.warn('[TaskWall]', e)
      setError(e?.message || 'Failed to load tasks')
      setLoading(false)
    }
  }, [])

  // Initial fetch + polling
  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchTasks])

  const total = Object.values(tasks).reduce((sum, arr) => sum + arr.length, 0)

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Task Wall</h2>
          {loading && (
            <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Loading...
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-[11px] text-gray-500 bg-white/5 px-2.5 py-1 rounded-full">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live (5s)
          </span>
          <span className="text-sm text-gray-400">{total} tasks</span>
        </div>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          ⚠ {error}
        </div>
      )}

      {!loading && !error && total === 0 && (
        <div className="border border-dashed border-gray-700 rounded-lg p-12 text-center">
          <p className="text-gray-500 text-sm">No tasks yet — ideas and pipelines generate tasks automatically.</p>
        </div>
      )}

      <div className="grid grid-cols-5 gap-3">
        {COLUMNS.map(col => (
          <div key={col} className="border border-[hsl(var(--border))] rounded-lg bg-white/5 p-3">
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-2 h-2 rounded-full ${COLORS[col]}`} />
              <span className="text-xs font-semibold uppercase text-gray-400">
                {col.replace('_', ' ')}
              </span>
              <span className="ml-auto text-xs text-gray-500">{tasks[col].length}</span>
            </div>
            <div className="space-y-2 min-h-[60px]">
              {tasks[col].map((t: any) => {
                const timeInfo = taskTimeDisplay(t)
                const justCompleted = completedAnimations.has(t.id)

                return (
                  <div
                    key={t.id}
                    className={[
                      'border rounded p-2 bg-black/20 transition-all duration-700',
                      justCompleted
                        ? 'border-emerald-400/60 bg-emerald-500/10 animate-complete-pop'
                        : timeInfo.isSlow
                          ? 'border-red-500/40 bg-red-500/5'
                          : timeInfo.isPaused
                            ? 'border-yellow-500/30'
                            : 'border-[hsl(var(--border))]',
                    ].join(' ')}
                  >
                    <p className="text-xs font-medium">{t.title}</p>
                    {/* Elapsed time */}
                    {timeInfo.label && (
                      <div className="flex items-center gap-1 mt-1">
                        <span className={
                          `text-[10px] ${
                            timeInfo.isSlow
                              ? 'text-red-400'
                              : timeInfo.isPaused
                                ? 'text-yellow-400'
                                : 'text-gray-500'
                          }`
                        }>
                          {timeInfo.isPaused ? '⏸ ' : '⏱ '}{timeInfo.label}
                        </span>
                        {timeInfo.isSlow && (
                          <span className="text-[10px] text-red-400 font-bold">SLOW</span>
                        )}
                        {justCompleted && (
                          <span className="text-[10px] text-emerald-400 font-bold ml-1">✓ DONE</span>
                        )}
                      </div>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        t.priority === 'critical'
                          ? 'bg-red-900/50 text-red-400'
                          : t.priority === 'high'
                            ? 'bg-orange-900/50 text-orange-400'
                            : 'bg-gray-800 text-gray-400'
                      }`}>
                        {t.priority || 'medium'}
                      </span>
                      {t.assigned_agent && (
                        <span className="text-[10px] text-gray-500">{t.assigned_agent}</span>
                      )}
                    </div>
                  </div>
                )
              })}
              {tasks[col].length === 0 && (
                <p className="text-xs text-gray-600 text-center py-4">No tasks</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Completion animation keyframes injected once */}
      <style>{`
        @keyframes complete-pop {
          0%   { transform: scale(1); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4); }
          50%  { transform: scale(1.03); box-shadow: 0 0 12px 4px rgba(52, 211, 153, 0.25); }
          100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }
        .animate-complete-pop {
          animation: complete-pop 0.7s ease-out;
        }
      `}</style>
    </div>
  )
}
