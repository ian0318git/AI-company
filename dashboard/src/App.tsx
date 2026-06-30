import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskWall from './pages/TaskWall'
import IdeaInbox from './pages/IdeaInbox'
import PipelineView from './pages/PipelineView'
import HardwarePanel from './pages/HardwarePanel'
import KnowledgeBase from './pages/KnowledgeBase'
import ProjectSettings from './pages/ProjectSettings'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tasks" element={<TaskWall />} />
        <Route path="/ideas" element={<IdeaInbox />} />
        <Route path="/pipelines" element={<PipelineView />} />
        <Route path="/hardware" element={<HardwarePanel />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/settings" element={<ProjectSettings />} />
      </Routes>
    </Layout>
  )
}
