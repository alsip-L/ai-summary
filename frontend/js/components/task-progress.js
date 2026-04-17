/* task-progress.js — Task progress monitoring */

const TaskProgress = {
    _interval: null,
    _startTime: null,
    _lastStatus: null,

    render() {
        this._checkRunningTask();
    },

    _showPanel() {
        const panel = document.getElementById('processing-progress');
        const empty = document.getElementById('empty-state');
        if (panel) { panel.classList.remove('hidden'); panel.classList.add('visible'); }
        if (empty) empty.classList.add('hidden');
    },

    _hidePanel() {
        const panel = document.getElementById('processing-progress');
        const empty = document.getElementById('empty-state');
        if (panel) { panel.classList.add('hidden'); panel.classList.remove('visible'); }
        if (empty) empty.classList.remove('hidden');
    },

    async _checkRunningTask() {
        try {
            const status = await API.getProcessingStatus();
            if (['processing', 'scanning'].includes(status.status)) {
                AppState.isProcessing = true;
                this._startTime = status.start_time ? status.start_time * 1000 : Date.now();
                this._showPanel();
                this.updateUI(status);
                this.startMonitoring();
            }
        } catch (e) {
            console.error('检查运行中任务失败:', e);
        }
    },

    async start() {
        if (AppState.isProcessing) {
            showMessage('正在处理中，请稍候', 'warning');
            return;
        }

        const dirInput = document.getElementById('directory_path');
        const directory = dirInput ? dirInput.value.trim() : AppState.directoryPath;
        if (!directory) { showMessage('请输入处理目录路径', 'error'); return; }
        if (!AppState.selectedProvider) { showMessage('请选择 AI 服务商', 'error'); return; }
        if (!AppState.selectedModel) { showMessage('请选择模型', 'error'); return; }
        if (!AppState.selectedPrompt) { showMessage('请选择提示词', 'error'); return; }

        let apiKey = AppState.apiKey || (document.getElementById('api_key') ? document.getElementById('api_key').value.trim() : '');
        if (!apiKey) {
            apiKey = await promptApiKey();
            if (!apiKey) { showMessage('必须提供 API Key', 'error'); return; }
        }

        this._showPanel();
        AppState.isProcessing = true;
        this._startTime = Date.now();
        this.updateUI({ status: 'scanning', progress: 0 });

        try {
            const result = await API.startProcessing({
                directory: directory,
                provider: AppState.selectedProvider,
                model: AppState.selectedModel,
                prompt: AppState.selectedPrompt,
                api_key: apiKey
            });
            if (result.success) {
                showMessage(result.message || '处理已启动', 'success');
                this.startMonitoring();
            } else {
                throw new Error(result.error || result.message || '启动失败');
            }
        } catch (e) {
            showMessage(`启动失败: ${e.message}`, 'error');
            AppState.isProcessing = false;
            this._hidePanel();
        }
    },

    startMonitoring() {
        if (this._interval) clearInterval(this._interval);
        this._interval = setInterval(async () => {
            try {
                const status = await API.getProcessingStatus();
                this.updateUI(status);
                if (['completed', 'error', 'cancelled'].includes(status.status)) {
                    AppState.isProcessing = false;
                    clearInterval(this._interval);
                    this._interval = null;
                    if (status.status === 'completed') {
                        const dur = (Date.now() - this._startTime) / 1000;
                        showMessage(`处理完成！耗时: ${Utils.formatDuration(dur)}`, 'success');
                    } else if (status.status === 'error') {
                        showMessage(`处理失败: ${status.error}`, 'error');
                    }
                }
            } catch (e) {
                console.error('获取状态失败:', e);
            }
        }, 2000);
    },

    async cancel() {
        if (!AppState.isProcessing) { showMessage('当前不在处理状态', 'info'); return; }
        if (!confirm('确定要取消当前处理吗？')) return;
        try {
            await API.cancelProcessing();
            if (this._interval) { clearInterval(this._interval); this._interval = null; }
            AppState.isProcessing = false;
            this._hidePanel();
            this.updateUI({ status: 'cancelled', progress: 0, error: '用户取消了处理' });
            showMessage('处理已取消', 'warning');
        } catch (e) {
            showMessage(`取消失败: ${e.message}`, 'error');
        }
    },

    updateUI(status) {
        if (this._lastStatus && this._areEqual(this._lastStatus, status)) return;
        this._lastStatus = { ...status };

        const fill = document.getElementById('progressFill');
        const pct = document.getElementById('progressPercentage');
        if (fill) fill.style.width = `${status.progress || 0}%`;
        if (pct) pct.textContent = `${status.progress || 0}%`;

        const title = document.getElementById('statusTitle');
        const msg = document.getElementById('statusMessage');
        const icon = document.getElementById('statusIcon');
        const info = this._statusInfo(status.status || 'idle', status);
        if (title) title.textContent = info.title;
        if (msg) msg.textContent = info.message;
        if (icon) icon.textContent = info.icon;

        const curFile = document.getElementById('currentFile');
        const files = document.getElementById('progressFiles');
        const elapsed = document.getElementById('elapsedTime');
        if (curFile) curFile.textContent = status.current_file || '-';
        if (files) files.textContent = `${status.processed_files_count || 0} / ${status.total_files || 0}`;
        if (elapsed && this._startTime) elapsed.textContent = Utils.formatDuration(Math.floor((Date.now() - this._startTime) / 1000));

        this._updatePanelStyle(status.status || 'idle');

        if (status.results && status.results.length > 0) {
            ResultTable.display(status.results);
        }
    },

    _statusInfo(s, data) {
        const map = {
            idle: { title: '就绪', message: '等待开始处理...', icon: '' },
            scanning: { title: '扫描文件', message: '正在扫描目录...', icon: '' },
            processing: { title: '正在处理', message: data.current_file ? `当前文件: ${data.current_file}` : '正在处理文件...', icon: '' },
            completed: { title: '处理完成', message: '所有文件处理完成', icon: '' },
            error: { title: '处理错误', message: `处理失败: ${data.error || '未知错误'}`, icon: '' },
            cancelled: { title: '已取消', message: '处理已被用户取消', icon: '' }
        };
        return map[s] || map.idle;
    },

    _updatePanelStyle(status) {
        const panel = document.getElementById('processing-progress');
        if (!panel) return;
        panel.classList.remove('idle', 'processing', 'completed', 'error', 'scanning', 'cancelled');
        panel.classList.add(status);
        const glow = panel.querySelector('.progress-glow');
        if (glow) glow.classList.toggle('active', status === 'processing' || status === 'scanning');
        const cancelBtn = document.getElementById('cancelProcessing');
        if (cancelBtn) {
            if (status === 'processing' || status === 'scanning') {
                cancelBtn.classList.remove('hidden');
            } else {
                cancelBtn.classList.add('hidden');
            }
        }
    },

    _areEqual(a, b) {
        if (!a || !b) return false;
        const keys = ['status', 'progress', 'current_file', 'processed_files_count', 'total_files'];
        for (const k of keys) { if (a[k] !== b[k]) return false; }
        return (a.results?.length || 0) === (b.results?.length || 0);
    }
};

window.TaskProgress = TaskProgress;
