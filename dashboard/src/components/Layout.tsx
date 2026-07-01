import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ListTodo, Lightbulb, GitBranch, Cpu, BookOpen, Settings, Globe, TrendingUp } from 'lucide-react'
import { useI18n } from '../i18n/context'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { tr, toggleLang, lang } = useI18n()

  const nav = [
    { to: '/', label: tr('nav.overview'), icon: LayoutDashboard },
    { to: '/tasks', label: tr('nav.taskWall'), icon: ListTodo },
    { to: '/ideas', label: tr('nav.ideaInbox'), icon: Lightbulb },
    { to: '/pipelines', label: tr('nav.pipelines'), icon: GitBranch },
    { to: '/evolution', label: tr('nav.evolution'), icon: TrendingUp },
    { to: '/hardware', label: tr('nav.hardware'), icon: Cpu },
    { to: '/knowledge', label: tr('nav.knowledge'), icon: BookOpen },
    { to: '/settings', label: tr('nav.settings'), icon: Settings },
  ]

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-60 border-r border-[hsl(var(--border))] p-5 flex flex-col gap-1">
        <div className="mb-6 px-3 py-2 flex items-center justify-between">
          <h1 className="text-base font-bold tracking-tight">
            <Cpu className="inline w-5 h-5 mr-2 text-blue-400" />
            {tr('brand.name')}
          </h1>
        </div>

        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded text-base transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}

        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="mt-auto flex items-center gap-2 px-3 py-2.5 rounded text-base text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <Globe className="w-5 h-5" />
          {tr('lang.switch')}
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-8">
        {children}
      </main>
    </div>
  )
}
