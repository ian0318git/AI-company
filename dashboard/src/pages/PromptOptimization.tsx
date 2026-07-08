import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Zap, TrendingDown, FlaskConical, BarChart3, Lightbulb, CheckCircle2, Clock, Cpu, Plus, Sparkles, Trash2 } from 'lucide-react'

interface Template {
  id: string
  agent_role: string
  pipeline_type: string
  template_name: string
  template_body: string
  token_count: number
  version: number
  status: string
  avg_tokens: number
  avg_seconds: number
  use_count: number
  created_at: string
}

interface RoiData {
  total_results: number
  avg_tokens_per_task: number
  avg_seconds_per_task: number
  estimated_savings: Record<string, number | string>
  template_performance: Array<{
    template_id: string
    template_name: string
    task_count: number
    avg_tokens: number
    avg_seconds: number
  }>
  experiment_count: number
}

interface Experiment {
  id: string
  experiment_name: string
  target_agent_role: string
  status: string
  control_total: number
  control_avg_tokens: number
  control_avg_seconds: number
  variant_total: number
  variant_avg_tokens: number
  variant_avg_seconds: number
  winner: string | null
  confidence: number | null
}

interface Insight {
  id: string
  agent_role: string
  finding: string
  effect_size: number
  confidence: number
  recommendation: string
  source_task_count: number
}

export default function PromptOptimization() {
  const [roi, setRoi] = useState<RoiData | null>(null)
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [insights, setInsights] = useState<Insight[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [newTemplate, setNewTemplate] = useState({
    agent_role: 'backend-developer',
    template_name: '',
    template_body: '',
  })

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      const [roiRes, expRes, insRes, tmplRes] = await Promise.all([
        api.prompts.roi().catch(() => null),
        api.prompts.experiments.list().catch(() => []),
        api.prompts.insights.list().catch(() => []),
        api.prompts.templates.list().catch(() => []),
      ])
      setRoi(roiRes)
      setExperiments(expRes || [])
      setInsights(insRes || [])
      setTemplates(tmplRes || [])
    } catch (e) {
      setError('Failed to load prompt optimization data')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateTemplate() {
    if (!newTemplate.template_name || !newTemplate.template_body) return
    try {
      await api.prompts.templates.create({
        agent_role: newTemplate.agent_role,
        template_name: newTemplate.template_name,
        template_body: newTemplate.template_body,
        token_count: newTemplate.template_body.split(/\s+/).length,
      })
      setShowCreateForm(false)
      setNewTemplate({ agent_role: 'backend-developer', template_name: '', template_body: '' })
      fetchData()
    } catch { /* ignore */ }
  }

  async function handleGenerateInsights() {
    setGenerating(true)
    try {
      await api.prompts.insights.generate()
      fetchData()
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Prompt Optimization Engine</h1>
            <p className="text-gray-400 mt-1">Loading data-driven insights...</p>
          </div>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-800 rounded-xl" />
          <div className="h-48 bg-gray-800 rounded-xl" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Zap className="w-6 h-6 text-yellow-400" />
            Prompt Optimization Engine
          </h1>
          <p className="text-gray-400 mt-1">
            Data-driven prompt engineering from 169 completed task records
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            v1 (MVP)
          </span>
          <button
            onClick={fetchData}
            className="px-3 py-1.5 text-sm bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm">
          {error}
        </div>
      )}

      {/* ROI Summary Cards */}
      {roi && roi.total_results > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700/50">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <BarChart3 className="w-4 h-4" />
              Results Collected
            </div>
            <div className="text-2xl font-bold">{roi.total_results}</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700/50">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <Cpu className="w-4 h-4" />
              Avg Tokens/Task
            </div>
            <div className="text-2xl font-bold">{roi.avg_tokens_per_task}</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700/50">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <TrendingDown className="w-4 h-4" />
              Est. Savings
            </div>
            <div className="text-2xl font-bold text-green-400">{roi.estimated_savings?.savings_percent || '15% target'}</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700/50">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <FlaskConical className="w-4 h-4" />
              Experiments
            </div>
            <div className="text-2xl font-bold">{roi.experiment_count}</div>
          </div>
        </div>
      )}

      {/* Template Performance */}
      {roi && roi.template_performance && roi.template_performance.length > 0 && (
        <div className="rounded-xl bg-gray-800/30 border border-gray-700/50 p-5">
          <h2 className="text-lg font-semibold mb-4">Template Performance Rankings</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700/50">
                  <th className="text-left py-2 pr-4">Template</th>
                  <th className="text-right py-2 px-4">Tasks</th>
                  <th className="text-right py-2 px-4">Avg Tokens</th>
                  <th className="text-right py-2 px-4">Avg Time (s)</th>
                  <th className="text-right py-2 px-4">Efficiency</th>
                </tr>
              </thead>
              <tbody>
                {roi.template_performance.map((t, i) => (
                  <tr key={t.template_id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                    <td className="py-2 pr-4 flex items-center gap-2">
                      {i === 0 && <Zap className="w-3 h-3 text-yellow-400" />}
                      <span className={i === 0 ? 'text-green-400 font-medium' : ''}>
                        {t.template_name?.substring(0, 30) || t.template_id.substring(0, 8)}
                      </span>
                    </td>
                    <td className="text-right py-2 px-4">{t.task_count}</td>
                    <td className="text-right py-2 px-4 font-mono">{t.avg_tokens}</td>
                    <td className="text-right py-2 px-4 font-mono">{t.avg_seconds}</td>
                    <td className="text-right py-2 px-4">
                      {i === 0 ? (
                        <span className="text-green-400 text-xs bg-green-400/10 px-2 py-0.5 rounded-full">
                          Best
                        </span>
                      ) : (
                        <span className="text-gray-500 text-xs">
                          {roi.template_performance[0].avg_tokens > 0
                            ? `${Math.round((t.avg_tokens / roi.template_performance[0].avg_tokens - 1) * 100)}% more`
                            : '-'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Template Management */}
      <div className="rounded-xl bg-gray-800/30 border border-gray-700/50 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            Prompt Templates
          </h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-cyan-600/20 text-cyan-400 rounded-lg hover:bg-cyan-600/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Template
          </button>
        </div>

        {showCreateForm && (
          <div className="mb-4 p-4 rounded-lg bg-gray-800/40 border border-gray-700/30 space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Agent Role</label>
              <select
                value={newTemplate.agent_role}
                onChange={e => setNewTemplate(p => ({ ...p, agent_role: e.target.value }))}
                className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-gray-200"
              >
                <option value="backend-developer">backend-developer</option>
                <option value="frontend-developer">frontend-developer</option>
                <option value="fullstack-developer">fullstack-developer</option>
                <option value="software-architect">software-architect</option>
                <option value="qa-engineer">qa-engineer</option>
                <option value="devops-engineer">devops-engineer</option>
                <option value="tech-lead">tech-lead</option>
                <option value="technical-writer">technical-writer</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Template Name</label>
              <input
                type="text"
                value={newTemplate.template_name}
                onChange={e => setNewTemplate(p => ({ ...p, template_name: e.target.value }))}
                placeholder="e.g. FastAPI endpoint boilerplate"
                className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-gray-200"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Template Body</label>
              <textarea
                value={newTemplate.template_body}
                onChange={e => setNewTemplate(p => ({ ...p, template_body: e.target.value }))}
                placeholder="You are a {role}. Build a {feature} with..."
                rows={4}
                className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-gray-200 font-mono"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTemplate}
                disabled={!newTemplate.template_name || !newTemplate.template_body}
                className="px-3 py-1.5 text-sm bg-cyan-600/30 text-cyan-300 rounded-lg hover:bg-cyan-600/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Create Template
              </button>
            </div>
          </div>
        )}

        {templates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No templates yet. Create your first prompt template.</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {templates.map(t => (
              <div key={t.id} className="p-3 rounded-lg bg-gray-800/20 border border-gray-700/30 text-sm flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${t.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`} />
                  <div>
                    <span className="text-gray-200 font-medium">{t.template_name}</span>
                    <span className="text-gray-500 ml-2 text-xs">{t.agent_role}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>v{t.version}</span>
                  <span>{t.use_count} uses</span>
                  <span>{t.token_count} tok</span>
                  {t.avg_tokens > 0 && (
                    <span className="text-green-400">{t.avg_tokens.toFixed(0)} avg tok</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* A/B Test Experiments */}
      <div className="rounded-xl bg-gray-800/30 border border-gray-700/50 p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FlaskConical className="w-5 h-5 text-purple-400" />
          A/B Test Experiments
        </h2>
        {experiments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FlaskConical className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No experiments yet. Create one to start comparing prompt templates.</p>
            <p className="text-xs mt-1">POST /api/prompts/experiments to begin A/B testing</p>
          </div>
        ) : (
          <div className="space-y-3">
            {experiments.map(exp => (
              <div key={exp.id} className="p-4 rounded-lg bg-gray-800/20 border border-gray-700/30">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      exp.status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-blue-500'
                    }`} />
                    <span className="font-medium">{exp.experiment_name}</span>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    exp.status === 'running' ? 'bg-green-400/10 text-green-400' : 'bg-blue-400/10 text-blue-400'
                  }`}>
                    {exp.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400 mb-1">Control ({exp.control_total} tasks)</div>
                    <div className="text-xs text-gray-500">
                      {exp.control_avg_tokens} tokens · {exp.control_avg_seconds}s avg
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-400 mb-1">Variant ({exp.variant_total} tasks)</div>
                    <div className="text-xs text-gray-500">
                      {exp.variant_avg_tokens} tokens · {exp.variant_avg_seconds}s avg
                    </div>
                  </div>
                </div>
                {exp.winner && (
                  <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Winner: {exp.winner} (confidence: {exp.confidence ? `${Math.round(exp.confidence * 100)}%` : 'N/A'})
                  </div>
                )}
                <div className="mt-2 text-xs text-gray-500">
                  Agent: {exp.target_agent_role}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Optimization Insights */}
      <div className="rounded-xl bg-gray-800/30 border border-gray-700/50 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-400" />
            Data-Driven Insights
          </h2>
          <button
            onClick={handleGenerateInsights}
            disabled={generating}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-yellow-600/20 text-yellow-400 rounded-lg hover:bg-yellow-600/30 disabled:opacity-50 transition-colors"
          >
            <Sparkles className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Generating...' : 'Generate Insights'}
          </button>
        </div>
        {insights.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No insights yet. Collect prompt results then click "Generate Insights".</p>
          </div>
        ) : (
          <div className="space-y-3">
            {insights.map(insight => (
              <div key={insight.id} className="p-4 rounded-lg bg-gray-800/20 border border-gray-700/30">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="font-medium text-yellow-400">{insight.agent_role}</span>
                    <p className="text-sm text-gray-300 mt-1">{insight.finding}</p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Confidence</div>
                      <div className="text-sm font-mono">{Math.round(insight.confidence * 100)}%</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Effect</div>
                      <div className="text-sm font-mono">{insight.effect_size > 0 ? '+' : ''}{Math.round(insight.effect_size * 100)}%</div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Recommendation: {insight.recommendation}</span>
                  <span>{insight.source_task_count} tasks analyzed</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Getting Started */}
      <div className="rounded-xl bg-gradient-to-r from-blue-500/5 to-purple-500/5 border border-blue-500/20 p-5">
        <h2 className="text-lg font-semibold mb-2">Getting Started</h2>
        <ol className="list-decimal list-inside text-sm text-gray-400 space-y-1.5">
          <li>Create a prompt template: <code className="text-blue-400">POST /api/prompts/templates</code></li>
          <li>Start an A/B experiment: <code className="text-blue-400">POST /api/prompts/experiments</code></li>
          <li>Log results after each task: <code className="text-blue-400">POST /api/prompts/results</code></li>
          <li>Generate insights: <code className="text-blue-400">POST /api/prompts/insights/generate</code></li>
          <li>Auto-inject optimized prompts via <code className="text-blue-400">GET /api/prompts/optimized</code></li>
        </ol>
      </div>
    </div>
  )
}
