/* frontend/js/components/settings-panel.js — 系统设置 */

const SettingsPanel = {
    render() {
        const container = document.getElementById('settings-section');
        if (!container) return;

        const s = AppState.systemSettings;
        const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
        const levelLabels = { DEBUG: '调试', INFO: '信息', WARNING: '警告', ERROR: '错误', CRITICAL: '严重' };

        container.innerHTML = `
            <div class="system-settings-form">
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="sys_debug_level" style="font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                        日志级别
                        <span style="font-size: 11px; color: #28a745; background: #e8f5e9; padding: 1px 6px; border-radius: 3px;">即时生效</span>
                    </label>
                    <select id="sys_debug_level" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; background: #fff;">
                        ${levels.map(l => `<option value="${l}" ${s.debug_level === l ? 'selected' : ''}>${l} - ${levelLabels[l]}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="sys_flask_secret" style="font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                        Flask密钥
                        <span style="font-size: 11px; color: #ffc107; background: #fff8e1; padding: 1px 6px; border-radius: 3px;">需重启</span>
                    </label>
                    <input type="text" id="sys_flask_secret" value="${Utils.escapeHtml(s.flask_secret_key)}" placeholder="Flask Secret Key" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; font-family: monospace;">
                </div>
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="sys_host" style="font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                        监听地址
                        <span style="font-size: 11px; color: #ffc107; background: #fff8e1; padding: 1px 6px; border-radius: 3px;">需重启</span>
                    </label>
                    <input type="text" id="sys_host" value="${Utils.escapeHtml(s.host)}" placeholder="0.0.0.0" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                </div>
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="sys_port" style="font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                        监听端口
                        <span style="font-size: 11px; color: #ffc107; background: #fff8e1; padding: 1px 6px; border-radius: 3px;">需重启</span>
                    </label>
                    <input type="number" id="sys_port" value="${s.port}" min="1" max="65535" placeholder="5000" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                </div>
                <div class="form-group" style="margin-bottom: 14px;">
                    <label style="font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="sys_debug" ${s.debug ? 'checked' : ''} style="width: 16px; height: 16px; cursor: pointer;">
                        Debug模式
                        <span style="font-size: 11px; color: #ffc107; background: #fff8e1; padding: 1px 6px; border-radius: 3px; margin-left: auto;">需重启</span>
                    </label>
                </div>
                <button type="button" class="btn btn-primary" onclick="SettingsPanel.save()" style="width: 100%; padding: 8px; font-size: 13px;">💾 保存系统设置</button>
                <div id="system-settings-message" style="margin-top: 8px; font-size: 12px; display: none;"></div>
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
                    msgEl.style.color = '#856404';
                    msgEl.style.backgroundColor = '#fff3cd';
                    msgEl.textContent = '⚠️ 设置已保存，部分配置需重启应用后生效';
                } else {
                    msgEl.style.color = '#155724';
                    msgEl.style.backgroundColor = '#d4edda';
                    msgEl.textContent = '✅ 设置已保存并即时生效';
                }
            } else {
                msgEl.style.color = '#721c24';
                msgEl.style.backgroundColor = '#f8d7da';
                msgEl.textContent = '❌ ' + (result.message || '保存失败');
            }
            msgEl.style.display = 'block';
            msgEl.style.padding = '6px 10px';
            msgEl.style.borderRadius = '4px';
            setTimeout(() => { msgEl.style.display = 'none'; }, 5000);
        } catch (e) {
            msgEl.style.color = '#721c24';
            msgEl.style.backgroundColor = '#f8d7da';
            msgEl.style.display = 'block';
            msgEl.style.padding = '6px 10px';
            msgEl.style.borderRadius = '4px';
            msgEl.textContent = '❌ 保存失败: ' + e.message;
            setTimeout(() => { msgEl.style.display = 'none'; }, 5000);
        }
    }
};

window.SettingsPanel = SettingsPanel;
