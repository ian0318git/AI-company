import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

// ── Types ──────────────────────────────────────────────────────────────────

interface TaskEvent {
  id: string
  title: string
  status: string
  priority: string
  assigned_agent: string | null
  started_at: string | null
  completed_at: string | null
  project_id: string
  created_at: string
  updated_at: string
}

interface TimelineProject {
  id: string
  name: string
  tasks: TaskEvent[]
  span: { start: number; end: number }
}

// ── Agent color mapping ───────────────────────────────────────────────────

const AGENT_COLORS: Record<string, string> = {
  'idea-refiner':          'bg-purple-500 border-purple-400 text-purple-200',
  'tech-lead':             'bg-blue-600  border-blue-400  text-blue-200',
  'technical-writer':      'bg-slate-600 border-slate-400 text-slate-200',
  'qa-engineer':           'bg-teal-600  border-teal-400  text-teal-200',
  'project-manager':       'bg-orange-600 border-orange-400 text-orange-200',
  'embedded-firmware-engineer':  'bg-cyan-700  border-cyan-400  text-cyan-200',
  'embedded-hardware-engineer':  'bg-indigo-700 border-indigo-400 text-indigo-200',
  'embedded-linux-engineer':     'bg-stone-700 border-stone-400 text-stone-200',
  'embedded-iot-engineer':       'bg-sky-700   border-sky-400   text-sky-200',
  'embedded-sensor-driver-dev':  'bg-violet-700 border-violet-400 text-violet-200',
  'embedded-testing-engineer':   'bg-lime-700  border-lime-400  text-lime-200',
  'software-architect':          'bg-rose-700  border-rose-400  text-rose-200',
  'backend-developer':           'bg-amber-700 border-amber-400 text-amber-200',
  'frontend-developer':          'bg-pink-600  border-pink-400  text-pink-200',
  'fullstack-developer':         'bg-fuchsia-600 border-fuchsia-400 text-fuchsia-200',
  'devops-engineer':             'bg-gray-700  border-gray-400  text-gray-200',
  'security-engineer':           'bg-red-800   border-red-400   text-red-200',
  'code-reviewer':               'bg-yellow-700 border-yellow-400 text-yellow-200',
  'rapid-prototyper':            'bg-emerald-700 border-emerald-400 text-emerald-200',
}

function agentColor(agent: string | null): string {
  if (!agent) return 'bg-gray-700 border-gray-500 text-gray-300'
  return AGENT_COLORS[agent] || 'bg-gray-700 border-gray-500 text-gray-300'
}

function agentLabel(agent: string | null): string {
  if (!agent) return 'Unassigned'
  const labels: Record<string, string> = {
    'idea-refiner': 'Idea Refiner',
    'tech-lead': 'Tech Lead',
    'technical-writer': 'Writer',
    'qa-engineer': 'QA',
    'project-manager': 'PM',
    'embedded-firmware-engineer': 'Firmware',
    'embedded-hardware-engineer': 'Hardware',
    'embedded-linux-engineer': 'Linux',
    'embedded-iot-engineer': 'IoT',
    'embedded-sensor-driver-dev': 'Sensor',
    'embedded-testing-engineer': 'Test Eng',
    'software-architect': 'Architect',
    'backend-developer': 'Backend',
    'frontend-developer': 'Frontend',
    'fullstack-developer': 'Fullstack',
    'devops-engineer': 'DevOps',
    'security-engineer': 'Security',
    'code-reviewer': 'Reviewer',
    'rapid-prototyper': 'Prototyper',
  }
  return labels[agent] || agent
}

function formatTS(ts: string | null): string {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDateShort(ts: string | null): string {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric' })
}

function durationMinutes(start: string | null | undefined, end: string | null | undefined): string {
  if (!start) return ''
  const s = new Date(start).getTime()
  const e = end ? new Date(end).getTime() : Date.now()
  const ms = Math.max(0, e - s)
  const min = ms / 60000
  if (min < 1) return '<1m'
  if (min < 60) return `${Math.round(min)}m`
  return `${Math.floor(min / 60)}h ${Math.round(min % 60)}m`
}

// ── Component ──────────────────────────────────────────────────────────────

export default function Timeline() {
  const [projects, setProjects] = useState<TimelineProject[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [expandedAll, setExpandedAll] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      setError(null)
      // Fetch all tasks with agent assignments
      const tasksData: TaskEvent[] = await api.tasks.list()
      if (!Array.isArray(tasksData)) {
        setProjects([])
        setLoading(false)
        return
      }

      // Group by project
      const projMap = new Map<string, TaskEvent[]>()
      for (const t of tasksData) {
        if (!t.assigned_agent && !t.started_at && !t.completed_at) continue
        const pid = t.project_id || 'unknown'
        if (!projMap.has(pid)) projMap.set(pid, [])
        projMap.get(pid)!.push(t)
      }

      // Build timeline objects
      const result: TimelineProject[] = []
      for (const [pid, tasks] of projMap) {
        // Sort by started_at, then completed_at, then created_at
        const sorted = [...tasks].sort((a, b) => {
          const aStart = a.started_at || a.created_at
          const bStart = b.started_at || b.created_at
          return new Date(aStart).getTime() - new Date(bStart).getTime()
        })
        // Compute time span (for timeline scaling)
        const times = sorted
          .flatMap(t => [t.started_at, t.completed_at, t.created_at, t.updated_at])
          .filter(Boolean) as string[]
        const start = Math.min(...times.map(t => new Date(t).getTime()))
        const end = Math.max(...times.map(t => new Date(t).getTime()))
        result.push({
          id: pid,
          name: `Project ${pid.slice(0, 8)}…`,
          tasks: sorted,
          span: { start, end },
        })
      }

      // Sort by most recent first
      result.sort((a, b) => b.span.end - a.span.end)
      setProjects(result)
      setLoading(false)
    } catch (e: any) {
      console.warn('[Timeline]', e)
      setError(e?.message || 'Failed to load timeline data')
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const toggleProject = (pid: string) => {
    setCollapsed(prev => {
      const next = new Set(prev)
      if (next.has(pid)) next.delete(pid)
      else next.add(pid)
      return next
    })
  }

  const toggleAll = () => {
    if (expandedAll) {
      // Collapse all
      setCollapsed(new Set(projects.map(p => p.id)))
    } else {
      setCollapsed(new Set())
    }
    setExpandedAll(!expandedAll)
  }

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Cycle Timeline</h2>
          {loading && (
            <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Loading...
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleAll}
            className="text-xs px-3 py-1.5 rounded border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
          >
            {expandedAll ? 'Collapse All' : 'Expand All'}
          </button>
          <span className="text-sm text-gray-400">{projects.length} projects</span>
        </div>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          ⚠ {error}
        </div>
      )}

      {!loading && !error && projects.length === 0 && (
        <div className="border border-dashed border-gray-700 rounded-lg p-12 text-center">
          <p className="text-gray-500 text-sm">No project timeline data available yet.</p>
          <p className="text-gray-600 text-xs mt-2">Timeline populates as agents are assigned to tasks and work is tracked.</p>
        </div>
      )}

      <div className="space-y-4">
        {projects.map(proj => {
          const isCollapsed = collapsed.has(proj.id)
          return (
            <div
              key={proj.id}
              className="border border-[hsl(var(--border))] rounded-lg bg-white/5 overflow-hidden"
            >
              {/* Project header (clickable to toggle) */}
              <button
                onClick={() => toggleProject(proj.id)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-gray-500 transition-transform ${isCollapsed ? '' : 'rotate-90'}`}>
                    ▶
                  </span>
                  <span className="font-semibold text-sm text-gray-200">{proj.name}</span>
                  <span className="text-xs text-gray-500">
                    {formatDateShort(proj.tasks[0]?.started_at || proj.tasks[0]?.created_at)}
                    {' — '}
                    {formatDateShort(proj.tasks[proj.tasks.length - 1]?.completed_at || proj.tasks[proj.tasks.length - 1]?.updated_at)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{proj.tasks.length} tasks</span>
                  <span className="text-[10px] text-gray-600">
                    {durationMinutes(
                      proj.tasks[0]?.started_at || proj.tasks[0]?.created_at,
                      proj.tasks[proj.tasks.length - 1]?.completed_at || undefined,
                    )}
                  </span>
                </div>
              </button>

              {/* Timeline body */}
              {!isCollapsed && (
                <div className="relative px-4 pb-4">
                  {/* Vertical line */}
                  <div className="absolute left-[52px] top-0 bottom-0 w-px bg-white/10" />

                  {proj.tasks.map((task, idx) => {
                    const colors = agentColor(task.assigned_agent).split(' ')
                    const circleColor = colors[0] || 'bg-gray-700'

                    return (
                      <div key={task.id} className="relative flex items-start gap-4 pt-3 first:pt-2">
                        {/* Timeline dot */}
                        <div className="relative z-10 flex-shrink-0 pt-0.5">
                          <div className={`w-3.5 h-3.5 rounded-full border-2 ${colors[1] || 'border-gray-500'} ${circleColor}`} />
                        </div>

                        {/* Card */}
                        <div className="flex-1 min-w-0">
                          <div className="border border-[hsl(var(--border))] rounded p-2.5 bg-black/20">
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0 flex-1">
                                <p className="text-xs font-medium text-gray-200 truncate">{task.title}</p>
                                <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colors.join(' ')}`}>
                                    {agentLabel(task.assigned_agent)}
                                  </span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    task.status === 'done'
                                      ? 'bg-green-900/40 text-green-400'
                                      : task.status === 'in_progress'
                                        ? 'bg-blue-900/40 text-blue-400'
                                        : 'bg-gray-800 text-gray-400'
                                  }`}>
                                    {task.status.replace('_', ' ')}
                                  </span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    task.priority === 'critical'
                                      ? 'bg-red-900/50 text-red-400'
                                      : task.priority === 'high'
                                        ? 'bg-orange-900/50 text-orange-400'
                                        : 'bg-gray-800 text-gray-400'
                                  }`}>
                                    {task.priority || 'medium'}
                                  </span>
                                </div>
                              </div>
                              {/* Time info */}
                              <div className="flex-shrink-0 text-right">
                                <span className="text-[10px] text-gray-500 font-mono">
                                  {durationMinutes(task.started_at, task.completed_at)}
                                </span>
                              </div>
                            </div>
                            {/* Timestamps */}
                            <div className="flex items-center gap-3 mt-1.5">
                              {task.started_at && (
                                <span className="text-[10px] text-gray-600">
                                  🚀 {formatTS(task.started_at)}
                                </span>
                              )}
                              {task.completed_at && (
                                <span className="text-[10px] text-gray-600">
                                  ✅ {formatTS(task.completed_at)}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
