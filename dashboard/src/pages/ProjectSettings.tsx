import { Settings, Users, Cpu, HardDrive } from 'lucide-react'

export default function ProjectSettings() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Settings</h2>

      <div className="space-y-4 max-w-xl">
        {[
          {
            title: 'System',
            icon: HardDrive,
            items: [
              { label: 'API Server', value: 'http://127.0.0.1:8765', desc: 'The FastAPI backend' },
              { label: 'Database', value: 'SQLite (local)', desc: '~/.claude/data/ai-embedded-company/' },
              { label: 'Version', value: '0.1.0', desc: 'AI Embedded Company' },
            ],
          },
          {
            title: 'Agent Templates',
            icon: Users,
            items: [
              { label: 'Installed', value: '19 agents', desc: 'In ~/.claude/agents/' },
              { label: 'Categories', value: 'Embedded / Software / Management / Special', desc: '4 categories' },
            ],
          },
          {
            title: 'Hardware Defaults',
            icon: Cpu,
            items: [
              { label: 'Default Board', value: 'M5Stack Core S3', desc: 'ESP32-S3 platform' },
              { label: 'Default Port', value: '/dev/ttyACM0', desc: 'Serial upload port' },
              { label: 'Baud Rate', value: '115200', desc: 'Monitor / 921600 upload' },
            ],
          },
        ].map(({ title, icon: Icon, items }) => (
          <div key={title} className="border border-[hsl(var(--border))] rounded-lg bg-white/5 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-[hsl(var(--border))]">
              <Icon className="w-4 h-4 text-blue-400" />
              <h3 className="font-semibold text-sm">{title}</h3>
            </div>
            <div className="p-4 space-y-3">
              {items.map(({ label, value, desc }) => (
                <div key={label} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{label}</p>
                    <p className="text-xs text-gray-500">{desc}</p>
                  </div>
                  <span className="text-xs font-mono text-gray-400">{value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
