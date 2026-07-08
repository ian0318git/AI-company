const API_BASE = '/api'

async function request<T = any>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${API_BASE}${path}`
  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) options.body = JSON.stringify(body)

  const res = await fetch(url, options)
  if (res.status === 204) return {} as T
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // System
  health: () => fetch('/health').then(r => { if (!r.ok) throw new Error(`Health check failed: HTTP ${r.status}`); return r.json() }),

  // Projects
  projects: {
    list: (status?: string) => request<any[]>('GET', `/projects/${status ? `?status=${status}` : ''}`),
    get: (id: string) => request<any>('GET', `/projects/${id}`),
    create: (data: any) => request<any>('POST', '/projects/', data),
    getTime: (id: string) => request<any>('GET', `/projects/${id}/time`),
  },

  // Tasks
  tasks: {
    list: (projectId?: string) => request<any[]>('GET', `/tasks/${projectId ? `?project_id=${projectId}` : ''}`),
    create: (data: any) => request<any>('POST', '/tasks/', data),
    updateStatus: (id: string, status: string) => request<any>('PATCH', `/tasks/${id}/status?status=${status}`),
    wall: (projectId?: string) => request<any>('GET', `/tasks/${projectId ? `?project_id=${projectId}` : ''}`),
    metrics: (projectId?: string) => request<any>('GET', `/tasks/metrics${projectId ? `?project_id=${projectId}` : ''}`),
    getTime: (id: string) => request<any>('GET', `/tasks/${id}/time`),
    logTokens: (id: string, tokens: number, agent: string) => request<any>('POST', `/tasks/${id}/tokens`, { tokens, agent }),
  },

  // Teams
  teams: {
    list: (projectId?: string) => request<any[]>('GET', `/teams/${projectId ? `?project_id=${projectId}` : ''}`),
    create: (data: any) => request<any>('POST', '/teams/', data),
  },

  // Ideas
  ideas: {
    list: (projectId?: string, status?: string) => {
      const params = new URLSearchParams()
      if (projectId) params.set('project_id', projectId)
      if (status) params.set('status', status)
      const qs = params.toString()
      return request<any[] | { ideas: any[] }>('GET', `/ideas/${qs ? `?${qs}` : ''}`)
    },
    create: (data: { title: string; raw_description: string; tags?: string[] }) =>
      request<any>('POST', '/ideas/', data),
    get: (id: string) => request<any>('GET', `/ideas/${id}`),
    refine: (id: string) => request<any>('POST', `/ideas/${id}/refine`),
    start: (id: string) => request<any>('POST', `/ideas/${id}/start`),
    workflow: (id: string) => request<any>('GET', `/ideas/${id}/workflow`),
    deliverables: (id: string) => request<any[]>('GET', `/ideas/${id}/deliverables`),
    addAgent: (id: string, agent: string) => request<any>('POST', `/ideas/${id}/team/add-agent?agent_role=${encodeURIComponent(agent)}`),
    removeAgent: (id: string, agent: string) => request<any>('POST', `/ideas/${id}/team/remove-agent?agent_role=${encodeURIComponent(agent)}`),
  },

  // Dashboard
  dashboard: {
    metrics: () => request<any>('GET', '/dashboard/metrics'),
  },

  // Prompts
  prompts: {
    templates: {
      list: (agentRole?: string, status?: string) => {
        const params = new URLSearchParams()
        if (agentRole) params.set('agent_role', agentRole)
        if (status) params.set('status', status)
        const qs = params.toString()
        return request<any[]>('GET', `/prompts/templates${qs ? `?${qs}` : ''}`)
      },
      create: (data: any) => request<any>('POST', '/prompts/templates', data),
      get: (id: string) => request<any>('GET', `/prompts/templates/${id}`),
      update: (id: string, data: any) => request<any>('PATCH', `/prompts/templates/${id}`, data),
    },
    optimized: (agentRole: string, pipelineType?: string) => {
      const params = new URLSearchParams({ agent_role: agentRole })
      if (pipelineType) params.set('pipeline_type', pipelineType)
      return request<any>('GET', `/prompts/optimized?${params}`)
    },
    results: {
      list: (templateId?: string, agentRole?: string) => {
        const params = new URLSearchParams()
        if (templateId) params.set('template_id', templateId)
        if (agentRole) params.set('agent_role', agentRole)
        const qs = params.toString()
        return request<any[]>('GET', `/prompts/results${qs ? `?${qs}` : ''}`)
      },
      log: (data: any) => request<any>('POST', '/prompts/results', data),
    },
    experiments: {
      list: (status?: string) => request<any[]>('GET', `/prompts/experiments${status ? `?status=${status}` : ''}`),
      create: (data: any) => request<any>('POST', '/prompts/experiments', data),
      get: (id: string) => request<any>('GET', `/prompts/experiments/${id}`),
      conclude: (id: string) => request<any>('POST', `/prompts/experiments/${id}/conclude`),
    },
    insights: {
      list: (agentRole?: string, minConfidence?: number) => {
        const params = new URLSearchParams()
        if (agentRole) params.set('agent_role', agentRole)
        if (minConfidence) params.set('min_confidence', String(minConfidence))
        const qs = params.toString()
        return request<any[]>('GET', `/prompts/insights${qs ? `?${qs}` : ''}`)
      },
      generate: () => request<any>('POST', '/prompts/insights/generate'),
    },
    roi: () => request<any>('GET', '/prompts/roi'),
  },

  // Pipelines
  pipelines: {
    list: (projectId?: string) => request<any[]>('GET', `/pipelines/${projectId ? `?project_id=${projectId}` : ''}`),
    get: (id: string) => request<any>('GET', `/pipelines/${id}`),
    advance: (id: string) => request<any>('POST', `/pipelines/${id}/advance`),
  },
}
