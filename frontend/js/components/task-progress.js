/* frontend/js/components/task-progress.js — 任务进度 */

const TaskProgress = {
    _interval: null,
    _startTime: null,
    _lastStatus: null,

    render() {
        const container = document.getElementById('processing-progress');
        if (!container) return;
        // 静态结构由 index.html 提供，此组件只做动态更新
    },

    async start() {
        if (AppState.isProcessing) {
            showMessage('正在处理中，请稍候...', 'warning');
            return;
        }

        const dirInput = document.getElementById('directory_path');
        const directory = dirInput ? dirInput.value.trim() : AppState.directoryPath;
        if (!directory) { showMessage('请输入处理目录路径', 'error'); return; }
        if (!AppState.selectedProvider) { showMessage('请选择AI服务商', 'error'); return; }
        if (!AppState.selectedModel) { showMessage('请选择AI模型', 'error'); return; }
        if (!AppState.selectedPrompt) { showMessage('请选择提示词', 'error'); return; }

        let apiKey = AppState.apiKey || (document.getElementById('api_key') ? document.getElementById('api_key').value.trim() : '');
        if (!apiKey) {
            apiKey = await promptApiKey();
            if (!apiKey) { showMessage('必须提供API Key', 'error'); return; }
        }

        // 显示进度面板
        const panel = document.getElementById('processing-progress');
        if (panel) { panel.style.display = 'block'; panel.classList.add('visible'); }

        AppState.isProcessing = true;
        this._startTime = Date.now();
        this.updateUI({ status: 'started', progress: 0 });

        try {
            const result = await API.startProcessing({
                directory_path: directory,
                selected_provider: AppState.selectedProvider,
                selected_model: AppState.selectedModel,
                selected_prompt: AppState.selectedPrompt,
                api_key: apiKey
            });
            if (result.status === 'started') {
                showMessage(result.message || '处理已启动', 'success');
                this.startMonitoring();
            } else {
                throw new Error(result.message || '启动失败');
            }
        } catch (e) {
            showMessage(`启动失败: ${e.message}`, 'error');
            AppState.isProcessing = false;
            if (panel) panel.style.display = 'none';
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
            const panel = document.getElementById('processing-progress');
            if (panel) panel.style.display = 'none';
            this.updateUI({ status: 'cancelled', progress: 0, error: '用户取消了处理' });
            showMessage('处理已取消', 'warning');
        } catch (e) {
            showMessage(`取消处理失败: ${e.message}`, 'error');
        }
    },

    updateUI(status) {
        // 避免不必要的更新
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
            idle: { title: '待机', message: '等待开始处理...', icon: '⏸️' },
            started: { title: '准备处理', message: '正在初始化处理流程...', icon: '🚀' },
            scanning: { title: '扫描文件', message: '正在扫描目录中的文件...', icon: '🔍' },
            processing: { title: '正在处理', message: data.current_file ? `正在处理文件: ${data.current_file}` : '正在处理文件...', icon: '⚙️' },
            completed: { title: '处理完成', message: '所有文件处理完成！', icon: '✅' },
            error: { title: '处理错误', message: `处理失败: ${data.error || '未知错误'}`, icon: '❌' },
            cancelled: { title: '已取消', message: '处理已被用户取消', icon: '⏹️' }
        };
        return map[s] || map.idle;
    },

    _updatePanelStyle(status) {
        const panel = document.getElementById('processing-progress');
        if (!panel) return;
        panel.classList.remove('idle', 'processing', 'completed', 'error');
        panel.classList.add(status);
        const glow = panel.querySelector('.progress-glow');
        if (glow) glow.classList.toggle('active', status === 'processing');
        const cancelBtn = document.getElementById('cancelProcessing');
        if (cancelBtn) cancelBtn.style.display = status === 'processing' ? 'inline-block' : 'none';
    },

    _areEqual(a, b) {
        if (!a || !b) return false;
        const keys = ['status', 'progress', 'current_file', 'processed_files_count', 'total_files'];
        for (const k of keys) { if (a[k] !== b[k]) return false; }
        return (a.results?.length || 0) === (b.results?.length || 0);
    }
};

window.TaskProgress = TaskProgress;
