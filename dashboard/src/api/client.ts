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
  health: () => request<any>('GET', '/health'),

  // Projects
  projects: {
    list: (status?: string) => request<any[]>('GET', `/projects/${status ? `?status=${status}` : ''}`),
    get: (id: string) => request<any>('GET', `/projects/${id}`),
    create: (data: any) => request<any>('POST', '/projects/', data),
  },

  // Tasks
  tasks: {
    list: (projectId?: string) => request<any[]>('GET', `/tasks/${projectId ? `?project_id=${projectId}` : ''}`),
    create: (data: any) => request<any>('POST', '/tasks/', data),
    updateStatus: (id: string, status: string) => request<any>('PATCH', `/tasks/${id}/status?status=${status}`),
    wall: (projectId?: string) => request<any>('GET', `/tasks/${projectId ? `?project_id=${projectId}` : ''}`),
  },

  // Teams
  teams: {
    list: (projectId?: string) => request<any[]>('GET', `/teams/${projectId ? `?project_id=${projectId}` : ''}`),
    create: (data: any) => request<any>('POST', '/teams/', data),
  },

  // Pipelines
  pipelines: {
    list: (projectId?: string) => request<any[]>('GET', `/pipelines/${projectId ? `?project_id=${projectId}` : ''}`),
    get: (id: string) => request<any>('GET', `/pipelines/${id}`),
  },
}

export type { API }
