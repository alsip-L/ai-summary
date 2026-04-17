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
                const errData = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
                throw new Error(errData.message || errData.error || `HTTP ${response.status}`);
            }
            // 204 No Content
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error(`API 请求失败 [${url}]:`, error);
            throw error;
        }
    },

    /* ========== 配置 ========== */
    async getConfig() {
        return this.request('/api/config');
    },
    async saveConfig(data) {
        return this.request('/api/config', { method: 'PUT', body: JSON.stringify(data) });
    },

    /* ========== 提供商 ========== */
    async getProviders() {
        return this.request('/api/providers/');
    },
    async getProvider(name) {
        return this.request(`/api/providers/${encodeURIComponent(name)}`);
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
    async restoreProvider(name) {
        return this.request(`/api/providers/${encodeURIComponent(name)}/restore`, { method: 'POST' });
    },
    async permanentDeleteProvider(name) {
        return this.request(`/api/providers/${encodeURIComponent(name)}/permanent-delete`, { method: 'DELETE' });
    },

    /* ========== 模型 ========== */
    async addModel(providerName, data) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/models/`, { method: 'POST', body: JSON.stringify(data) });
    },
    async deleteModel(providerName, modelDisplay) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/models/${encodeURIComponent(modelDisplay)}`, { method: 'DELETE' });
    },

    /* ========== API Key ========== */
    async saveApiKey(providerName, apiKey) {
        return this.request(`/api/providers/${encodeURIComponent(providerName)}/api-key`, {
            method: 'PUT',
            body: JSON.stringify({ api_key: apiKey })
        });
    },

    /* ========== 提示词 ========== */
    async getPrompts() {
        return this.request('/api/prompts/');
    },
    async getPrompt(name) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}`);
    },
    async createPrompt(data) {
        return this.request('/api/prompts/', { method: 'POST', body: JSON.stringify(data) });
    },
    async updatePrompt(name, data) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}`, { method: 'PUT', body: JSON.stringify(data) });
    },
    async deletePrompt(name) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}`, { method: 'DELETE' });
    },
    async restorePrompt(name) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}/restore`, { method: 'POST' });
    },
    async permanentDeletePrompt(name) {
        return this.request(`/api/prompts/${encodeURIComponent(name)}/permanent-delete`, { method: 'DELETE' });
    },

    /* ========== 处理 ========== */
    async startProcessing(data) {
        return this.request('/api/processing/start', { method: 'POST', body: JSON.stringify(data) });
    },
    async cancelProcessing() {
        return this.request('/api/processing/cancel', { method: 'POST' });
    },
    async getProcessingStatus() {
        return this.request('/api/processing/status');
    },

    /* ========== 目录 ========== */
    async getDirectoryContents(path = '') {
        const url = path ? `/api/directory/contents?path=${encodeURIComponent(path)}` : '/api/directory/contents';
        return this.request(url);
    },

    /* ========== 系统设置 ========== */
    async getSystemSettings() {
        return this.request('/api/settings');
    },
    async saveSystemSettings(data) {
        return this.request('/api/settings', { method: 'PUT', body: JSON.stringify(data) });
    },

    /* ========== 回收站 ========== */
    async getTrash() {
        return this.request('/api/trash');
    },

    /* ========== 结果文件 ========== */
    async viewResult(filePath) {
        return this.request(`/api/results/view?path=${encodeURIComponent(filePath)}`);
    }
};

window.API = API;
