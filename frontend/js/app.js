/* frontend/js/app.js — 入口 + 初始化 */

/* ========== 全局辅助函数 ========== */

/** 显示消息提示 */
function showMessage(message, type = 'info') {
    const div = document.getElementById('message');
    if (!div) return;
    div.className = `alert alert-${type === 'error' ? 'danger' : type}`;
    div.textContent = message;
    div.style.display = 'block';
    div.style.animation = 'none';
    div.offsetHeight; // 触发重绘
    div.style.animation = 'fixedSlideIn 0.3s ease-out';
    setTimeout(() => {
        div.style.animation = 'fixedFadeOut 0.3s ease-out';
        setTimeout(() => { div.style.display = 'none'; }, 300);
    }, 2000);
}

/** 弹出 API Key 输入框 */
function promptApiKey() {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';
        const dialog = document.createElement('div');
        dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;min-width:350px;max-width:90%;';
        dialog.innerHTML = `
            <h3 style="margin:0 0 15px 0;">输入API Key</h3>
            <div style="margin-bottom:15px;">
                <input type="password" id="api_key_input" style="width:100%;padding:10px;box-sizing:border-box;" placeholder="请输入API Key">
            </div>
            <div style="text-align:right;">
                <button id="cancel_api_key" style="padding:8px 15px;margin-right:10px;cursor:pointer;">取消</button>
                <button id="submit_api_key" style="padding:8px 15px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;">确定</button>
            </div>
        `;
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        document.getElementById('submit_api_key').onclick = () => {
            resolve(document.getElementById('api_key_input').value.trim());
            overlay.remove();
        };
        document.getElementById('cancel_api_key').onclick = () => { resolve(''); overlay.remove(); };
        dialog.querySelector('#api_key_input').focus();
    });
}

/** 通用对话框 */
function showDialog({ title, fields, onSubmit }) {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';
    const dialog = document.createElement('div');
    dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;min-width:400px;max-width:90%;';
    let html = `<h3 style="margin:0 0 15px 0;">${Utils.escapeHtml(title)}</h3>`;
    fields.forEach(f => {
        html += `<div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">${f.label}</label>
            ${f.type === 'textarea'
                ? `<textarea id="${f.id}" style="width:100%;min-height:100px;padding:8px;box-sizing:border-box;" placeholder="${f.placeholder || ''}"></textarea>`
                : `<input type="${f.type || 'text'}" id="${f.id}" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="${f.placeholder || ''}">`
            }
        </div>`;
    });
    html += `<div style="text-align:right;">
        <button id="dialog_cancel" style="padding:8px 15px;margin-right:10px;cursor:pointer;">取消</button>
        <button id="dialog_submit" style="padding:8px 15px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;">确定</button>
    </div>`;
    dialog.innerHTML = html;
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    dialog.querySelector(`#${fields[0].id}`).focus();

    document.getElementById('dialog_submit').onclick = async () => {
        const ok = await onSubmit();
        if (ok !== false) overlay.remove();
    };
    document.getElementById('dialog_cancel').onclick = () => overlay.remove();
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
}

/* ========== 下拉菜单管理 ========== */

const _dropdownOriginalParents = new Map();

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        el.classList.remove('show');
        if (_dropdownOriginalParents.has(el)) {
            _dropdownOriginalParents.get(el).appendChild(el);
            _dropdownOriginalParents.delete(el);
        }
    });
    document.querySelectorAll('.prompt-content-area, .trash-content-area, .system-settings-area').forEach(el => {
        el.style.display = 'none';
    });
}

window.toggleDropdown = function(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    let content;
    if (dropdownId === 'prompt-content-dropdown') {
        content = document.getElementById('prompt-content-options');
    } else if (dropdownId === 'trash-dropdown') {
        content = document.getElementById('trash-options');
    } else if (dropdownId === 'system-settings-dropdown') {
        content = document.getElementById('system-settings-content');
    } else {
        content = dropdown.querySelector('.dropdown-content');
    }
    if (!content) return;

    // 关闭其他
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        if (el !== content) {
            el.classList.remove('show');
            if (_dropdownOriginalParents.has(el)) {
                _dropdownOriginalParents.get(el).appendChild(el);
                _dropdownOriginalParents.delete(el);
            }
        }
    });
    document.querySelectorAll('.prompt-content-area, .trash-content-area, .system-settings-area').forEach(el => {
        if (el !== content && el.style.display !== 'none') el.style.display = 'none';
    });

    if (['prompt-content-dropdown', 'trash-dropdown', 'system-settings-dropdown'].includes(dropdownId)) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    } else {
        const isShowing = content.classList.contains('show');
        if (isShowing) {
            content.classList.remove('show');
            if (_dropdownOriginalParents.has(content)) {
                _dropdownOriginalParents.get(content).appendChild(content);
                _dropdownOriginalParents.delete(content);
            }
        } else {
            if (!_dropdownOriginalParents.has(content)) {
                _dropdownOriginalParents.set(content, content.parentElement);
            }
            document.body.appendChild(content);
            content.classList.add('show');
            positionDropdown(dropdown, content);
        }
    }
};

function positionDropdown(dropdown, content) {
    const selected = dropdown.querySelector('.dropdown-selected');
    if (!selected) return;
    const rect = selected.getBoundingClientRect();
    const maxH = 320;
    let top = rect.bottom + 6;
    if (top + maxH > window.innerHeight) top = Math.max(4, rect.top - maxH - 6);
    let left = Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8));
    content.style.top = top + 'px';
    content.style.left = left + 'px';
    content.style.width = rect.width + 'px';
}

window.positionDropdown = positionDropdown;

/* ========== 主题切换 ========== */

function setupThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const theme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
        AppState.theme = theme;
    });
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

/* ========== 全局事件 ========== */

document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown') && !e.target.closest('.dropdown-content')) {
        closeAllDropdowns();
    }
});

window.addEventListener('scroll', () => closeAllDropdowns(), true);
window.addEventListener('resize', () => closeAllDropdowns());

/* ========== DOMContentLoaded 初始化 ========== */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('初始化前端应用...');

    // 1. 加载全部数据
    try {
        await AppState.loadAll();
    } catch (e) {
        console.error('加载初始数据失败:', e);
    }

    // 2. 渲染各组件
    ProviderPanel.render();
    PromptPanel.render();
    TrashPanel.render();
    SettingsPanel.render();

    // 3. 绑定按钮事件
    const startBtn = document.getElementById('start-process-btn');
    if (startBtn) {
        startBtn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); TaskProgress.start(); };
    }

    const cancelBtn = document.getElementById('cancelProcessing');
    if (cancelBtn) {
        cancelBtn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); TaskProgress.cancel(); };
    }

    // 4. 主题
    setupThemeToggle();

    // 5. 目录浏览器全局函数绑定（兼容 onclick）
    window.closeDirectoryBrowser = () => DirectoryBrowser.close();
    window.goBack = () => DirectoryBrowser.goBack();
    window.refreshDirectory = () => DirectoryBrowser.refresh();
    window.goToDirectPath = () => DirectoryBrowser.goToDirectPath();
    window.selectDirectory = () => DirectoryBrowser.selectDirectory();
    window.saveSystemSettings = () => SettingsPanel.save();

    console.log('前端应用初始化完成');
});
