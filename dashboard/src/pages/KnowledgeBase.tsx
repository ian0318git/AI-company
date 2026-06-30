import { BookOpen, Search } from 'lucide-react'

export default function KnowledgeBase() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Knowledge Base</h2>

      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search knowledge base..."
            className="w-full border border-[hsl(var(--border))] rounded pl-10 pr-4 py-2 bg-black/30 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {[
          { title: 'M5Stack Core S3 Pinout', category: 'pinout', tags: ['m5stack', 'esp32-s3', 'pinout'] },
          { title: 'ESP32 Common Pitfalls', category: 'reference', tags: ['esp32', 'gotchas', 'debug'] },
          { title: 'PlatformIO Quick Start', category: 'code-pattern', tags: ['platformio', 'build', 'ci'] },
          { title: 'I2C Bus Best Practices', category: 'tip', tags: ['i2c', 'sensor', 'pull-up'] },
          { title: 'FreeRTOS Task Patterns', category: 'code-pattern', tags: ['rtos', 'freertos', 'task'] },
          { title: 'WiFi Power Optimization', category: 'tip', tags: ['wifi', 'power', 'battery'] },
        ].map(({ title, category, tags }) => (
          <div key={title} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5 hover:bg-white/10 transition-colors cursor-pointer">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-blue-400 uppercase">{category}</span>
            </div>
            <h3 className="font-medium text-sm mb-2">{title}</h3>
            <div className="flex gap-1 flex-wrap">
              {tags.map(t => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">{t}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
