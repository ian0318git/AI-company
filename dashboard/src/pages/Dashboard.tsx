import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Cpu, ListTodo, Lightbulb, GitBranch, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({ projects: 0, tasks: 0, ideas: 0, pipelines: 0 })

  useEffect(() => {
    Promise.all([
      api.projects.list('active'),
      api.tasks.list(),
      api.pipelines.list(),
    ]).then(([projects, tasks, pipelines]) => {
      setStats({
        projects: Array.isArray(projects) ? projects.length : 0,
        tasks: Array.isArray(tasks) ? tasks.length : 0,
        ideas: 0,
        pipelines: Array.isArray(pipelines) ? pipelines.length : 0,
      })
    }).catch(() => {})
  }, [])

  const cards = [
    { label: 'Active Projects', value: stats.projects, icon: Cpu, color: 'text-blue-400' },
    { label: 'Open Tasks', value: stats.tasks, icon: ListTodo, color: 'text-yellow-400' },
    { label: 'Ideas Captured', value: stats.ideas, icon: Lightbulb, color: 'text-purple-400' },
    { label: 'Pipelines', value: stats.pipelines, icon: GitBranch, color: 'text-green-400' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-5 h-5 ${color}`} />
              <span className="text-sm text-gray-400">{label}</span>
            </div>
            <p className="text-3xl font-bold">{value}</p>
          </div>
        ))}
      </div>

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
