/* frontend/js/components/directory-browser.js — 目录浏览器 */

const DirectoryBrowser = {
    _currentPath: '',
    _selectedPath: '',

    open() {
        const modal = document.getElementById('directory-browser-modal');
        if (!modal) return;
        modal.style.display = 'flex';
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
        if (modal) modal.style.display = 'none';
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
                alert('加载失败: ' + (data.error || '未知错误'));
            }
        } catch (e) {
            alert('加载失败: ' + e.message);
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
            backBtn.style.display = 'inline-block';
            backBtn.dataset.parentPath = data.parent;
        } else {
            backBtn.style.display = 'none';
        }

        listEl.innerHTML = '';
        if (data.drives && data.drives.length > 0) {
            data.drives.forEach(drive => listEl.appendChild(this._createItem(drive, drive, '💻')));
        }
        if (data.directories && data.directories.length > 0) {
            data.directories.forEach(dir => listEl.appendChild(this._createItem(dir.name, dir.path, '📂')));
        } else if (!data.drives || data.drives.length === 0) {
            listEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">此目录下没有子目录</div>';
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
        if (this._selectedPath) {
            const dirInput = document.getElementById('directory_path');
            if (dirInput) dirInput.value = this._selectedPath;
            AppState.directoryPath = this._selectedPath;
            this.close();
            try {
                await API.saveConfig({ directory_path: this._selectedPath });
                showMessage('✅ 目录已选择', 'success');
            } catch (e) {
                console.error('保存目录路径失败:', e);
            }
        }
    }
};

window.DirectoryBrowser = DirectoryBrowser;
