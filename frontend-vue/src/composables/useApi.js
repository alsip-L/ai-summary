const BASE_URL = ''

const TOKEN_KEY = 'ai_summary_api_token'

function _loadToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || null
  } catch {
    return null
  }
}

function _saveToken(token) {
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token)
    } else {
      sessionStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    // sessionStorage 不可用时静默失败
  }
}

let _apiToken = _loadToken()

export function setApiToken(token) {
  _apiToken = token
  _saveToken(token)
}

export function getStoredApiToken() {
  return _apiToken
}

export function clearApiToken() {
  _apiToken = null
  _saveToken(null)
}

async function request(url, options = {}) {
  const defaults = {
    credentials: 'same-origin',
  }
  if (options.body) {
    defaults.headers = { 'Content-Type': 'application/json' }
  }
  if (_apiToken) {
    defaults.headers = { ...(defaults.headers || {}), 'X-API-Token': _apiToken }
  }
  const merged = {
    ...defaults,
    ...options,
    headers: { ...(defaults.headers || {}), ...(options.headers || {}) },
  }

  const response = await fetch(BASE_URL + url, merged)
  if (!response.ok) {
    if (response.status === 401) {
      clearApiToken()
    }
    const errData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }))
    throw new Error(errData.error || errData.message || `HTTP ${response.status}`)
  }
  if (response.status === 204) return null
  return await response.json()
}

export const api = {
  getToken: (secretKey) => request('/api/settings/token', { method: 'POST', body: JSON.stringify({ secret_key: secretKey }) }),

  getProviders: () => request('/api/providers/'),
  createProvider: (data) => request('/api/providers/', { method: 'POST', body: JSON.stringify(data) }),
  deleteProvider: (name) => request(`/api/providers/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  getApiKey: (name) => request(`/api/providers/${encodeURIComponent(name)}/api-key`),
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
  getPreferencesApiKey: () => request('/api/settings/preferences/api-key'),
  savePreferences: (data) => request('/api/settings/preferences', { method: 'PATCH', body: JSON.stringify(data) }),

  getSystemSettings: () => request('/api/settings/system'),
  saveSystemSettings: (data) => request('/api/settings/system', { method: 'PUT', body: JSON.stringify(data) }),

  clearLogs: () => request('/api/logs/clear', { method: 'POST' }),

  rebuild: () => request('/api/system/rebuild', { method: 'POST' }),
}
