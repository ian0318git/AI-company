import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ListTodo, Lightbulb, GitBranch, Cpu, BookOpen, Settings } from 'lucide-react'

const nav = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/tasks', label: 'Task Wall', icon: ListTodo },
  { to: '/ideas', label: 'Idea Inbox', icon: Lightbulb },
  { to: '/pipelines', label: 'Pipelines', icon: GitBranch },
  { to: '/hardware', label: 'Hardware', icon: Cpu },
  { to: '/knowledge', label: 'Knowledge', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 border-r border-[hsl(var(--border))] p-4 flex flex-col gap-1">
        <div className="mb-6 px-3 py-2">
          <h1 className="text-sm font-bold tracking-tight">
            <Cpu className="inline w-4 h-4 mr-2 text-blue-400" />
            AI Embedded Co.
          </h1>
        </div>
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  )
}
