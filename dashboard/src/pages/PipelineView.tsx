import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { GitBranch, ArrowRight } from 'lucide-react'

export default function PipelineView() {
  const [pipelines, setPipelines] = useState<any[]>([])

  useEffect(() => {
    api.pipelines.list().then((data: any) => {
      setPipelines(Array.isArray(data) ? data : [])
    }).catch(() => {})
  }, [])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Pipelines</h2>

      {pipelines.length === 0 ? (
        <div className="border border-[hsl(var(--border))] rounded-lg p-8 bg-white/5 text-center">
          <GitBranch className="w-12 h-12 mx-auto mb-4 text-gray-600" />
          <p className="text-gray-400">No active pipelines.</p>
          <p className="text-sm text-gray-500 mt-2">
            Use <code className="text-blue-400">pipeline_create</code> in Claude Code to start one.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {pipelines.map((p: any) => (
            <div key={p.id} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-blue-400 font-mono">{p.pipeline_type}</span>
                  <h3 className="font-semibold mt-1">Pipeline {p.id.slice(0, 8)}</h3>
                </div>
                <span className="text-sm text-gray-400">{p.current_phase}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5 mt-6">
        <h3 className="text-lg font-semibold mb-4">Pipeline Types</h3>
        <div className="space-y-3">
          {[
            { name: 'embedded-firmware', desc: 'Idea → Pin Plan → HAL → Logic → Test → Flash', color: 'text-green-400' },
            { name: 'embedded-linux', desc: 'Idea → System Design → Driver/App → Cross-compile → Test', color: 'text-blue-400' },
            { name: 'web-fullstack', desc: 'Idea → UI/UX → Frontend → Backend → Deploy', color: 'text-purple-400' },
            { name: 'quick-prototype', desc: 'Idea → MVP → Iterate', color: 'text-yellow-400' },
            { name: 'research-spike', desc: 'Research Question → Survey → Feasibility → Report', color: 'text-orange-400' },
          ].map(({ name, desc, color }) => (
            <div key={name} className="flex items-center gap-3">
              <ArrowRight className={`w-4 h-4 ${color}`} />
              <div>
                <span className={`text-sm font-medium ${color}`}>{name}</span>
                <span className="text-xs text-gray-500 ml-2">{desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
