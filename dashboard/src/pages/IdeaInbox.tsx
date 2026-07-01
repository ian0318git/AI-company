import { useState, useEffect } from 'react'
import {
  Lightbulb, Send, Loader2, AlertCircle, ChevronDown, ChevronUp,
  Sparkles, Play, CheckCircle2, Circle, Clock, Users, ListTodo,
  ArrowRight, TrendingUp, FileText, Download,
} from 'lucide-react'
import { api } from '../api/client'
import { useI18n } from '../i18n/context'

interface Idea {
  id: string; title: string; raw_description: string; refined_description: string | null
  tags: string[]; status: string; suggested_pipeline: string | null; created_at: string
}
interface WorkflowStep { phase: string; name: string; agent: string; status: string }
interface WorkflowTask { id: string; title: string; status: string; priority: string; assigned_agent: string | null }
interface WorkflowMember { role: string; status: string }
interface AgentAction {
  id: string; agent: string; title: string; description: string
  inputs: string[]; outputs: string[]; depends_on: string[]; parallel_group: string | null; status: string
}
interface WorkflowState {
  idea: Idea
  pipeline: { id: string; pipeline_type: string; current_phase: string; steps: WorkflowStep[] } | null
  tasks: WorkflowTask[]
  team: { id: string; name: string; members: WorkflowMember[] } | null
  agent_workflow: AgentAction[] | null
}

const PHASE_ORDER = ['idea', 'requirements', 'design', 'implementation', 'testing', 'deploy', 'done']

const statusColors: Record<string, string> = {
  new: 'bg-blue-500/20 text-blue-400', refining: 'bg-yellow-500/20 text-yellow-400',
  approved: 'bg-green-500/20 text-green-400', rejected: 'bg-red-500/20 text-red-400',
  in_progress: 'bg-purple-500/20 text-purple-400', done: 'bg-emerald-500/20 text-emerald-400',
}

const agentColors: Record<string, string> = {
  'idea-refiner': 'border-yellow-500/30', 'tech-lead': 'border-blue-500/30',
  'technical-writer': 'border-green-500/30', 'qa-engineer': 'border-red-500/30',
  'project-manager': 'border-purple-500/30', 'embedded-firmware-engineer': 'border-cyan-500/30',
  'embedded-hardware-engineer': 'border-orange-500/30', 'embedded-sensor-driver-dev': 'border-pink-500/30',
  'embedded-testing-engineer': 'border-lime-500/30', 'embedded-iot-engineer': 'border-teal-500/30',
  'embedded-linux-engineer': 'border-indigo-500/30', 'frontend-developer': 'border-sky-500/30',
  'backend-developer': 'border-emerald-500/30', 'software-architect': 'border-violet-500/30',
  'fullstack-developer': 'border-rose-500/30', 'devops-engineer': 'border-amber-500/30',
  'rapid-prototyper': 'border-fuchsia-500/30', 'security-engineer': 'border-red-600/30',
  'code-reviewer': 'border-slate-500/30',
}
const agentDotColors: Record<string, string> = {
  'idea-refiner': 'bg-yellow-500', 'tech-lead': 'bg-blue-500',
  'technical-writer': 'bg-green-500', 'qa-engineer': 'bg-red-500',
  'project-manager': 'bg-purple-500', 'embedded-firmware-engineer': 'bg-cyan-500',
  'embedded-hardware-engineer': 'bg-orange-500', 'embedded-sensor-driver-dev': 'bg-pink-500',
  'embedded-testing-engineer': 'bg-lime-500', 'embedded-iot-engineer': 'bg-teal-500',
  'embedded-linux-engineer': 'bg-indigo-500', 'frontend-developer': 'bg-sky-500',
  'backend-developer': 'bg-emerald-500', 'software-architect': 'bg-violet-500',
  'fullstack-developer': 'bg-rose-500', 'devops-engineer': 'bg-amber-500',
  'rapid-prototyper': 'bg-fuchsia-500', 'security-engineer': 'bg-red-600',
  'code-reviewer': 'bg-slate-500',
}

export default function IdeaInbox() {
  const { tr } = useI18n()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [loadingIdeas, setLoadingIdeas] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [refiningId, setRefiningId] = useState<string | null>(null)
  const [startingId, setStartingId] = useState<string | null>(null)
  const [workflows, setWorkflows] = useState<Record<string, WorkflowState>>({})
  const [deliverables, setDeliverables] = useState<Record<string, any[]>>({})

  const fetchIdeas = async () => {
    try {
      const data = await api.ideas.list()
      setIdeas(Array.isArray(data) ? data : (data as any).ideas || [])
    } catch { /* ignore */ }
    finally { setLoadingIdeas(false) }
  }
  useEffect(() => { fetchIdeas() }, [])

  const handleSubmit = async () => {
    if (!title.trim()) return
    setLoading(true); setError('')
    try {
      await api.ideas.create({ title: title.trim(), raw_description: description.trim(), tags: tags.split(',').map(t => t.trim()).filter(Boolean) })
      setTitle(''); setDescription(''); setTags('')
      await fetchIdeas()
    } catch (e: any) { setError(e.message || 'Failed to submit idea') }
    finally { setLoading(false) }
  }

  const handleRefine = async (id: string) => {
    setRefiningId(id)
    try { const r = await api.ideas.refine(id); setIdeas(p => p.map(i => i.id === id ? r : i)) } catch {}
    finally { setRefiningId(null) }
  }

  const handleStart = async (id: string) => {
    setStartingId(id)
    try { const w = await api.ideas.start(id); setWorkflows(p => ({ ...p, [id]: w })); setIdeas(p => p.map(i => i.id === id ? w.idea : i)) } catch {}
    finally { setStartingId(null) }
  }

  const handleTaskToggle = async (ideaId: string, taskId: string, s: string) => {
    const next = s === 'todo' ? 'in_progress' : s === 'in_progress' ? 'done' : 'todo'
    try { await api.tasks.updateStatus(taskId, next); const wf = await api.ideas.workflow(ideaId); setWorkflows(p => ({ ...p, [ideaId]: wf })) } catch {}
  }

  const handleAdvancePhase = async (ideaId: string, pipelineId: string) => {
    try { await api.pipelines.advance(pipelineId); const wf = await api.ideas.workflow(ideaId); setWorkflows(p => ({ ...p, [ideaId]: wf })) } catch {}
  }

  const handleToggleExpand = async (ideaId: string) => {
    if (expanded === ideaId) { setExpanded(null); return }
    setExpanded(ideaId)
    if (!workflows[ideaId]) { try { const wf = await api.ideas.workflow(ideaId); setWorkflows(p => ({ ...p, [ideaId]: wf })) } catch {} }
    if (!deliverables[ideaId]) { try { const d = await api.ideas.deliverables(ideaId); setDeliverables(p => ({ ...p, [ideaId]: d })) } catch {} }
  }

  const renderWorkflow = (wf: WorkflowState) => {
    const { pipeline, tasks, team } = wf
    const currentIdx = pipeline ? PHASE_ORDER.indexOf(pipeline.current_phase) : -1
    const totalPhases = pipeline?.steps.length || 1
    const taskCounts = { todo: 0, in_progress: 0, done: 0 }
    tasks.forEach(t => { if (t.status in taskCounts) taskCounts[t.status as keyof typeof taskCounts]++ })

    const phasePct = totalPhases > 0 ? Math.round((currentIdx / totalPhases) * 100) : 0
    const taskPct = tasks.length > 0 ? Math.round((taskCounts.done / tasks.length) * 100) : 0
    const overallPct = tasks.length > 0 ? Math.round(phasePct * 0.7 + taskPct * 0.3) : phasePct
    const isComplete = overallPct >= 100

    return (
      <div className="border border-t-0 border-[hsl(var(--border))] rounded-b p-5 bg-white/[0.03] -mt-px space-y-5">
        {/* Overall Progress */}
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">{tr('wf.overallProgress')}</span>
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold ${isComplete ? 'text-green-400' : 'text-blue-400'}`}>{overallPct}%</span>
                {isComplete && <CheckCircle2 className="w-5 h-5 text-green-400" />}
              </div>
            </div>
            <div className="h-2.5 bg-white/10 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${isComplete ? 'bg-green-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'}`}
                   style={{ width: `${overallPct}%` }} />
            </div>
          </div>
          {pipeline && (
            <button
              onClick={e => { e.stopPropagation(); handleAdvancePhase(wf.idea.id, pipeline.id) }}
              disabled={pipeline.current_phase === 'done'}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/50 hover:bg-blue-500 disabled:opacity-30 rounded text-sm font-medium transition-colors shrink-0"
            >
              <ArrowRight className="w-4 h-4" />{tr('wf.nextPhase')}
            </button>
          )}
        </div>

        {/* Pipeline Progress */}
        {pipeline && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                {tr('wf.pipeline')}: {tr(`pipeline.${pipeline.pipeline_type}`) || pipeline.pipeline_type}
              </span>
              <span className="text-sm text-gray-500">
                {tr('wf.phase')} {currentIdx + 1}/{totalPhases}: {pipeline.current_phase.toUpperCase()}
              </span>
            </div>
            <div className="flex gap-1">
              {pipeline.steps.map((step, i) => {
                const idx = PHASE_ORDER.indexOf(step.phase)
                return (
                  <div key={i} className="flex-1 group relative">
                    <div className={`h-2 rounded-full transition-colors ${idx < currentIdx ? 'bg-green-500' : idx === currentIdx ? 'bg-blue-500 animate-pulse' : 'bg-white/10'}`}
                         title={`${step.phase}: ${step.name} — ${tr(`agent.${step.agent}`) || step.agent}`} />
                  </div>
                )
              })}
            </div>
            <div className="flex justify-between mt-2">
              {pipeline.steps.map((step, i) => {
                const idx = PHASE_ORDER.indexOf(step.phase)
                return (
                  <div key={i} className="text-xs text-gray-500 truncate max-w-[70px] text-center"
                       title={`${step.name}\nAgent: ${tr(`agent.${step.agent}`) || step.agent}`}>
                    {idx < currentIdx ? '✓' : idx === currentIdx ? '●' : ''} {step.name}
                  </div>
                )
              })}
            </div>
            {pipeline.current_phase === 'done' && (
              <p className="text-sm text-green-400 mt-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> {tr('wf.allPhasesComplete')}
              </p>
            )}
          </div>
        )}

        {/* Tasks + Team */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <ListTodo className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                {tr('wf.tasks')} ({taskCounts.done}/{tasks.length})
              </span>
              {tasks.length > 0 && <span className="text-xs text-gray-500 ml-auto">{tr('wf.clickToCycle')}</span>}
            </div>
            {tasks.length === 0 ? (
              <p className="text-sm text-gray-500">{tr('wf.noTasks')}</p>
            ) : (
              <ul className="space-y-1">
                {tasks.map(task => (
                  <li key={task.id}
                      onClick={e => { e.stopPropagation(); handleTaskToggle(wf.idea.id, task.id, task.status) }}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:bg-white/5 rounded px-1.5 py-1 transition-colors group">
                    {task.status === 'done' ? <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                      : task.status === 'in_progress' ? <Clock className="w-4 h-4 text-blue-400 shrink-0" />
                      : <Circle className="w-4 h-4 text-gray-600 group-hover:text-gray-400 shrink-0 transition-colors" />}
                    <span className={`truncate ${task.status === 'done' ? 'text-gray-500 line-through' : 'text-gray-300'}`}>{task.title}</span>
                    {task.assigned_agent && (
                      <span className="text-xs text-gray-500 ml-auto shrink-0">{tr(`agent.${task.assigned_agent}`) || task.assigned_agent}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                {tr('wf.team')} ({team?.members.length || 0})
              </span>
            </div>
            {!team || team.members.length === 0 ? (
              <p className="text-sm text-gray-500">{tr('wf.noTeam')}</p>
            ) : (
              <ul className="space-y-1">
                {team.members.map((m, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <span className={`w-2 h-2 rounded-full ${m.status === 'busy' ? 'bg-yellow-400' : 'bg-green-600'}`} />
                    <span className="text-gray-300">{tr(`agent.${m.role}`) || m.role}</span>
                    <span className="text-xs text-gray-500 ml-auto">{m.status}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Agent Workflow */}
        {wf.agent_workflow && wf.agent_workflow.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">{tr('wf.agentWorkflow')}</span>
              <span className="text-xs text-gray-500 ml-auto">
                {wf.agent_workflow.filter(a => a.status === 'done').length}/{wf.agent_workflow.length} {tr('wf.actionsComplete')}
              </span>
            </div>
            {(() => {
              const groups: { key: string; actions: AgentAction[]; isParallel: boolean }[] = []
              const seen = new Set<string>()
              const addAction = (action: AgentAction) => {
                if (seen.has(action.id)) return
                const pg = action.parallel_group
                if (pg) {
                  const pa = wf.agent_workflow!.filter(a => a.parallel_group === pg && !seen.has(a.id))
                  groups.push({ key: `pg-${pg}`, actions: pa, isParallel: true })
                  pa.forEach(a => seen.add(a.id))
                } else { groups.push({ key: action.id, actions: [action], isParallel: false }); seen.add(action.id) }
              }
              const remaining = [...wf.agent_workflow!]
              let prevLen = -1
              while (remaining.length > 0 && prevLen !== remaining.length) {
                prevLen = remaining.length
                for (let i = remaining.length - 1; i >= 0; i--) {
                  if (remaining[i].depends_on.every(d => seen.has(d)) || remaining[i].depends_on.length === 0) {
                    addAction(remaining[i]); remaining.splice(i, 1)
                  }
                }
              }
              remaining.forEach(a => addAction(a))

              return (
                <div className="space-y-3">
                  {groups.map(group => (
                    <div key={group.key}>
                      {group.isParallel && group.actions.length > 1 && (
                        <div className="text-xs text-purple-400 font-medium mb-1.5 flex items-center gap-2">
                          <span className="w-4 h-px bg-purple-500/50" />{tr('wf.parallelExecution')}<span className="w-4 h-px bg-purple-500/50" />
                        </div>
                      )}
                      <div className="grid gap-2"
                           style={{ gridTemplateColumns: group.actions.length === 2 ? 'repeat(2, 1fr)' : group.actions.length >= 3 ? 'repeat(3, 1fr)' : '1fr' }}>
                        {group.actions.map(action => {
                          const isDone = action.status === 'done'
                          const isActive = action.status === 'in_progress'
                          const isPending = action.status === 'pending'
                          return (
                            <div key={action.id}
                              className={`border rounded p-3 transition-all ${
                                isDone ? 'border-green-500/20 bg-green-500/5 opacity-80' :
                                isActive ? 'border-blue-500/30 bg-blue-500/5 ring-1 ring-blue-500/20' :
                                'border-white/5 bg-white/[0.02] opacity-50'
                              } ${agentColors[action.agent] || ''}`}>
                              <div className="flex items-center gap-2 mb-1.5">
                                <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                                  isDone ? 'bg-green-500' : isActive ? 'bg-blue-500 animate-pulse' : 'bg-gray-600'}`} />
                                <span className={`text-sm font-medium truncate ${isDone ? 'text-green-400' : isActive ? 'text-blue-400' : 'text-gray-400'}`}>
                                  {tr(`agent.${action.agent}`) || action.agent}
                                </span>
                                <span className={`text-xs px-1.5 py-0.5 rounded ml-auto shrink-0 ${
                                  isDone ? 'bg-green-500/20 text-green-400' : isActive ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-500'}`}>
                                  {isDone ? '✓' : isActive ? '▶' : '…'}
                                </span>
                              </div>
                              <p className={`text-sm font-medium mb-1 ${isPending ? 'text-gray-500' : 'text-gray-200'}`}>{action.title}</p>
                              <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">{action.description}</p>
                              <div className="mt-2 pt-2 border-t border-white/5 space-y-1">
                                {action.inputs.length > 0 && (
                                  <div className="text-xs text-gray-500">
                                    <span className="text-gray-600">IN:</span> {action.inputs.slice(0, 2).join(', ')}{action.inputs.length > 2 ? ` +${action.inputs.length - 2}` : ''}
                                  </div>
                                )}
                                {action.outputs.length > 0 && (
                                  <div className="text-xs text-gray-500">
                                    <span className="text-gray-600">OUT:</span> {action.outputs.slice(0, 2).join(', ')}{action.outputs.length > 2 ? ` +${action.outputs.length - 2}` : ''}
                                  </div>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center gap-4 pt-2 border-t border-white/5 text-xs text-gray-500">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-green-500" /> {tr('wf.done')}</span>
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" /> {tr('wf.inProgress')}</span>
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-gray-600" /> {tr('wf.pending')}</span>
                    <span className="flex items-center gap-1.5 ml-auto"><span className="text-purple-400">{tr('wf.parallelExecution')}</span></span>
                  </div>
                </div>
              )
            })()}
          </div>
        )}

        {/* Deliverables */}
        {(() => {
          const dl = deliverables[wf.idea.id]
          if (!dl || dl.length === 0) return null
          return (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">{tr('wf.deliverables')} ({dl.length})</span>
              </div>
              <ul className="space-y-1.5">
                {dl.map((d: any, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-sm border border-[hsl(var(--border))] rounded p-2.5 bg-white/5">
                    <FileText className="w-4 h-4 text-blue-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-gray-300">{d.name}</span>
                      <span className="text-gray-500 ml-2">{(d.size / 1024).toFixed(1)} KB · {new Date(d.modified).toLocaleDateString()}</span>
                      {d.preview && <p className="text-gray-500 text-xs truncate mt-0.5">{d.preview.slice(0, 120)}...</p>}
                    </div>
                    <a href={`/api/ideas/${wf.idea.id}/deliverables/${encodeURIComponent(d.name)}/html`}
                       target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                       className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/30 hover:bg-blue-500/50 rounded text-sm font-medium transition-colors shrink-0 no-underline text-blue-300">
                      <Download className="w-4 h-4" />{tr('wf.view')}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )
        })()}
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-3xl font-bold mb-6">{tr('idea.title')}</h2>

      {/* New Idea Form */}
      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-6 h-6 text-yellow-400" />
          <h3 className="text-xl font-semibold">{tr('idea.newIdea')}</h3>
        </div>
        <p className="text-base text-gray-400 mb-4">{tr('idea.newIdeaHint')}</p>

        <input type="text" placeholder={tr('idea.titlePlaceholder')}
          className="w-full border border-[hsl(var(--border))] rounded p-3 mb-3 bg-black/30 text-base focus:outline-none focus:border-blue-500"
          value={title} onChange={e => setTitle(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
        <textarea placeholder={tr('idea.descPlaceholder')}
          className="w-full border border-[hsl(var(--border))] rounded p-3 mb-3 bg-black/30 text-base focus:outline-none focus:border-blue-500"
          rows={5} value={description} onChange={e => setDescription(e.target.value)} />
        <input type="text" placeholder={tr('idea.tagsPlaceholder')}
          className="w-full border border-[hsl(var(--border))] rounded p-3 mb-4 bg-black/30 text-base focus:outline-none focus:border-blue-500"
          value={tags} onChange={e => setTags(e.target.value)} />

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-base mb-3">
            <AlertCircle className="w-5 h-5" />{error}
          </div>
        )}
        <button onClick={handleSubmit} disabled={!title.trim() || loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded text-base font-medium transition-colors">
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          {loading ? tr('idea.submitting') : tr('idea.submit')}
        </button>
      </div>

      {/* Recent Ideas */}
      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5">
        <h3 className="text-xl font-semibold mb-3">{tr('idea.recent')}</h3>
        {loadingIdeas ? (
          <div className="flex items-center gap-2 text-base text-gray-400"><Loader2 className="w-5 h-5 animate-spin" />{tr('idea.loading')}</div>
        ) : ideas.length === 0 ? (
          <p className="text-base text-gray-500">{tr('idea.empty')}</p>
        ) : (
          <ul className="space-y-3">
            {ideas.map(idea => {
              const wf = workflows[idea.id]
              const showWorkflow = expanded === idea.id && wf && wf.pipeline
              return (
                <li key={idea.id}>
                  <div onClick={() => handleToggleExpand(idea.id)}
                       className="border border-[hsl(var(--border))] rounded p-4 bg-white/5 hover:bg-white/10 transition-colors cursor-pointer">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-medium text-base truncate mr-2">{idea.title}</span>
                      <span className={`text-sm px-2 py-0.5 rounded-full shrink-0 ${statusColors[idea.status] || 'bg-gray-500/20 text-gray-400'}`}>
                        {tr(`status.${idea.status}`) || idea.status}
                      </span>
                    </div>
                    {idea.raw_description && <p className="text-sm text-gray-400 line-clamp-2 mb-2">{idea.raw_description}</p>}
                    <div className="flex items-center gap-2 flex-wrap">
                      {idea.tags?.map(tag => <span key={tag} className="text-sm px-1.5 py-0.5 bg-white/10 rounded text-gray-400">{tag}</span>)}
                      {idea.suggested_pipeline && (
                        <span className="text-sm text-blue-400">{tr(`pipeline.${idea.suggested_pipeline}`) || idea.suggested_pipeline}</span>
                      )}
                      {wf?.pipeline && <span className="text-sm text-green-400 ml-auto">{tr('wf.phase')}: {wf.pipeline.current_phase}</span>}
                      <span className="text-sm text-gray-500 ml-auto">
                        {expanded === idea.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </span>
                    </div>
                  </div>

                  {/* Meta (no pipeline yet) */}
                  {expanded === idea.id && !showWorkflow && (
                    <div className="border border-t-0 border-[hsl(var(--border))] rounded-b p-5 bg-white/[0.03] -mt-px space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-base">
                        <div><span className="text-gray-500">{tr('general.status')}</span>
                          <p className="text-white">{tr(`status.${idea.status}`) || idea.status}</p></div>
                        <div><span className="text-gray-500">{tr('general.pipeline')}</span>
                          <p className="text-white">{idea.suggested_pipeline ? (tr(`pipeline.${idea.suggested_pipeline}`) || idea.suggested_pipeline) : tr('general.notDetermined')}</p></div>
                        <div className="col-span-2"><span className="text-gray-500">{tr('general.description')}</span>
                          <p className="text-white whitespace-pre-wrap text-base mt-1">{idea.raw_description || '(empty)'}</p></div>
                        <div><span className="text-gray-500">{tr('general.created')}</span>
                          <p className="text-white text-sm">{new Date(idea.created_at).toLocaleString()}</p></div>
                        <div><span className="text-gray-500">{tr('general.id')}</span>
                          <p className="text-white text-sm font-mono">{idea.id.slice(0, 8)}…</p></div>
                      </div>
                      <div className="flex gap-2">
                        {idea.status === 'new' && (
                          <button onClick={e => { e.stopPropagation(); handleRefine(idea.id) }} disabled={refiningId === idea.id}
                            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-40 rounded text-sm font-medium transition-colors">
                            {refiningId === idea.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                            {refiningId === idea.id ? tr('idea.refining') : tr('idea.refine')}
                          </button>
                        )}
                        {idea.status === 'refining' && idea.suggested_pipeline && (
                          <button onClick={e => { e.stopPropagation(); handleStart(idea.id) }} disabled={startingId === idea.id}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded text-sm font-medium transition-colors">
                            {startingId === idea.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            {startingId === idea.id ? tr('idea.starting') : tr('idea.start')}
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Full Workflow */}
                  {showWorkflow && renderWorkflow(wf)}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
