/* frontend/js/components/prompt-panel.js — 提示词面板 */

const PromptPanel = {
    render() {
        const container = document.getElementById('prompt-section');
        if (!container) return;

        const currentContent = AppState.prompts[AppState.selectedPrompt] || '';

        container.innerHTML = `
            <h2>Prompt管理</h2>
            <div class="form-group">
                <label>选择System Prompt:</label>
                <div class="custom-dropdown" id="prompt-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('prompt-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedPrompt || '请选择')}</span>
                        <span class="dropdown-arrow">▼</span>
                    </div>
                    <div class="dropdown-content" id="prompt-options">
                        ${AppState.promptNames.map(name => `
                            <div class="dropdown-option" onclick="PromptPanel.selectPrompt('${Utils.escapeHtml(name)}'); event.stopPropagation();">
                                <span>${Utils.escapeHtml(name)}</span>
                                <button type="button" class="delete-option-btn" onclick="PromptPanel.deletePrompt('${Utils.escapeHtml(name)}'); event.stopPropagation();">×</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="PromptPanel.addNew()">
                            <span>+ 新增Prompt</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="custom-dropdown" id="prompt-content-dropdown">
                <div class="dropdown-selected" onclick="toggleDropdown('prompt-content-dropdown')">
                    <span>📄 查看当前Prompt内容</span>
                    <span class="dropdown-arrow">▼</span>
                </div>
                <div class="dropdown-content prompt-content-area" id="prompt-content-options" style="display: none;">
                    <textarea readonly rows="8" style="width: 100%; padding: 10px; border: none; resize: vertical; font-family: monospace; background-color: #f9f9f9; box-sizing: border-box;">${Utils.escapeHtml(currentContent)}</textarea>
                </div>
            </div>
        `;
    },

    async selectPrompt(name) {
        closeAllDropdowns();
        try {
            await API.saveConfig({ selected_prompt: name });
            AppState.selectedPrompt = name;
            AppState.notify('prompt-changed');
            this.render();
            showMessage('✅ 配置已保存', 'success');
        } catch (e) {
            showMessage('❌ 保存失败: ' + e.message, 'error');
        }
    },

    async deletePrompt(name) {
        if (!confirm(`确定要删除Prompt '${name}' 吗？`)) return;
        try {
            await API.deletePrompt(name);
            await AppState.loadAll();
            AppState.notify('prompt-deleted');
            this.render();
            TrashPanel.render();
        } catch (e) {
            showMessage('❌ 删除失败: ' + e.message, 'error');
        }
    },

    addNew() {
        closeAllDropdowns();
        showDialog({
            title: '新增Prompt',
            fields: [
                { id: 'new_prompt_name', label: 'Prompt名称:', placeholder: '如: 文章总结', type: 'text' },
                { id: 'new_prompt_content', label: 'Prompt内容:', placeholder: '请输入Prompt内容...', type: 'textarea' }
            ],
            onSubmit: async () => {
                const name = document.getElementById('new_prompt_name').value.trim();
                const content = document.getElementById('new_prompt_content').value.trim();
                if (!name || !content) { alert('请输入Prompt名称和内容'); return false; }
                await API.createPrompt({ name, content });
                await AppState.loadAll();
                AppState.notify('prompt-added');
                PromptPanel.render();
                return true;
            }
        });
    }
};

window.PromptPanel = PromptPanel;
