const BASE_URL = ''

async function request(url, options = {}) {
  const defaults = {
    credentials: 'same-origin',
  }
  // Only set Content-Type when there is a body
  if (options.body) {
    defaults.headers = { 'Content-Type': 'application/json' }
  }
  const merged = {
    ...defaults,
    ...options,
    headers: { ...(defaults.headers || {}), ...(options.headers || {}) },
  }

  const response = await fetch(BASE_URL + url, merged)
  if (!response.ok) {
    const errData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }))
    throw new Error(errData.error || errData.message || `HTTP ${response.status}`)
  }
  if (response.status === 204) return null
  return await response.json()
}

export const api = {
  getProviders: () => request('/api/providers/'),
  createProvider: (data) => request('/api/providers/', { method: 'POST', body: JSON.stringify(data) }),
  deleteProvider: (name) => request(`/api/providers/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  saveApiKey: (name, apiKey) => request(`/api/providers/${encodeURIComponent(name)}/api-key`, { method: 'PUT', body: JSON.stringify({ api_key: apiKey }) }),
  addModel: (name, data) => request(`/api/providers/${encodeURIComponent(name)}/models`, { method: 'POST', body: JSON.stringify(data) }),
  deleteModel: (name, modelDisplay) => request(`/api/providers/${encodeURIComponent(name)}/models/${encodeURIComponent(modelDisplay)}`, { method: 'DELETE' }),

  getPrompts: () => request('/api/prompts/'),
  createPrompt: (data) => request('/api/prompts/', { method: 'POST', body: JSON.stringify(data) }),
  deletePrompt: (name) => request(`/api/prompts/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  startProcessing: (data) => request('/api/tasks/start', { method: 'POST', body: JSON.stringify(data) }),
  cancelProcessing: () => request('/api/tasks/cancel', { method: 'POST' }),
  getProcessingStatus: () => request('/api/tasks/status'),
  getFailedRecords: () => request('/api/tasks/failed'),
  clearFailedRecords: () => request('/api/tasks/failed', { method: 'DELETE' }),
  retryFailed: (data) => request('/api/tasks/retry-failed', { method: 'POST', body: JSON.stringify(data) }),

  getDirectoryContents: (path = '') => {
    const url = path ? `/api/files/directory?path=${encodeURIComponent(path)}` : '/api/files/drives'
    return request(url)
  },
  viewResult: (filePath) => request(`/api/files/result?path=${encodeURIComponent(filePath)}`),

  getTrash: () => request('/api/settings/trash/'),
  restoreProvider: (name) => request(`/api/settings/trash/restore/provider/${encodeURIComponent(name)}`, { method: 'POST' }),
  permanentDeleteProvider: (name) => request(`/api/settings/trash/provider/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  restorePrompt: (name) => request(`/api/settings/trash/restore/prompt/${encodeURIComponent(name)}`, { method: 'POST' }),
  permanentDeletePrompt: (name) => request(`/api/settings/trash/prompt/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  getPreferences: () => request('/api/settings/preferences'),
  savePreferences: (data) => request('/api/settings/preferences', { method: 'PUT', body: JSON.stringify(data) }),

  clearLogs: () => request('/api/logs/clear', { method: 'POST' }),

  rebuild: () => request('/api/system/rebuild', { method: 'POST' }),
}
