/* directory-browser.js — Directory browser modal */

const DirectoryBrowser = {
    _currentPath: '',
    _selectedPath: '',

    open() {
        const modal = document.getElementById('directory-browser-modal');
        if (!modal) return;
        modal.classList.remove('hidden');
        this._currentPath = '';
        this._selectedPath = '';

        const dirInput = document.getElementById('directory_path');
        if (dirInput && dirInput.value) {
            this.navigateTo(dirInput.value);
        } else {
            this._loadContents('');
        }

        modal.onclick = (e) => { if (e.target === modal) this.close(); };
        document.addEventListener('keydown', this._escHandler);
    },

    close() {
        const modal = document.getElementById('directory-browser-modal');
        if (modal) modal.classList.add('hidden');
        document.removeEventListener('keydown', this._escHandler);
    },

    _escHandler(e) {
        if (e.key === 'Escape') DirectoryBrowser.close();
    },

    async _loadContents(path) {
        try {
            const data = await API.getDirectoryContents(path);
            if (data.success) {
                this._renderContents(data);
            } else {
                showMessage('加载失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (e) {
            showMessage('加载失败: ' + e.message, 'error');
        }
    },

    _renderContents(data) {
        const listEl = document.getElementById('directory-list');
        const pathEl = document.getElementById('browser-current-path');
        const backBtn = document.getElementById('browser-back-btn');
        const selectBtn = document.getElementById('select-directory-btn');
        if (!listEl || !pathEl) return;

        this._currentPath = data.path || '';
        pathEl.textContent = data.path || '选择驱动器';

        if (data.parent) {
            backBtn.classList.remove('hidden');
            backBtn.dataset.parentPath = data.parent;
        } else {
            backBtn.classList.add('hidden');
        }

        listEl.innerHTML = '';
        if (data.drives && data.drives.length > 0) {
            data.drives.forEach(drive => listEl.appendChild(this._createItem(drive, drive, '\uD83D\uDCBB')));
        }
        if (data.directories && data.directories.length > 0) {
            data.directories.forEach(dir => listEl.appendChild(this._createItem(dir.name, dir.path, '\uD83D\uDCC2')));
        } else if (!data.drives || data.drives.length === 0) {
            listEl.innerHTML = '<div class="empty-state"><div class="empty-state-text">此目录下没有子目录</div></div>';
        }

        if (data.path) {
            selectBtn.disabled = false;
            this._selectedPath = data.path;
        } else {
            selectBtn.disabled = true;
            this._selectedPath = '';
        }
    },

    _createItem(name, path, icon) {
        const item = document.createElement('div');
        item.className = 'directory-item';
        item.innerHTML = `<span class="directory-icon">${icon}</span><span class="directory-name">${Utils.escapeHtml(name)}</span>`;
        item.onclick = () => this.navigateTo(path);
        return item;
    },

    navigateTo(path) {
        this._loadContents(path);
    },

    goBack() {
        const backBtn = document.getElementById('browser-back-btn');
        if (backBtn && backBtn.dataset.parentPath) {
            this.navigateTo(backBtn.dataset.parentPath);
        }
    },

    refresh() {
        this._loadContents(this._currentPath);
    },

    goToDirectPath() {
        const input = document.getElementById('direct-path-input');
        if (input && input.value.trim()) {
            this.navigateTo(input.value.trim());
        }
    },

    async selectDirectory() {
        const selectedPath = this._selectedPath;
        if (!selectedPath) {
            showMessage('请先选择一个目录', 'warning');
            return;
        }
        const dirInput = document.getElementById('directory_path');
        if (dirInput) dirInput.value = selectedPath;
        AppState.directoryPath = selectedPath;
        this.close();
        try {
            await API.savePreferences({ directory_path: selectedPath });
            showMessage('目录已选择', 'success');
        } catch (e) {
            console.error('保存目录路径失败:', e);
        }
    }
};

window.DirectoryBrowser = DirectoryBrowser;
