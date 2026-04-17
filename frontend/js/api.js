/* frontend/js/api.js — 统一 API 客户端封装（RESTful 端点） */

const API = {
    /** 统一请求封装 */
    async request(url, options = {}) {
        const defaults = {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        };
        // 如果是 FormData，移除 Content-Type 让浏览器自动设置
        if (options.body instanceof FormData) {
            delete defaults.headers['Content-Type'];
        }
        const merged = {
            ...defaults,
            ...options,
            headers: { ...defaults.headers, ...(options.headers || {}) }
        };

        try {
            const response = await fetch(url, merged);
            if (!response.ok) {
                const errData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
                throw new Error(errData.error || errData.message || `HTTP ${response.status}`);
            }
            // 204 No Content
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error(`API 请求失败 [${url}]:`, error);
            throw error;
        }
    },

    /* ========== 用户偏好 ========== */
    async getPreferences() {
        return this.request('/api/settings/preferences');
    },
    async savePreferences(data) {
        return this.request('/api/settings/preferences', { method: 'PUT', body: JSON.stringify(data) });
    },

    /* ========== 提供商 ========== */
    async getProviders() {
        return this.request('/api/providers/');
    },
    async createProvider(data) {
        return this.request('/api/providers/', { method: 'POST', body: JSON.stringify(data) });
    },
    async updateProvider(name, data) {
        return this.request(`/api/providers/${encodeURIComponent(name)}`, { method: 'PUT', body: JSON.stringify(data) });
    },
    async deleteProvider(name) {
        return this.request(`/api/providers/${encodeURIComponent(name)}`, { method: 'DELETE' });
    },
    async saveApiKey(providerName, apiKey) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/api-key`, {
            method: 'PUT',
            body: JSON.stringify({ api_key: apiKey })
        });
    },

    /* ========== 模型 ========== */
    async addModel(providerName, data) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/models`, { method: 'POST', body: JSON.stringify(data) });
    },
    async deleteModel(providerName, modelDisplay) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/models/${encodeURIComponent(modelDisplay)}`, { method: 'DELETE' });
    },

    /* ========== 提示词 ========== */
    async getPrompts() {
        return this.request('/api/prompts/');
    },
    async createPrompt(data) {
        return this.request('/api/prompts/', { method: 'POST', body: JSON.stringify(data) });
    },
    async deletePrompt(name) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}`, { method: 'DELETE' });
    },

    /* ========== 任务 ========== */
    async startProcessing(data) {
        return this.request('/api/tasks/start', { method: 'POST', body: JSON.stringify(data) });
    },
    async cancelProcessing() {
        return this.request('/api/tasks/cancel', { method: 'POST' });
    },
    async getProcessingStatus() {
        return this.request('/api/tasks/status');
    },

    /* ========== 文件/目录 ========== */
    async getDrives() {
        return this.request('/api/files/drives');
    },
    async getDirectoryContents(path = '') {
        const url = path ? `/api/files/directory?path=${encodeURIComponent(path)}` : '/api/files/drives';
        return this.request(url);
    },
    async viewResult(filePath) {
        return this.request(`/api/files/result?path=${encodeURIComponent(filePath)}`);
    },

    /* ========== 系统设置 ========== */
    async getSystemSettings() {
        return this.request('/api/settings/system');
    },
    async saveSystemSettings(data) {
        return this.request('/api/settings/system', { method: 'PUT', body: JSON.stringify(data) });
    },

    /* ========== 回收站 ========== */
    async getTrash() {
        return this.request('/api/settings/trash');
    },
    async restoreProvider(name) {
        return this.request(`/api/settings/trash/restore/provider/${encodeURIComponent(name)}`, { method: 'POST' });
    },
    async permanentDeleteProvider(name) {
        return this.request(`/api/settings/trash/provider/${encodeURIComponent(name)}`, { method: 'DELETE' });
    },
    async restorePrompt(name) {
        return this.request(`/api/settings/trash/restore/prompt/${encodeURIComponent(name)}`, { method: 'POST' });
    },
    async permanentDeletePrompt(name) {
        return this.request(`/api/settings/trash/prompt/${encodeURIComponent(name)}`, { method: 'DELETE' });
    }
};

window.API = API;
