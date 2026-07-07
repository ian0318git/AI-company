import { useState, useEffect } from 'react'
import { Shield, FlaskConical, Microscope, TrendingUp, Loader2, CheckCircle2, AlertTriangle, Lightbulb } from 'lucide-react'
import { api } from '../api/client'
import { useI18n } from '../i18n/context'

interface EvoStatus {
  failures: { total: number; analyzed: number; high_frequency_patterns: number; by_category: Record<string, number>; antibodies_active: number; vaccines_active: number }
  research: { total_findings: number; accepted: number; conversion_rate: string }
  evolution_health: string
}

interface Failure {
  id: string; title: string; category: string; severity: string; frequency: number
  status: string; root_cause: string; antibody: string; vaccine: string; catalyst: string
  created_at: string
}

interface ResearchItem {
  id: string; title: string; source: string; source_type: string; summary: string
  relevance_score: number; status: string; debate_notes: string; action_items: string
  idea_id: string; created_at: string
}

export default function EvolutionPanel() {
  const { tr } = useI18n()
  const [status, setStatus] = useState<EvoStatus | null>(null)
  const [failures, setFailures] = useState<Failure[]>([])
  const [research, setResearch] = useState<ResearchItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [s, f, r] = await Promise.all([
          fetch('/api/evolution/status').then(r => r.json()),
          fetch('/api/evolution/failures').then(r => r.json()),
          fetch('/api/evolution/research').then(r => r.json()),
        ])
        setStatus(s); setFailures(f); setResearch(r)
      } catch (e) { console.warn('[EvolutionPanel]', e) } finally { setLoading(false) }
    })()
  }, [])

  const sevColors: Record<string, string> = { critical: 'text-red-400 bg-red-500/20', high: 'text-orange-400 bg-orange-500/20', medium: 'text-yellow-400 bg-yellow-500/20', low: 'text-blue-400 bg-blue-500/20' }
  const catIcons: Record<string, string> = { race_condition: '🔀', resource_leak: '💧', config_miss: '⚙️', logic_error: '🧩', dependency: '📦', timeout: '⏱️', api_error: '🔌', security: '🔒' }

  if (loading) return <div className="flex items-center gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" />Loading evolution data...</div>

  return (
    <div className="max-w-3xl space-y-8">
      <h2 className="text-3xl font-bold">Self-Evolution</h2>

      {/* Health Dashboard */}
      {status && (
        <div className="grid grid-cols-4 gap-4">
          <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 text-center">
            <Shield className="w-6 h-6 text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-400">{status.failures.antibodies_active}</div>
            <div className="text-sm text-gray-400">Antibodies Active</div>
          </div>
          <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 text-center">
            <AlertTriangle className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-yellow-400">{status.failures.vaccines_active}</div>
            <div className="text-sm text-gray-400">Vaccines Active</div>
          </div>
          <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 text-center">
            <Microscope className="w-6 h-6 text-blue-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-blue-400">{status.research.accepted}/{status.research.total_findings}</div>
            <div className="text-sm text-gray-400">Research Accepted</div>
          </div>
          <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 text-center">
            <TrendingUp className="w-6 h-6 text-purple-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-purple-400">{status.evolution_health}</div>
            <div className="text-sm text-gray-400">System Health</div>
          </div>
        </div>
      )}

      {/* Failure Alchemy — Antibodies */}
      <div>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-green-400" /> Failure Alchemy
        </h3>
        <div className="space-y-3">
          {failures.map(f => (
            <div key={f.id} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-base">{f.title}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-white/10 text-gray-400">{catIcons[f.category] || '📋'} {f.category}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${sevColors[f.severity] || ''}`}>{f.severity}</span>
                  {f.frequency >= 2 && <span className="text-xs text-orange-400">×{f.frequency}</span>}
                </div>
              </div>
              <p className="text-sm text-gray-400 mb-2">Root cause: {f.root_cause}</p>
              <div className="grid grid-cols-1 gap-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-green-400 shrink-0 mt-0.5">🛡️</span>
                  <span className="text-gray-300">{f.antibody}</span>
                </div>
                {f.frequency >= 2 && (
                  <div className="flex items-start gap-2">
                    <span className="text-yellow-400 shrink-0 mt-0.5">💉</span>
                    <span className="text-gray-300">{f.vaccine}</span>
                  </div>
                )}
                <div className="flex items-start gap-2">
                  <span className="text-purple-400 shrink-0 mt-0.5">⚡</span>
                  <span className="text-gray-300">{f.catalyst}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Research Loop */}
      <div>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Microscope className="w-5 h-5 text-blue-400" /> Research Loop
        </h3>
        <div className="space-y-3">
          {research.map(r => (
            <div key={r.id} className={`border rounded-lg p-4 bg-white/5 ${
              r.status === 'accepted' ? 'border-green-500/20' :
              r.status === 'rejected' ? 'border-red-500/20 opacity-60' :
              r.status === 'debated' ? 'border-yellow-500/20' :
              'border-[hsl(var(--border))]'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-base">{r.title}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-white/10 text-gray-400">{r.source_type}</span>
                  <span className="text-xs text-blue-400">★{r.relevance_score}/10</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    r.status === 'accepted' ? 'bg-green-500/20 text-green-400' :
                    r.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                    r.status === 'debated' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>{r.status}</span>
                </div>
              </div>
              <p className="text-sm text-gray-400 mb-2">{r.summary}</p>
              {r.debate_notes && (
                <div className="text-sm text-yellow-300/80 bg-yellow-500/5 rounded p-2 mb-2">
                  <span className="text-yellow-400 font-medium">Debate:</span> {r.debate_notes}
                </div>
              )}
              {r.action_items && (
                <div className="text-sm text-green-400 flex items-center gap-1">
                  <Lightbulb className="w-4 h-4" /> {r.action_items}
                </div>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                <span>Source: {r.source}</span>
                {r.idea_id && <span className="text-blue-400">→ Idea created in Inbox</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
