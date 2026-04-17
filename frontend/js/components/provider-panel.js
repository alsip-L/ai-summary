/* provider-panel.js — Provider configuration panel */

const ProviderPanel = {
    render() {
        const container = document.getElementById('provider-section');
        if (!container) return;

        const models = AppState.getCurrentModels();
        const modelKeys = Object.keys(models);
        const apiKey = AppState.getCurrentApiKey();

        container.innerHTML = `
            <div class="section-header">服务商</div>
            <div class="form-group">
                <label class="form-label">AI 服务商</label>
                <div class="custom-dropdown" id="provider-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('provider-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedProvider || '请选择...')}</span>
                        <span class="dropdown-arrow">&#9662;</span>
                    </div>
                    <div class="dropdown-content" id="provider-options">
                        ${AppState.providerNames.map(name => `
                            <div class="dropdown-option" onclick="ProviderPanel.selectProvider('${Utils.escapeHtml(name)}'); event.stopPropagation();">
                                <span>${Utils.escapeHtml(name)}</span>
                                <button type="button" class="delete-option-btn" onclick="ProviderPanel.deleteProvider('${Utils.escapeHtml(name)}'); event.stopPropagation();">&times;</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="ProviderPanel.addNew(); event.stopPropagation();">
                            <span style="color: var(--accent-indigo);">+ 新增服务商</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">模型</label>
                <div class="custom-dropdown" id="model-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('model-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedModel || '请选择...')}</span>
                        <span class="dropdown-arrow">&#9662;</span>
                    </div>
                    <div class="dropdown-content" id="model-options">
                        ${modelKeys.map(display => `
                            <div class="dropdown-option" onclick="ProviderPanel.selectModel('${Utils.escapeHtml(display)}'); event.stopPropagation();">
                                <span>${Utils.escapeHtml(display)}</span>
                                <button type="button" class="delete-option-btn" onclick="ProviderPanel.deleteModel('${Utils.escapeHtml(AppState.selectedProvider)}', '${Utils.escapeHtml(display)}'); event.stopPropagation();">&times;</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="ProviderPanel.addModel(); event.stopPropagation();">
                            <span style="color: var(--accent-indigo);">+ 新增模型</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">API Key</label>
                <input type="text" id="api_key" class="form-control" value="${Utils.escapeHtml(apiKey)}" placeholder="${apiKey ? '已配置' : '请输入 API Key'}" onblur="ProviderPanel.saveApiKey()">
            </div>
            <div class="form-group">
                <label class="form-label">处理目录</label>
                <div class="input-group">
                    <input type="text" id="directory_path" class="form-control" value="${Utils.escapeHtml(AppState.directoryPath)}" placeholder="输入目录路径" onblur="ProviderPanel.saveDirectoryPath()">
                    <button type="button" class="btn btn-sm btn-secondary" onclick="DirectoryBrowser.open()">浏览</button>
                </div>
            </div>
        `;
    },

    async selectProvider(name) {
        closeAllDropdowns();
        try {
            await API.savePreferences({ selected_provider: name });
            AppState.selectedProvider = name;
            const models = AppState.getCurrentModels();
            AppState.selectedModel = Object.keys(models)[0] || '';
            AppState.apiKey = AppState.getCurrentApiKey();
            AppState.notify('provider-changed');
            this.render();
            showMessage('已保存', 'success');
        } catch (e) {
            showMessage('保存失败: ' + e.message, 'error');
        }
    },

    async selectModel(name) {
        closeAllDropdowns();
        try {
            await API.savePreferences({ selected_model: name });
            AppState.selectedModel = name;
            AppState.notify('model-changed');
            this.render();
            showMessage('已保存', 'success');
        } catch (e) {
            showMessage('保存失败: ' + e.message, 'error');
        }
    },

    async deleteProvider(name) {
        closeAllDropdowns();
        if (!confirm(`确定删除服务商 '${name}' 吗？`)) return;
        try {
            await API.deleteProvider(name);
            await AppState.loadAll();
            AppState.notify('provider-deleted');
            this.render();
            TrashPanel.render();
        } catch (e) {
            showMessage('删除失败: ' + e.message, 'error');
        }
    },

    async deleteModel(providerName, modelDisplay) {
        closeAllDropdowns();
        if (!confirm(`确定从 '${providerName}' 删除模型 '${modelDisplay}' 吗？`)) return;
        try {
            await API.deleteModel(providerName, modelDisplay);
            await AppState.loadAll();
            AppState.notify('model-deleted');
            this.render();
        } catch (e) {
            showMessage('删除失败: ' + e.message, 'error');
        }
    },

    async saveApiKey() {
        const input = document.getElementById('api_key');
        if (!input || !AppState.selectedProvider) return;
        const key = input.value.trim();
        try {
            await API.saveApiKey(AppState.selectedProvider, key);
            AppState.apiKey = key;
            showMessage('API Key 已保存', 'success');
        } catch (e) {
            showMessage('保存失败: ' + e.message, 'error');
        }
    },

    async saveDirectoryPath() {
        const input = document.getElementById('directory_path');
        if (!input) return;
        const path = input.value.trim();
        if (!path) return;
        try {
            await API.savePreferences({ directory_path: path });
            AppState.directoryPath = path;
            showMessage('目录路径已保存', 'success');
        } catch (e) {
            showMessage('保存失败: ' + e.message, 'error');
        }
    },

    addNew() {
        closeAllDropdowns();
        showDialog({
            title: '新增服务商',
            fields: [
                { id: 'new_provider_name', label: '名称', placeholder: '如: OpenAI' },
                { id: 'new_provider_url', label: 'API 地址', placeholder: '如: https://api.openai.com/v1' },
                { id: 'new_provider_apikey', label: 'API Key', placeholder: '可选' },
                { id: 'new_provider_model', label: '模型名称', placeholder: '可选，如: gpt-4' }
            ],
            onSubmit: async () => {
                const name = document.getElementById('new_provider_name').value.trim();
                const url = document.getElementById('new_provider_url').value.trim();
                const apiKey = document.getElementById('new_provider_apikey').value.trim();
                const modelName = document.getElementById('new_provider_model').value.trim();
                if (!name || !url) { showMessage('名称和地址为必填', 'warning'); return false; }
                const models = modelName ? { [modelName]: modelName } : { 'default': name.toLowerCase().replace(/\s+/g, '-') + '-model' };
                await API.createProvider({ name, base_url: url, api_key: apiKey, models });
                await AppState.loadAll();
                AppState.notify('provider-added');
                ProviderPanel.render();
                return true;
            }
        });
    },

    addModel() {
        closeAllDropdowns();
        if (!AppState.selectedProvider) { showMessage('请先选择服务商', 'warning'); return; }
        showDialog({
            title: `新增模型 — ${AppState.selectedProvider}`,
            fields: [
                { id: 'new_model_display', label: '显示名称', placeholder: '如: GPT-4' },
                { id: 'new_model_id', label: '模型 ID', placeholder: '如: gpt-4' }
            ],
            onSubmit: async () => {
                const display = document.getElementById('new_model_display').value.trim();
                const id = document.getElementById('new_model_id').value.trim();
                if (!display || !id) { showMessage('两项均为必填', 'warning'); return false; }
                await API.addModel(AppState.selectedProvider, { display_name: display, model_id: id });
                await AppState.loadAll();
                AppState.notify('model-added');
                ProviderPanel.render();
                return true;
            }
        });
    }
};

window.ProviderPanel = ProviderPanel;
