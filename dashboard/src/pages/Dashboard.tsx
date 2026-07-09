import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Cpu, ListTodo, Lightbulb, GitBranch, Clock, AlertTriangle, CheckCircle, Users, FolderOpen, Coins, TrendingUp } from 'lucide-react'
import { useTaskMetrics } from '../hooks/useTaskTime'

function formatMinutes(m: number): string {
  if (m < 1) return '<1m'
  if (m < 60) return `${Math.round(m)}m`
  const h = Math.floor(m / 60)
  const r = Math.round(m % 60)
  return r > 0 ? `${h}h ${r}m` : `${h}h`
}

interface AgentTime {
  agent: string
  minutes: number
}

interface ProjectTime {
  id: string
  name: string
  total_minutes: number
  total_minutes_formatted: string
  total_tasks: number
  tracked_tasks: number
  completed_tasks: number
  agent_breakdown: AgentTime[]
  token_breakdown: { agent: string; tokens: number }[]
  total_tokens: number
  status_counts: Record<string, number>
}

interface DashboardMetrics {
  pipelines: { total: number; by_phase: Record<string, number>; by_type: Record<string, number> }
  ideas: { total: number; by_status: Record<string, number>; daily_created: Record<string, number> }
  tasks: { total: number; tracked: number; by_status: Record<string, number>; today_minutes: number; completed_count: number; average_completion_minutes: number | null; total_tokens: number }
  projects: { total: number; active: number }
  evolution: { total_failures: number; by_category: Record<string, number>; by_severity: Record<string, number>; antibodies: number; vaccines: number }
  cycle_throughput: { ideas_per_day: Record<string, number>; pipelines_per_day: Record<string, number> }
}

export default function Dashboard() {
  const [dm, setDm] = useState<DashboardMetrics | null>(null)
  const [activeProjects, setActiveProjects] = useState<any[]>([])
  const [completedProjects, setCompletedProjects] = useState<any[]>([])
  const [projectTimes, setProjectTimes] = useState<Map<string, ProjectTime>>(new Map())
  const [tokenHistory, setTokenHistory] = useState<{ date: string; tokens: number }[]>([])
  const { metrics } = useTaskMetrics(60_000)

  const loadProjectTimes = (projects: any[]) => {
    if (!Array.isArray(projects)) return
    projects.forEach((p: any) => {
      api.projects.getTime(p.id).then((pt: ProjectTime) => {
        setProjectTimes(prev => new Map(prev).set(p.id, pt))
      }).catch(() => {})
    })
  }

  useEffect(() => {
    // Load consolidated dashboard metrics
    api.dashboard.metrics().then(setDm).catch(() => {})
    // Load active + recent completed projects (for time/token breakdown)
    api.projects.list('active').then(projects => {
      if (Array.isArray(projects)) {
        setActiveProjects(projects)
        loadProjectTimes(projects)
      }
    }).catch(e => console.warn('[Dashboard]', e))
    // Load last 5 completed projects with time data
    api.projects.list('completed').then(projects => {
      if (Array.isArray(projects)) {
        const recent = projects.slice(0, 5)
        setCompletedProjects(recent)
        loadProjectTimes(recent)
      }
    }).catch(e => console.warn('[Dashboard]', e))
    // Load daily token history
    api.tasks.tokenHistory().then(d => {
      if (d?.daily) setTokenHistory(d.daily)
    }).catch(() => {})
  }, [])

  const projects = dm?.projects ?? { total: 0, active: 0 }
  const tasks = dm?.tasks ?? { total: 0, tracked: 0, by_status: {}, today_minutes: 0, completed_count: 0, average_completion_minutes: null, total_tokens: 0 }
  const ideas = dm?.ideas ?? { total: 0, by_status: {}, daily_created: {} }
  const pipelines = dm?.pipelines ?? { total: 0, by_phase: {}, by_type: {} }

  const cards = [
    { label: 'Projects', value: projects.total, icon: Cpu, color: 'text-blue-400', sub: `${projects.active} active` },
    { label: 'Tasks', value: tasks.total, icon: ListTodo, color: 'text-yellow-400', sub: `${tasks.completed_count} done` },
    { label: 'Ideas', value: ideas.total, icon: Lightbulb, color: 'text-purple-400', sub: `${Object.values(ideas.by_status).reduce((a, b) => a + b, 0) - (ideas.by_status?.done ?? 0)} pending` },
    { label: 'Pipelines', value: pipelines.total, icon: GitBranch, color: 'text-green-400', sub: `${(pipelines.by_phase?.done ?? 0)} completed` },
  ]

  const timeCards = metrics ? [
    { label: 'Today Tracked', value: formatMinutes(metrics.today_minutes), icon: Clock, color: 'text-cyan-400' },
    { label: 'Avg Task Time', value: metrics.average_completion_minutes ? formatMinutes(metrics.average_completion_minutes) : '—', icon: Clock, color: 'text-indigo-400' },
    { label: 'Active Tasks', value: metrics.active_count, icon: CheckCircle, color: 'text-blue-400' },
    { label: 'Slow Tasks', value: metrics.slow_count, icon: AlertTriangle, color: metrics.slow_count > 0 ? 'text-red-400' : 'text-gray-400' },
  ] : null

  // Agent label mapping (short display names)
  const agentLabels: Record<string, string> = {
    'idea-refiner': 'Refiner',
    'tech-lead': 'Tech Lead',
    'technical-writer': 'Writer',
    'qa-engineer': 'QA',
    'project-manager': 'PM',
    'embedded-firmware-engineer': 'Firmware',
    'embedded-hardware-engineer': 'Hardware',
    'embedded-testing-engineer': 'Test Eng',
    'frontend-developer': 'Frontend',
    'backend-developer': 'Backend',
    'fullstack-developer': 'Fullstack',
    'software-architect': 'Architect',
    'devops-engineer': 'DevOps',
    'rapid-prototyper': 'Prototyper',
    'unassigned': '—',
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {/* Main stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {cards.map((card) => {
          const Icon = card.icon
          return (
          <div key={card.label} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-5 h-5 ${card.color}`} />
              <span className="text-sm text-gray-400">{card.label}</span>
            </div>
            <p className="text-3xl font-bold">{card.value}</p>
            {'sub' in card ? <p className="text-xs text-gray-500 mt-1">{card.sub}</p> : null}
          </div>)
        })}
      </div>

      {/* Time tracking stats */}
      {timeCards && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          {timeCards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-5 h-5 ${color}`} />
                <span className="text-sm text-gray-400">{label}</span>
              </div>
              <p className="text-3xl font-bold">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Agent Performance: Combined Time + Token */}
      {metrics && metrics.agent_breakdown && metrics.agent_breakdown.length > 0 && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-indigo-400" />
            <h3 className="text-lg font-semibold text-gray-200">Agent Performance</h3>
            <span className="text-sm text-gray-500 ml-auto">
              {metrics.total_tokens.toLocaleString()} 🪙 total
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-white/10">
                  <th className="text-left py-2 pr-4">Agent</th>
                  <th className="text-right py-2 px-4">Time</th>
                  <th className="text-right py-2 px-4">Tokens</th>
                  <th className="text-right py-2 pl-4 w-40">Time Distribution</th>
                  <th className="text-right py-2 pl-4 w-40">Token Distribution</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const maxTime = metrics.agent_breakdown[0]?.minutes || 1
                  const maxTokens = metrics.token_breakdown[0]?.tokens || 1
                  // Merge time + token data
                  const merged = metrics.agent_breakdown.map(a => ({
                    agent: a.agent,
                    minutes: a.minutes,
                    tokens: metrics.token_breakdown?.find(t => t.agent === a.agent)?.tokens || 0,
                  }))
                  return merged.map((a, i) => (
                    <tr key={a.agent} className={`${i < merged.length - 1 ? 'border-b border-white/5' : ''}`}>
                      <td className="py-2.5 pr-4 font-medium text-gray-200">{agentLabels[a.agent] || a.agent}</td>
                      <td className="py-2.5 px-4 text-right text-gray-300 font-mono">{formatMinutes(a.minutes)}</td>
                      <td className="py-2.5 px-4 text-right text-gray-300 font-mono">{a.tokens.toLocaleString()}</td>
                      <td className="py-2.5 pl-4">
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 rounded-full transition-all"
                               style={{ width: `${(a.minutes / maxTime) * 100}%` }} />
                        </div>
                      </td>
                      <td className="py-2.5 pl-4">
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-yellow-500 rounded-full transition-all"
                               style={{ width: `${(a.tokens / maxTokens) * 100}%` }} />
                        </div>
                      </td>
                    </tr>
                  ))
                })()}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Daily Token Usage Chart */}
      {tokenHistory.length > 0 && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-gray-200">Daily Token Usage</h3>
            <span className="text-sm text-gray-500 ml-auto">
              {tokenHistory.reduce((s, d) => s + d.tokens, 0).toLocaleString()} total
            </span>
          </div>
          <div className="flex items-end gap-2 h-24">
            {(() => {
              const max = Math.max(...tokenHistory.map(d => d.tokens), 1)
              return tokenHistory.map(d => (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                  <span className="text-[10px] text-gray-400 font-mono">{(d.tokens / 1000).toFixed(1)}k</span>
                  <div className="w-full bg-yellow-500/80 rounded-t"
                       style={{ height: `${(d.tokens / max) * 100}%`, minHeight: d.tokens > 0 ? '8px' : '0' }}
                       title={`${d.date}: ${d.tokens.toLocaleString()} tokens`} />
                  <span className="text-[10px] text-gray-500">{d.date.slice(5)}</span>
                </div>
              ))
            })()}
          </div>
        </div>
      )}

      {/* Evolution Health */}
      {dm && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold text-gray-200">Evolution System Health</h3>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Failures</p>
              <p className="text-xl font-bold text-red-400">{dm.evolution.total_failures}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Antibodies</p>
              <p className="text-xl font-bold text-blue-400">{dm.evolution.antibodies}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Vaccines</p>
              <p className="text-xl font-bold text-green-400">{dm.evolution.vaccines}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Ideas/Day</p>
              <p className="text-xl font-bold text-purple-400">{Object.keys(dm.cycle_throughput?.ideas_per_day ?? {}).length} days</p>
            </div>
          </div>
        </div>
      )}

      {/* Slow tasks alert */}
      {metrics && metrics.slow_count > 0 && (
        <div className="border border-red-500/20 rounded-lg p-4 bg-red-500/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-red-400">Slow Tasks ({metrics.slow_count})</h3>
          </div>
          <div className="space-y-2">
            {metrics.slow_tasks.map(t => (
              <div key={t.id} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{t.title}</span>
                <span className="text-red-400 font-mono">{formatMinutes(t.elapsed_minutes)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Projects */}
      {activeProjects.length > 0 && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <FolderOpen className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-gray-200">Active Projects</h3>
          </div>
          <div className="space-y-3">
            {activeProjects.map(p => {
              const pt = projectTimes.get(p.id)
              return (
                <div key={p.id} className="border border-[hsl(var(--border))] rounded p-3 bg-black/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm text-gray-200">{p.name}</span>
                    {pt && (
                      <span className="text-sm text-gray-400 font-mono">{pt.total_minutes_formatted}</span>
                    )}
                  </div>
                  {pt && (
                    <div className="grid grid-cols-4 gap-2 text-xs text-gray-500">
                      <span>📋 {pt.total_tasks} tasks</span>
                      <span>⏱ {pt.tracked_tasks} tracked</span>
                      <span>✅ {pt.completed_tasks} done</span>
                      <span>🪙 {pt.total_tokens.toLocaleString()} tokens</span>
                    </div>
                  )}
                  {pt && pt.agent_breakdown.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {pt.agent_breakdown.map((a: AgentTime) => {
                        const tokens = pt.token_breakdown?.find(t => t.agent === a.agent)
                        return (
                          <span key={a.agent} className="text-[10px] px-2 py-0.5 rounded bg-white/10 text-gray-400">
                            {agentLabels[a.agent] || a.agent}: {formatMinutes(a.minutes)}
                            {tokens ? ` / ${tokens.tokens.toLocaleString()}🪙` : ''}
                          </span>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Recent Completed Projects */}
      {completedProjects.length > 0 && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold text-gray-200">Recent Completed Projects</h3>
          </div>
          <div className="space-y-3">
            {completedProjects.slice(0, 5).map(p => {
              const pt = projectTimes.get(p.id)
              return (
                <div key={p.id} className="border border-[hsl(var(--border))] rounded p-3 bg-black/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm text-gray-200">{p.name}</span>
                    {pt && <span className="text-sm text-gray-400 font-mono">{pt.total_minutes_formatted} / 🪙{pt.total_tokens.toLocaleString()}</span>}
                  </div>
                  {pt && pt.agent_breakdown.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {pt.agent_breakdown.map((a: AgentTime) => {
                        const tok = pt.token_breakdown?.find(t => t.agent === a.agent)
                        return (
                          <span key={a.agent} className="text-[10px] px-2 py-0.5 rounded bg-white/10 text-gray-400">
                            {agentLabels[a.agent] || a.agent}: {formatMinutes(a.minutes)}{tok && tok.tokens > 0 ? ` / 🪙${tok.tokens.toLocaleString()}` : ''}
                          </span>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Capture New Idea', desc: 'Submit a new product idea for refinement' },
            { label: 'Create Pipeline', desc: 'Start a development pipeline from an idea' },
            { label: 'Check Hardware', desc: 'Detect connected dev boards and sensors' },
            { label: 'View Task Wall', desc: 'See what the team is working on' },
          ].map(({ label, desc }) => (
            <div key={label} className="border border-[hsl(var(--border))] rounded p-3 cursor-pointer hover:bg-white/5 transition-colors">
              <p className="font-medium text-sm">{label}</p>
              <p className="text-xs text-gray-500 mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
