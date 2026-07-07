import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ListTodo, Lightbulb, GitBranch, Cpu, BookOpen, Settings, Globe, TrendingUp, Wifi, WifiOff } from 'lucide-react'
import { useI18n } from '../i18n/context'
import { useConnectionStatus } from '../hooks/useConnectionStatus'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { tr, toggleLang, lang } = useI18n()
  const connectionState = useConnectionStatus()

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
        <div className="mb-4 px-3 py-2">
          <h1 className="text-base font-bold tracking-tight">
            <Cpu className="inline w-5 h-5 mr-2 text-blue-400" />
            {tr('brand.name')}
          </h1>
        </div>

        {/* CEO Status */}
        <div className="mb-4 mx-1 p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-medium text-blue-400">{tr('ceo.title')}</span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">{tr('ceo.subtitle')}</p>
          <div className="flex items-center gap-1 mt-2 text-[10px] text-gray-500">
            <span>👤 {tr('ceo.chairman')}</span>
            <span className="text-gray-600">→</span>
            <span className="text-blue-400">🤖 {tr('ceo.ai')}</span>
            <span className="text-gray-600">→</span>
            <span>👥 {tr('ceo.agents')}</span>
          </div>
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
        {connectionState === 'connecting' && (
          <div className="flex items-center gap-2 px-4 py-2 mb-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm">
            <Wifi className="w-4 h-4 animate-pulse" />
            Connecting to API server...
          </div>
        )}
        {connectionState === 'disconnected' && (
          <div className="flex items-center gap-2 px-4 py-2 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <WifiOff className="w-4 h-4" />
            API server disconnected — check if the backend is running (port 8765)
          </div>
        )}
        {children}
      </main>
    </div>
  )
}
