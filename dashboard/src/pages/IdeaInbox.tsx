import { useState } from 'react'
import { Lightbulb, Send } from 'lucide-react'

export default function IdeaInbox() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = () => {
    if (!title.trim()) return
    setSubmitted(true)
    // In a full implementation, call api.ideas.create()
    setTimeout(() => setSubmitted(false), 3000)
    setTitle('')
    setDescription('')
    setTags('')
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">Idea Inbox</h2>

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
        />

        <textarea
          placeholder="Describe your idea... What does it do? Who is it for? What hardware/software should it use?"
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

        <button
          onClick={handleSubmit}
          disabled={!title.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded text-sm font-medium transition-colors"
        >
          <Send className="w-4 h-4" />
          {submitted ? 'Submitted!' : 'Submit Idea'}
        </button>
      </div>

      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5">
        <h3 className="text-lg font-semibold mb-3">Recent Ideas</h3>
        <p className="text-sm text-gray-500">
          Captured ideas will appear here. Use the <code className="text-blue-400">idea_capture</code> MCP tool
          in Claude Code to submit ideas directly.
        </p>
      </div>
    </div>
  )
}
