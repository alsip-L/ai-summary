/* app.js — Entry point + initialization */

/* ========== Global Helpers ========== */

function showMessage(message, type = 'info') {
    const div = document.getElementById('message');
    if (!div) return;
    div.className = `alert alert-${type === 'error' ? 'danger' : type}`;
    div.textContent = message;
    div.classList.remove('hidden');
    div.style.animation = 'none';
    div.offsetHeight;
    div.style.animation = 'fixedSlideIn 0.3s ease-out';
    setTimeout(() => {
        div.style.animation = 'fixedFadeOut 0.3s ease-out';
        setTimeout(() => { div.classList.add('hidden'); }, 300);
    }, 2000);
}

function promptApiKey() {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        const dialog = document.createElement('div');
        dialog.className = 'modal-content';
        dialog.innerHTML = `
            <div class="modal-header"><h3>输入 API Key</h3></div>
            <div class="modal-body">
                <input type="text" id="api_key_input" class="form-control" placeholder="请输入 API Key">
            </div>
            <div class="modal-footer">
                <button id="cancel_api_key" class="btn btn-secondary btn-sm">取消</button>
                <button id="submit_api_key" class="btn btn-primary btn-sm">确定</button>
            </div>
        `;
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        document.getElementById('submit_api_key').onclick = () => {
            resolve(document.getElementById('api_key_input').value.trim());
            overlay.remove();
        };
        document.getElementById('cancel_api_key').onclick = () => { resolve(''); overlay.remove(); };
        overlay.onclick = (e) => { if (e.target === overlay) { resolve(''); overlay.remove(); } };
        dialog.querySelector('#api_key_input').focus();
    });
}

function showDialog({ title, fields, onSubmit }) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const dialog = document.createElement('div');
    dialog.className = 'modal-content';

    let bodyHtml = '';
    fields.forEach(f => {
        bodyHtml += `<div class="form-group">
            <label class="form-label">${f.label}</label>
            ${f.type === 'textarea'
                ? `<textarea id="${f.id}" class="form-control" placeholder="${f.placeholder || ''}"></textarea>`
                : `<input type="${f.type || 'text'}" id="${f.id}" class="form-control" placeholder="${f.placeholder || ''}">`
            }
        </div>`;
    });

    dialog.innerHTML = `
        <div class="modal-header"><h3>${Utils.escapeHtml(title)}</h3></div>
        <div class="modal-body">${bodyHtml}</div>
        <div class="modal-footer">
            <button id="dialog_cancel" class="btn btn-secondary btn-sm">取消</button>
            <button id="dialog_submit" class="btn btn-primary btn-sm">确定</button>
        </div>
    `;
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

/* ========== Dropdown Management ========== */

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        el.classList.remove('show');
    });
    document.querySelectorAll('.trash-content-area.show').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('show');
    });
}

window.toggleDropdown = function(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    let content;
    if (dropdownId === 'trash-dropdown') {
        content = document.getElementById('trash-options');
    } else {
        content = dropdown.querySelector('.dropdown-content');
    }
    if (!content) return;

    // Close others
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        if (el !== content) el.classList.remove('show');
    });
    document.querySelectorAll('.trash-content-area.show').forEach(el => {
        if (el !== content) { el.classList.add('hidden'); el.classList.remove('show'); }
    });

    // Toggle current
    if (dropdownId === 'trash-dropdown') {
        const isHidden = content.classList.contains('hidden') || !content.classList.contains('show');
        if (isHidden) {
            content.classList.remove('hidden');
            content.classList.add('show');
        } else {
            content.classList.add('hidden');
            content.classList.remove('show');
        }
    } else {
        content.classList.toggle('show');
    }
};

/* ========== Global Events ========== */

document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown') && !e.target.closest('.dropdown-content')) {
        closeAllDropdowns();
    }
});

window.addEventListener('scroll', (e) => {
    if (!e.target.closest('.modal-overlay') && !e.target.closest('.modal-content') && !e.target.closest('.sidebar-scroll')) {
        closeAllDropdowns();
    }
}, true);
window.addEventListener('resize', () => closeAllDropdowns());

/* ========== DOMContentLoaded ========== */

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Load all data
    try {
        await AppState.loadAll();
    } catch (e) {
        console.error('加载初始数据失败:', e);
    }

    // 2. Render components
    ProviderPanel.render();
    PromptPanel.render();
    TrashPanel.render();
    TaskProgress.render();

    // 3. Bind buttons
    const startBtn = document.getElementById('start-process-btn');
    if (startBtn) {
        startBtn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); TaskProgress.start(); };
    }

    const cancelBtn = document.getElementById('cancelProcessing');
    if (cancelBtn) {
        cancelBtn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); TaskProgress.cancel(); };
    }

    // 4. Directory browser global functions
    window.closeDirectoryBrowser = () => DirectoryBrowser.close();
    window.goBack = () => DirectoryBrowser.goBack();
    window.refreshDirectory = () => DirectoryBrowser.refresh();
    window.goToDirectPath = () => DirectoryBrowser.goToDirectPath();
    window.selectDirectory = () => DirectoryBrowser.selectDirectory();
});
