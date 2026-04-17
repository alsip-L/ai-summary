/* frontend/js/components/provider-panel.js — 提供商配置面板 */

const ProviderPanel = {
    render() {
        const container = document.getElementById('provider-section');
        if (!container) return;

        const models = AppState.getCurrentModels();
        const modelKeys = Object.keys(models);
        const apiKey = AppState.getCurrentApiKey();

        container.innerHTML = `
            <h2>AI服务商设置</h2>
            <div class="form-group">
                <label>选择AI服务商:</label>
                <div class="custom-dropdown" id="provider-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('provider-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedProvider || '请选择')}</span>
                        <span class="dropdown-arrow">▼</span>
                    </div>
                    <div class="dropdown-content" id="provider-options">
                        ${AppState.providerNames.map(name => `
                            <div class="dropdown-option" onclick="ProviderPanel.selectProvider('${Utils.escapeHtml(name)}'); event.stopPropagation();">
                                <span>${Utils.escapeHtml(name)}</span>
                                <button type="button" class="delete-option-btn" onclick="ProviderPanel.deleteProvider('${Utils.escapeHtml(name)}'); event.stopPropagation();">×</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="ProviderPanel.addNew()">
                            <span>+ 新增服务商</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label>选择模型:</label>
                <div class="custom-dropdown" id="model-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('model-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedModel || '请选择')}</span>
                        <span class="dropdown-arrow">▼</span>
                    </div>
                    <div class="dropdown-content" id="model-options">
                        ${modelKeys.map(display => `
                            <div class="dropdown-option" onclick="ProviderPanel.selectModel('${Utils.escapeHtml(display)}')">
                                <span>${Utils.escapeHtml(display)}</span>
                                <button type="button" class="delete-option-btn" onclick="ProviderPanel.deleteModel('${Utils.escapeHtml(AppState.selectedProvider)}', '${Utils.escapeHtml(display)}'); event.stopPropagation();">×</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="ProviderPanel.addModel()">
                            <span>+ 新增模型</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label>${Utils.escapeHtml(AppState.selectedProvider || 'AI')} API Key:</label>
                <input type="text" id="api_key" value="${Utils.escapeHtml(apiKey)}" placeholder="${apiKey ? '已配置' : '请输入API Key'}">
                <button type="button" class="btn btn-secondary" style="margin-top: 5px;" onclick="ProviderPanel.saveApiKey()">保存API Key</button>
            </div>
            <div class="form-group">
                <label>📁 处理目录:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="text" id="directory_path" value="${Utils.escapeHtml(AppState.directoryPath)}" placeholder="输入要处理的目录的完整路径" style="flex: 1;">
                    <button type="button" class="btn btn-secondary" style="padding: 8px 16px; white-space: nowrap;" onclick="DirectoryBrowser.open()">
                        📁 浏览
                    </button>
                </div>
            </div>
        `;
    },

    async selectProvider(name) {
        closeAllDropdowns();
        try {
            await API.saveConfig({ selected_provider: name });
            AppState.selectedProvider = name;
            const models = AppState.getCurrentModels();
            AppState.selectedModel = Object.keys(models)[0] || '';
            AppState.apiKey = AppState.getCurrentApiKey();
            AppState.notify('provider-changed');
            this.render();
            showMessage('✅ 配置已保存', 'success');
        } catch (e) {
            showMessage('❌ 保存失败: ' + e.message, 'error');
        }
    },

    async selectModel(name) {
        closeAllDropdowns();
        try {
            await API.saveConfig({ selected_model: name });
            AppState.selectedModel = name;
            AppState.notify('model-changed');
            this.render();
            showMessage('✅ 配置已保存', 'success');
        } catch (e) {
            showMessage('❌ 保存失败: ' + e.message, 'error');
        }
    },

    async deleteProvider(name) {
        if (!confirm(`确定要删除AI提供商 '${name}' 吗？`)) return;
        try {
            await API.deleteProvider(name);
            await AppState.loadAll();
            AppState.notify('provider-deleted');
            this.render();
            TrashPanel.render();
        } catch (e) {
            showMessage('❌ 删除失败: ' + e.message, 'error');
        }
    },

    async deleteModel(providerName, modelDisplay) {
        if (!confirm(`确定要从提供商 '${providerName}' 中删除模型 '${modelDisplay}' 吗？`)) return;
        try {
            await API.deleteModel(providerName, modelDisplay);
            await AppState.loadAll();
            AppState.notify('model-deleted');
            this.render();
        } catch (e) {
            showMessage('❌ 删除失败: ' + e.message, 'error');
        }
    },

    async saveApiKey() {
        const input = document.getElementById('api_key');
        const key = input ? input.value.trim() : '';
        if (!AppState.selectedProvider) { alert('请先选择AI提供商'); return; }
        if (!key) { alert('请输入API Key'); return; }
        try {
            await API.saveApiKey(AppState.selectedProvider, key);
            AppState.apiKey = key;
            showMessage('✅ API Key 保存成功', 'success');
        } catch (e) {
            showMessage('❌ 保存失败: ' + e.message, 'error');
        }
    },

    addNew() {
        closeAllDropdowns();
        showDialog({
            title: '新增服务商',
            fields: [
                { id: 'new_provider_name', label: '服务商名称:', placeholder: '如: 阿里通义' },
                { id: 'new_provider_url', label: 'API地址:', placeholder: '如: https://api.openai.com/v1' },
                { id: 'new_provider_apikey', label: 'API Key:', placeholder: '可选' },
                { id: 'new_provider_model', label: '模型名称:', placeholder: '可选，如: gpt-4' }
            ],
            onSubmit: async () => {
                const name = document.getElementById('new_provider_name').value.trim();
                const url = document.getElementById('new_provider_url').value.trim();
                const apiKey = document.getElementById('new_provider_apikey').value.trim();
                const modelName = document.getElementById('new_provider_model').value.trim();
                if (!name || !url) { alert('请输入服务商名称和API地址'); return false; }
                const models = modelName ? { [modelName]: modelName } : { '默认模型': name.toLowerCase().replace(/\s+/g, '-') + '-model' };
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
        if (!AppState.selectedProvider) { alert('请先选择一个服务商'); return; }
        showDialog({
            title: `新增模型 - ${AppState.selectedProvider}`,
            fields: [
                { id: 'new_model_display', label: '模型显示名称:', placeholder: '如: GPT-4' },
                { id: 'new_model_id', label: '模型ID:', placeholder: '如: gpt-4' }
            ],
            onSubmit: async () => {
                const display = document.getElementById('new_model_display').value.trim();
                const id = document.getElementById('new_model_id').value.trim();
                if (!display || !id) { alert('请输入模型名称和ID'); return false; }
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
