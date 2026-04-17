/* frontend/js/components/trash-panel.js — 回收站 */

const TrashPanel = {
    render() {
        const container = document.getElementById('trash-section');
        if (!container) return;

        const provKeys = Object.keys(AppState.trashProviders);
        const promptKeys = Object.keys(AppState.trashPrompts);

        container.innerHTML = `
            <div class="trash-section">
                <h4>已删除的提供商 (${provKeys.length}):</h4>
                ${provKeys.length > 0 ? provKeys.map(name => `
                    <div class="trash-item" style="display: flex; align-items: center; justify-content: space-between; border: 1px solid #ddd; padding: 8px; margin: 3px 0; border-radius: 3px; background-color: #f9f9f9;">
                        <span style="flex: 1; margin-right: 10px;">${Utils.escapeHtml(name)}</span>
                        <div style="display: flex; gap: 6px;">
                            <button type="button" class="restore-btn" onclick="TrashPanel.restoreProvider('${Utils.escapeHtml(name)}')">恢复</button>
                            <button type="button" class="permanent-delete-btn" onclick="TrashPanel.permanentDeleteProvider('${Utils.escapeHtml(name)}')">删除</button>
                        </div>
                    </div>
                `).join('') : '<p style="color: #666; font-style: italic;">暂无已删除的提供商</p>'}
            </div>
            <hr style="margin: 10px 0;">
            <div class="trash-section">
                <h4>已删除的Prompt (${promptKeys.length}):</h4>
                ${promptKeys.length > 0 ? promptKeys.map(name => `
                    <div class="trash-item" style="display: flex; align-items: center; justify-content: space-between; border: 1px solid #ddd; padding: 8px; margin: 3px 0; border-radius: 3px; background-color: #f9f9f9;">
                        <span style="flex: 1; margin-right: 10px;">${Utils.escapeHtml(name)}</span>
                        <div style="display: flex; gap: 6px;">
                            <button type="button" class="restore-btn" onclick="TrashPanel.restorePrompt('${Utils.escapeHtml(name)}')">恢复</button>
                            <button type="button" class="permanent-delete-btn" onclick="TrashPanel.permanentDeletePrompt('${Utils.escapeHtml(name)}')">删除</button>
                        </div>
                    </div>
                `).join('') : '<p style="color: #666; font-style: italic;">暂无已删除的Prompt</p>'}
            </div>
        `;
    },

    async restoreProvider(name) {
        try {
            await API.restoreProvider(name);
            await AppState.loadAll();
            ProviderPanel.render();
            this.render();
            showMessage('✅ 提供商已恢复', 'success');
        } catch (e) {
            showMessage('❌ 恢复失败: ' + e.message, 'error');
        }
    },

    async permanentDeleteProvider(name) {
        if (!confirm(`确定要永久删除AI提供商 '${name}' 吗？此操作不可恢复！`)) return;
        try {
            await API.permanentDeleteProvider(name);
            await AppState.loadAll();
            this.render();
            showMessage('✅ 已永久删除', 'success');
        } catch (e) {
            showMessage('❌ 删除失败: ' + e.message, 'error');
        }
    },

    async restorePrompt(name) {
        try {
            await API.restorePrompt(name);
            await AppState.loadAll();
            PromptPanel.render();
            this.render();
            showMessage('✅ Prompt已恢复', 'success');
        } catch (e) {
            showMessage('❌ 恢复失败: ' + e.message, 'error');
        }
    },

    async permanentDeletePrompt(name) {
        if (!confirm(`确定要永久删除Prompt '${name}' 吗？此操作不可恢复！`)) return;
        try {
            await API.permanentDeletePrompt(name);
            await AppState.loadAll();
            this.render();
            showMessage('✅ 已永久删除', 'success');
        } catch (e) {
            showMessage('❌ 删除失败: ' + e.message, 'error');
        }
    }
};

window.TrashPanel = TrashPanel;
