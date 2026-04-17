/* settings-panel.js — System settings panel */

const SettingsPanel = {
    render() {
        const container = document.getElementById('settings-section');
        if (!container) return;

        const s = AppState.systemSettings;
        const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

        container.innerHTML = `
            <div class="system-settings-form">
                <div class="form-group">
                    <label>日志级别 <span class="badge badge-live">即时</span></label>
                    <select id="sys_debug_level" class="form-control">
                        ${levels.map(l => `<option value="${l}" ${s.debug_level === l ? 'selected' : ''}>${l}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Flask 密钥 <span class="badge badge-restart">重启</span></label>
                    <input type="text" id="sys_flask_secret" class="form-control" value="${Utils.escapeHtml(s.flask_secret_key)}" placeholder="密钥" style="font-family: var(--font-mono);">
                </div>
                <div class="form-group">
                    <label>主机 <span class="badge badge-restart">重启</span></label>
                    <input type="text" id="sys_host" class="form-control" value="${Utils.escapeHtml(s.host)}" placeholder="0.0.0.0">
                </div>
                <div class="form-group">
                    <label>端口 <span class="badge badge-restart">重启</span></label>
                    <input type="number" id="sys_port" class="form-control" value="${s.port}" min="1" max="65535" placeholder="5000">
                </div>
                <div class="form-group">
                    <label style="cursor: pointer;">
                        <input type="checkbox" id="sys_debug" ${s.debug ? 'checked' : ''} style="margin-right: 6px;">
                        调试模式
                        <span class="badge badge-restart" style="margin-left: auto;">重启</span>
                    </label>
                </div>
                <button type="button" class="btn btn-primary w-full" onclick="SettingsPanel.save()">保存设置</button>
                <div id="system-settings-message" class="system-settings-message"></div>
            </div>
        `;
    },

    async save() {
        const data = {
            debug_level: document.getElementById('sys_debug_level').value,
            flask_secret_key: document.getElementById('sys_flask_secret').value,
            host: document.getElementById('sys_host').value,
            port: parseInt(document.getElementById('sys_port').value),
            debug: document.getElementById('sys_debug').checked
        };

        const msgEl = document.getElementById('system-settings-message');
        try {
            const result = await API.saveSystemSettings(data);
            if (result.success) {
                if (result.needs_restart) {
                    msgEl.className = 'system-settings-message warning';
                    msgEl.textContent = '已保存，部分设置需重启生效';
                } else {
                    msgEl.className = 'system-settings-message success';
                    msgEl.textContent = '已保存并生效';
                }
            } else {
                msgEl.className = 'system-settings-message error';
                msgEl.textContent = result.error || '保存失败';
            }
            setTimeout(() => { msgEl.className = 'system-settings-message'; }, 4000);
        } catch (e) {
            msgEl.className = 'system-settings-message error';
            msgEl.textContent = '保存失败: ' + e.message;
            setTimeout(() => { msgEl.className = 'system-settings-message'; }, 4000);
        }
    }
};

window.SettingsPanel = SettingsPanel;
