/* prompt-panel.js — Prompt management panel */

const PromptPanel = {
    render() {
        const container = document.getElementById('prompt-section');
        if (!container) return;

        const currentContent = AppState.prompts[AppState.selectedPrompt] || '';

        container.innerHTML = `
            <div class="section-header">提示词</div>
            <div class="form-group">
                <label class="form-label">系统提示词</label>
                <div class="custom-dropdown" id="prompt-dropdown">
                    <div class="dropdown-selected" onclick="toggleDropdown('prompt-dropdown')">
                        <span>${Utils.escapeHtml(AppState.selectedPrompt || '请选择...')}</span>
                        <span class="dropdown-arrow">&#9662;</span>
                    </div>
                    <div class="dropdown-content" id="prompt-options">
                        ${AppState.promptNames.map(name => `
                            <div class="dropdown-option" onclick="PromptPanel.selectPrompt('${Utils.escapeHtml(name)}'); event.stopPropagation();">
                                <span>${Utils.escapeHtml(name)}</span>
                                <button type="button" class="delete-option-btn" onclick="PromptPanel.deletePrompt('${Utils.escapeHtml(name)}'); event.stopPropagation();">&times;</button>
                            </div>
                        `).join('')}
                        <div class="dropdown-option" onclick="PromptPanel.addNew(); event.stopPropagation();">
                            <span style="color: var(--accent-indigo);">+ 新增提示词</span>
                        </div>
                    </div>
                </div>
            </div>
            ${currentContent ? `
            <div class="prompt-preview">
                <label class="form-label">内容预览</label>
                <textarea readonly rows="4" class="form-control prompt-preview-text">${Utils.escapeHtml(currentContent)}</textarea>
            </div>` : ''}
        `;
    },

    async selectPrompt(name) {
        closeAllDropdowns();
        try {
            await API.savePreferences({ selected_prompt: name });
            AppState.selectedPrompt = name;

            this.render();
            showMessage('已保存', 'success');
        } catch (e) {
            showMessage('保存失败: ' + e.message, 'error');
        }
    },

    async deletePrompt(name) {
        closeAllDropdowns();
        if (!confirm(`确定删除提示词 '${name}' 吗？`)) return;
        try {
            await API.deletePrompt(name);
            await AppState.loadAll();

            this.render();
            TrashPanel.render();
        } catch (e) {
            showMessage('删除失败: ' + e.message, 'error');
        }
    },

    addNew() {
        closeAllDropdowns();
        showDialog({
            title: '新增提示词',
            fields: [
                { id: 'new_prompt_name', label: '名称', placeholder: '如: 文章摘要', type: 'text' },
                { id: 'new_prompt_content', label: '内容', placeholder: '输入提示词内容...', type: 'textarea' }
            ],
            onSubmit: async () => {
                const name = document.getElementById('new_prompt_name').value.trim();
                const content = document.getElementById('new_prompt_content').value.trim();
                if (!name || !content) { showMessage('两项均为必填', 'warning'); return false; }
                await API.createPrompt({ name, content });
                await AppState.loadAll();

                PromptPanel.render();
                return true;
            }
        });
    }
};

window.PromptPanel = PromptPanel;
