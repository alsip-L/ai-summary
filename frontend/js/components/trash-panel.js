/* trash-panel.js — Trash panel */

const TrashPanel = {
    render() {
        const container = document.getElementById('trash-section');
        const dropdown = document.getElementById('trash-dropdown');
        const countEl = document.getElementById('trash-count');
        if (!container) return;

        const provKeys = Object.keys(AppState.trashProviders);
        const promptKeys = Object.keys(AppState.trashPrompts);
        const total = provKeys.length + promptKeys.length;

        // Hide entire trash section when empty
        if (!dropdown) return;
        if (total === 0) {
            dropdown.classList.add('hidden');
            return;
        }
        dropdown.classList.remove('hidden');
        if (countEl) countEl.textContent = total;

        container.innerHTML = `
            <div class="trash-section">
                <h4>服务商 (${provKeys.length})</h4>
                ${provKeys.length > 0 ? provKeys.map(name => `
                    <div class="trash-item-row">
                        <span class="trash-item">${Utils.escapeHtml(name)}</span>
                        <div class="flex gap-1">
                            <button type="button" class="restore-btn" onclick="TrashPanel.restoreProvider('${Utils.escapeHtml(name)}')">恢复</button>
                            <button type="button" class="permanent-delete-btn" onclick="TrashPanel.permanentDeleteProvider('${Utils.escapeHtml(name)}')">删除</button>
                        </div>
                    </div>
                `).join('') : '<p class="empty-state-text">空</p>'}
            </div>
            <div class="sidebar-divider"></div>
            <div class="trash-section">
                <h4>提示词 (${promptKeys.length})</h4>
                ${promptKeys.length > 0 ? promptKeys.map(name => `
                    <div class="trash-item-row">
                        <span class="trash-item">${Utils.escapeHtml(name)}</span>
                        <div class="flex gap-1">
                            <button type="button" class="restore-btn" onclick="TrashPanel.restorePrompt('${Utils.escapeHtml(name)}')">恢复</button>
                            <button type="button" class="permanent-delete-btn" onclick="TrashPanel.permanentDeletePrompt('${Utils.escapeHtml(name)}')">删除</button>
                        </div>
                    </div>
                `).join('') : '<p class="empty-state-text">空</p>'}
            </div>
        `;
    },

    async restoreProvider(name) {
        try {
            await API.restoreProvider(name);
            await AppState.loadAll();
            ProviderPanel.render();
            this.render();
            showMessage('服务商已恢复', 'success');
        } catch (e) {
            showMessage('恢复失败: ' + e.message, 'error');
        }
    },

    async permanentDeleteProvider(name) {
        if (!confirm(`永久删除 '${name}'？此操作不可撤销。`)) return;
        try {
            await API.permanentDeleteProvider(name);
            await AppState.loadAll();
            this.render();
            showMessage('已永久删除', 'success');
        } catch (e) {
            showMessage('删除失败: ' + e.message, 'error');
        }
    },

    async restorePrompt(name) {
        try {
            await API.restorePrompt(name);
            await AppState.loadAll();
            PromptPanel.render();
            this.render();
            showMessage('提示词已恢复', 'success');
        } catch (e) {
            showMessage('恢复失败: ' + e.message, 'error');
        }
    },

    async permanentDeletePrompt(name) {
        if (!confirm(`永久删除提示词 '${name}'？此操作不可撤销。`)) return;
        try {
            await API.permanentDeletePrompt(name);
            await AppState.loadAll();
            this.render();
            showMessage('已永久删除', 'success');
        } catch (e) {
            showMessage('删除失败: ' + e.message, 'error');
        }
    }
};

window.TrashPanel = TrashPanel;
