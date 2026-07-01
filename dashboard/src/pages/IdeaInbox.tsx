import { useState, useEffect } from 'react'
import {
  Lightbulb, Send, Loader2, AlertCircle, ChevronDown, ChevronUp,
  Sparkles, Play, CheckCircle2, Circle, Clock, Users, ListTodo,
  ArrowRight, TrendingUp, FileText, Download,
} from 'lucide-react'
import { api } from '../api/client'

interface Idea {
  id: string
  title: string
  raw_description: string
  refined_description: string | null
  tags: string[]
  status: string
  suggested_pipeline: string | null
  created_at: string
}

interface WorkflowStep {
  phase: string
  name: string
  agent: string
  status: string
}

interface WorkflowTask {
  id: string
  title: string
  status: string
  priority: string
  assigned_agent: string | null
}

interface WorkflowMember {
  role: string
  status: string
}

interface WorkflowState {
  idea: Idea
  pipeline: {
    id: string
    pipeline_type: string
    current_phase: string
    steps: WorkflowStep[]
  } | null
  tasks: WorkflowTask[]
  team: {
    id: string
    name: string
    members: WorkflowMember[]
  } | null
}

const PHASE_ORDER = ['idea', 'requirements', 'design', 'implementation', 'testing', 'deploy', 'done']

const statusColors: Record<string, string> = {
  new: 'bg-blue-500/20 text-blue-400',
  refining: 'bg-yellow-500/20 text-yellow-400',
  approved: 'bg-green-500/20 text-green-400',
  rejected: 'bg-red-500/20 text-red-400',
  in_progress: 'bg-purple-500/20 text-purple-400',
  done: 'bg-emerald-500/20 text-emerald-400',
}

const statusLabels: Record<string, string> = {
  new: 'New', refining: 'Refining', approved: 'Approved',
  rejected: 'Rejected', in_progress: 'In Progress', done: 'Done',
}

const taskStatusIcons: Record<string, React.ReactNode> = {
  done: null,
  todo: null,
  in_progress: null,
}

const pipelineLabels: Record<string, string> = {
  'embedded-firmware': 'Embedded Firmware Pipeline',
  'embedded-linux': 'Embedded Linux Pipeline',
  'web-fullstack': 'Web Fullstack Pipeline',
  'quick-prototype': 'Quick Prototype',
  'research-spike': 'Research / Analysis',
}

const agentNames: Record<string, string> = {
  'embedded-firmware-engineer': 'Firmware Engineer',
  'embedded-hardware-engineer': 'Hardware Engineer',
  'embedded-linux-engineer': 'Linux Engineer',
  'embedded-iot-engineer': 'IoT Engineer',
  'embedded-sensor-driver-dev': 'Sensor Driver Dev',
  'embedded-testing-engineer': 'Testing Engineer',
  'software-architect': 'Software Architect',
  'backend-developer': 'Backend Developer',
  'frontend-developer': 'Frontend Developer',
  'fullstack-developer': 'Fullstack Developer',
  'devops-engineer': 'DevOps Engineer',
  'security-engineer': 'Security Engineer',
  'tech-lead': 'Tech Lead',
  'project-manager': 'Project Manager',
  'code-reviewer': 'Code Reviewer',
  'qa-engineer': 'QA Engineer',
  'technical-writer': 'Technical Writer',
  'idea-refiner': 'Idea Refiner',
  'rapid-prototyper': 'Rapid Prototyper',
}

export default function IdeaInbox() {
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
      const list = Array.isArray(data) ? data : (data as any).ideas || []
      setIdeas(list)
    } catch {
      // silently fail
    } finally {
      setLoadingIdeas(false)
    }
  }

  useEffect(() => {
    fetchIdeas()
  }, [])

  const handleSubmit = async () => {
    if (!title.trim()) return
    setLoading(true)
    setError('')
    try {
      await api.ideas.create({
        title: title.trim(),
        raw_description: description.trim(),
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      })
      setTitle('')
      setDescription('')
      setTags('')
      await fetchIdeas()
    } catch (e: any) {
      setError(e.message || 'Failed to submit idea')
    } finally {
      setLoading(false)
    }
  }

  const handleRefine = async (ideaId: string) => {
    setRefiningId(ideaId)
    try {
      const refined = await api.ideas.refine(ideaId)
      setIdeas(prev => prev.map(i => (i.id === ideaId ? refined : i)))
    } catch { /* ignore */ }
    finally { setRefiningId(null) }
  }

  const handleStart = async (ideaId: string) => {
    setStartingId(ideaId)
    try {
      const wf = await api.ideas.start(ideaId)
      setWorkflows(prev => ({ ...prev, [ideaId]: wf }))
      setIdeas(prev => prev.map(i => (i.id === ideaId ? wf.idea : i)))
    } catch { /* ignore */ }
    finally { setStartingId(null) }
  }

  const handleTaskToggle = async (ideaId: string, taskId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'todo' ? 'in_progress'
      : currentStatus === 'in_progress' ? 'done'
      : 'todo'
    try {
      await api.tasks.updateStatus(taskId, nextStatus)
      // Refresh workflow
      const wf = await api.ideas.workflow(ideaId)
      setWorkflows(prev => ({ ...prev, [ideaId]: wf }))
    } catch { /* ignore */ }
  }

  const handleAdvancePhase = async (ideaId: string, pipelineId: string) => {
    try {
      await api.pipelines.advance(pipelineId)
      const wf = await api.ideas.workflow(ideaId)
      setWorkflows(prev => ({ ...prev, [ideaId]: wf }))
    } catch { /* ignore */ }
  }

  const handleToggleExpand = async (ideaId: string) => {
    if (expanded === ideaId) {
      setExpanded(null)
      return
    }
    setExpanded(ideaId)

    // Fetch workflow if not cached
    if (!workflows[ideaId]) {
      try {
        const wf = await api.ideas.workflow(ideaId)
        setWorkflows(prev => ({ ...prev, [ideaId]: wf }))
      } catch { /* ignore */ }
    }
    // Fetch deliverables
    if (!deliverables[ideaId]) {
      try {
        const d = await api.ideas.deliverables(ideaId)
        setDeliverables(prev => ({ ...prev, [ideaId]: d }))
      } catch { /* ignore */ }
    }
  }

  const renderWorkflow = (wf: WorkflowState) => {
    const { pipeline, tasks, team } = wf
    const currentIdx = pipeline
      ? PHASE_ORDER.indexOf(pipeline.current_phase)
      : -1
    const totalPhases = pipeline?.steps.length || 1

    const taskCounts = { todo: 0, in_progress: 0, done: 0 }
    tasks.forEach(t => { if (t.status in taskCounts) taskCounts[t.status as keyof typeof taskCounts]++ })

    // Overall progress: 70% pipeline + 30% tasks
    const phasePct = totalPhases > 0 ? Math.round((currentIdx / totalPhases) * 100) : 0
    const taskPct = tasks.length > 0 ? Math.round((taskCounts.done / tasks.length) * 100) : 0
    const overallPct = tasks.length > 0
      ? Math.round(phasePct * 0.7 + taskPct * 0.3)
      : phasePct
    const isComplete = overallPct >= 100

    return (
      <div className="border border-t-0 border-[hsl(var(--border))] rounded-b p-4 bg-white/[0.03] -mt-px space-y-4">
        {/* ── Overall Progress ──────────────────────────────────── */}
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Overall Progress
              </span>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-bold ${isComplete ? 'text-green-400' : 'text-blue-400'}`}>
                  {overallPct}%
                </span>
                {isComplete && <CheckCircle2 className="w-4 h-4 text-green-400" />}
              </div>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isComplete ? 'bg-green-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}
                style={{ width: `${overallPct}%` }}
              />
            </div>
          </div>
          {pipeline && (
            <button
              onClick={e => { e.stopPropagation(); handleAdvancePhase(wf.idea.id, pipeline.id) }}
              disabled={pipeline.current_phase === 'done'}
              className="flex items-center gap-1 px-2 py-1 bg-blue-600/50 hover:bg-blue-500 disabled:opacity-30 rounded text-[10px] font-medium transition-colors shrink-0"
              title="Advance to next phase"
            >
              <ArrowRight className="w-3 h-3" />
              Next Phase
            </button>
          )}
        </div>

        {/* ── Pipeline Progress ─────────────────────────────────── */}
        {pipeline && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Pipeline: {pipelineLabels[pipeline.pipeline_type] || pipeline.pipeline_type}
              </span>
              <span className="text-xs text-gray-500">
                Phase {currentIdx + 1}/{totalPhases}: {pipeline.current_phase.toUpperCase()}
              </span>
            </div>
            <div className="flex gap-1">
              {pipeline.steps.map((step, i) => {
                const idx = PHASE_ORDER.indexOf(step.phase)
                const isDone = idx < currentIdx
                const isCurrent = idx === currentIdx
                return (
                  <div key={i} className="flex-1 group relative">
                    <div
                      className={`h-1.5 rounded-full transition-colors ${
                        isDone ? 'bg-green-500' : isCurrent ? 'bg-blue-500 animate-pulse' : 'bg-white/10'
                      }`}
                      title={`${step.phase}: ${step.name} — ${agentNames[step.agent] || step.agent}`}
                    />
                  </div>
                )
              })}
            </div>
            <div className="flex justify-between mt-1.5">
              {pipeline.steps.map((step, i) => {
                const idx = PHASE_ORDER.indexOf(step.phase)
                const isDone = idx < currentIdx
                const isCurrent = idx === currentIdx
                return (
                  <div key={i} className="text-[10px] text-gray-500 truncate max-w-[60px] text-center"
                       title={`${step.name}\nAgent: ${agentNames[step.agent] || step.agent}`}>
                    {isDone ? '✓' : isCurrent ? '●' : ''} {step.name}
                  </div>
                )
              })}
            </div>
            {pipeline.current_phase === 'done' && (
              <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> All phases complete!
              </p>
            )}
          </div>
        )}

        {/* ── Tasks + Team ───────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          {/* Tasks — clickable to toggle */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <ListTodo className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Tasks ({taskCounts.done}/{tasks.length})
              </span>
              {tasks.length > 0 && (
                <span className="text-[10px] text-gray-500 ml-auto">
                  click to cycle
                </span>
              )}
            </div>
            {tasks.length === 0 ? (
              <p className="text-xs text-gray-500">No tasks yet</p>
            ) : (
              <ul className="space-y-1">
                {tasks.map(task => (
                  <li
                    key={task.id}
                    onClick={e => { e.stopPropagation(); handleTaskToggle(wf.idea.id, task.id, task.status) }}
                    className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-white/5 rounded px-1 py-0.5 transition-colors group"
                    title="Click to toggle: todo → in_progress → done → todo"
                  >
                    {task.status === 'done' ? (
                      <CheckCircle2 className="w-3 h-3 text-green-400 shrink-0" />
                    ) : task.status === 'in_progress' ? (
                      <Clock className="w-3 h-3 text-blue-400 shrink-0" />
                    ) : (
                      <Circle className="w-3 h-3 text-gray-600 group-hover:text-gray-400 shrink-0 transition-colors" />
                    )}
                    <span className={`truncate ${task.status === 'done' ? 'text-gray-500 line-through' : 'text-gray-300'}`}>
                      {task.title}
                    </span>
                    {task.assigned_agent && (
                      <span className="text-[10px] text-gray-500 ml-auto shrink-0">
                        {agentNames[task.assigned_agent] || task.assigned_agent}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Team */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Users className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Team ({team?.members.length || 0})
              </span>
            </div>
            {!team || team.members.length === 0 ? (
              <p className="text-xs text-gray-500">No team assigned</p>
            ) : (
              <ul className="space-y-1">
                {team.members.map((m, i) => (
                  <li key={i} className="flex items-center gap-1.5 text-xs">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      m.status === 'busy' ? 'bg-yellow-400' : 'bg-green-600'
                    }`} />
                    <span className="text-gray-300">
                      {agentNames[m.role] || m.role}
                    </span>
                    <span className="text-[10px] text-gray-500 ml-auto">{m.status}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* ── Deliverables ──────────────────────────────────────── */}
        {(() => {
          const ideaDeliverables = deliverables[wf.idea.id]
          if (!ideaDeliverables || ideaDeliverables.length === 0) return null
          return (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <FileText className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                  Deliverables ({ideaDeliverables.length})
                </span>
              </div>
              <ul className="space-y-1">
                {ideaDeliverables.map((d: any, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-xs border border-[hsl(var(--border))] rounded p-2 bg-white/5">
                    <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-gray-300">{d.name}</span>
                      <span className="text-gray-500 ml-2">
                        {(d.size / 1024).toFixed(1)} KB · {new Date(d.modified).toLocaleDateString()}
                      </span>
                      {d.preview && (
                        <p className="text-gray-500 text-[10px] truncate mt-0.5">{d.preview.slice(0, 120)}...</p>
                      )}
                    </div>
                    <a
                      href={`/api/ideas/${wf.idea.id}/deliverables/${encodeURIComponent(d.name)}/html`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={e => e.stopPropagation()}
                      className="flex items-center gap-1 px-2 py-1 bg-blue-600/30 hover:bg-blue-500/50 rounded text-[10px] font-medium transition-colors shrink-0 no-underline text-blue-300"
                    >
                      <Download className="w-3 h-3" />
                      View
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
      <h2 className="text-2xl font-bold mb-6">Idea Inbox</h2>

      {/* ── New Idea Form ─────────────────────────────────────────────── */}
      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold">New Idea</h3>
        </div>

        <p className="text-sm text-gray-400 mb-4">
          Describe your idea — it can be vague. The Idea Refiner will expand it into requirements.
        </p>

        <input
          type="text"
          placeholder="Idea title (e.g., M5Stack 溫濕度監測器)"
          className="w-full border border-[hsl(var(--border))] rounded p-2 mb-3 bg-black/30 text-sm focus:outline-none focus:border-blue-500"
          value={title}
          onChange={e => setTitle(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
        />

        <textarea
          placeholder="Describe your idea..."
          className="w-full border border-[hsl(var(--border))] rounded p-2 mb-3 bg-black/30 text-sm focus:outline-none focus:border-blue-500"
          rows={5}
          value={description}
          onChange={e => setDescription(e.target.value)}
        />

        <input
          type="text"
          placeholder="Tags (comma-separated): m5stack, sensor, iot"
          className="w-full border border-[hsl(var(--border))] rounded p-2 mb-4 bg-black/30 text-sm focus:outline-none focus:border-blue-500"
          value={tags}
          onChange={e => setTags(e.target.value)}
        />

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm mb-3">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!title.trim() || loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded text-sm font-medium transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {loading ? 'Submitting...' : 'Submit Idea'}
        </button>
      </div>

      {/* ── Recent Ideas List ─────────────────────────────────────────── */}
      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5">
        <h3 className="text-lg font-semibold mb-3">Recent Ideas</h3>

        {loadingIdeas ? (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading...
          </div>
        ) : ideas.length === 0 ? (
          <p className="text-sm text-gray-500">
            No ideas yet. Submit your first idea above.
          </p>
        ) : (
          <ul className="space-y-3">
            {ideas.map(idea => {
              const wf = workflows[idea.id]
              const showWorkflow = expanded === idea.id && wf && wf.pipeline

              return (
                <li key={idea.id}>
                  <div
                    onClick={() => handleToggleExpand(idea.id)}
                    className="border border-[hsl(var(--border))] rounded p-3 bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm truncate mr-2">{idea.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${statusColors[idea.status] || 'bg-gray-500/20 text-gray-400'}`}>
                        {statusLabels[idea.status] || idea.status}
                      </span>
                    </div>
                    {idea.raw_description && (
                      <p className="text-xs text-gray-400 line-clamp-2 mb-2">{idea.raw_description}</p>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      {idea.tags?.map(tag => (
                        <span key={tag} className="text-xs px-1.5 py-0.5 bg-white/10 rounded text-gray-400">{tag}</span>
                      ))}
                      {idea.suggested_pipeline && (
                        <span className="text-xs text-blue-400">
                          {pipelineLabels[idea.suggested_pipeline] || idea.suggested_pipeline}
                        </span>
                      )}
                      {/* Workflow mini-indicator */}
                      {wf?.pipeline && (
                        <span className="text-xs text-green-400 ml-auto">
                          Phase: {wf.pipeline.current_phase}
                        </span>
                      )}
                      <span className="text-xs text-gray-500 ml-auto">
                        {expanded === idea.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </span>
                    </div>
                  </div>

                  {/* Expanded: Meta */}
                  {expanded === idea.id && !showWorkflow && (
                    <div className="border border-t-0 border-[hsl(var(--border))] rounded-b p-4 bg-white/[0.03] -mt-px space-y-3">
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Status</span>
                          <p className="text-white">{statusLabels[idea.status] || idea.status}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Pipeline</span>
                          <p className="text-white">
                            {idea.suggested_pipeline
                              ? pipelineLabels[idea.suggested_pipeline] || idea.suggested_pipeline
                              : 'Not yet determined'}
                          </p>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-500">Description</span>
                          <p className="text-white whitespace-pre-wrap text-sm mt-1">
                            {idea.raw_description || '(empty)'}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">Created</span>
                          <p className="text-white text-xs">{new Date(idea.created_at).toLocaleString()}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">ID</span>
                          <p className="text-white text-xs font-mono">{idea.id.slice(0, 8)}…</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {idea.status === 'new' && (
                          <button
                            onClick={e => { e.stopPropagation(); handleRefine(idea.id) }}
                            disabled={refiningId === idea.id}
                            className="flex items-center gap-2 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-40 rounded text-xs font-medium transition-colors"
                          >
                            {refiningId === idea.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                            {refiningId === idea.id ? 'Refining...' : 'Refine Idea'}
                          </button>
                        )}
                        {idea.status === 'refining' && idea.suggested_pipeline && (
                          <button
                            onClick={e => { e.stopPropagation(); handleStart(idea.id) }}
                            disabled={startingId === idea.id}
                            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded text-xs font-medium transition-colors"
                          >
                            {startingId === idea.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                            {startingId === idea.id ? 'Starting...' : 'Start Pipeline'}
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Expanded: Full Workflow */}
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
