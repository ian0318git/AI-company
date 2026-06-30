import { useState, useEffect } from 'react'
import { api } from '../api/client'

const COLUMNS = ['todo', 'in_progress', 'blocked', 'review', 'done'] as const
const COLORS: Record<string, string> = {
  todo: 'bg-gray-600',
  in_progress: 'bg-blue-600',
  blocked: 'bg-red-600',
  review: 'bg-yellow-600',
  done: 'bg-green-600',
}

export default function TaskWall() {
  const [tasks, setTasks] = useState<Record<string, any[]>>({ todo: [], in_progress: [], blocked: [], review: [], done: [] })

  useEffect(() => {
    api.tasks.list().then((data: any) => {
      const grouped: Record<string, any[]> = { todo: [], in_progress: [], blocked: [], review: [], done: [] }
      if (Array.isArray(data)) {
        for (const t of data) {
          const s = t.status || 'todo'
          if (grouped[s]) grouped[s].push(t)
        }
      }
      setTasks(grouped)
    }).catch(() => {})
  }, [])

  const total = Object.values(tasks).reduce((sum, arr) => sum + arr.length, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Task Wall</h2>
        <span className="text-sm text-gray-400">{total} tasks</span>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {COLUMNS.map(col => (
          <div key={col} className="border border-[hsl(var(--border))] rounded-lg bg-white/5 p-3">
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-2 h-2 rounded-full ${COLORS[col]}`} />
              <span className="text-xs font-semibold uppercase text-gray-400">{col.replace('_', ' ')}</span>
              <span className="ml-auto text-xs text-gray-500">{tasks[col].length}</span>
            </div>
            <div className="space-y-2">
              {tasks[col].map((t: any) => (
                <div key={t.id} className="border border-[hsl(var(--border))] rounded p-2 bg-black/20">
                  <p className="text-xs font-medium">{t.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${t.priority === 'critical' ? 'bg-red-900/50 text-red-400' : t.priority === 'high' ? 'bg-orange-900/50 text-orange-400' : 'bg-gray-800 text-gray-400'}`}>
                      {t.priority || 'medium'}
                    </span>
                    {t.assigned_agent && (
                      <span className="text-[10px] text-gray-500">{t.assigned_agent}</span>
                    )}
                  </div>
                </div>
              ))}
              {tasks[col].length === 0 && (
                <p className="text-xs text-gray-600 text-center py-4">No tasks</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
