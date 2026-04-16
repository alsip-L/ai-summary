/* static/script.js - 优化版本的前端JavaScript文件 */

// 统一的配置
const CONFIG = {
    DEBUG: window.location.hostname === 'localhost',
    API_ENDPOINTS: {
        CANCEL_PROCESSING: '/cancel_processing',
        START_PROCESSING: '/start_processing',
        GET_STATUS: '/get_processing_status',
        AUTO_SAVE_INTERVAL: 30000, // 30秒自动保存
    },
    UI_UPDATE_INTERVAL: 2000, // 2秒更新UI
    ANIMATION_DURATION: 300
};

// 工具函数
class Utils {
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static escapeHtml(text) {
        const map = {
            '&': '&',
            '<': '<',
            '>': '>',
            '"': '"',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    static formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

// 配置管理器
class ConfigManager {
    static async autoSave() {
        if (CONFIG.DEBUG) console.log('执行自动保存');
        
        const form = document.getElementById('configForm');
        if (!form) return;
        
        const formData = new FormData(form);
        formData.append('auto_save', 'true');
        
        try {
            const response = await fetch('/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (CONFIG.DEBUG) console.log('自动保存响应:', response.status);
        } catch (error) {
            console.error('自动保存失败:', error);
        }
    }

    static setupAutoSave() {
        // 每30秒自动保存一次
        setInterval(() => {
            this.autoSave();
        }, CONFIG.API_ENDPOINTS.AUTO_SAVE_INTERVAL);
    }

    static setupFormChangeHandlers() {
        const form = document.getElementById('configForm');
        if (!form) return;

        const debouncedSave = Utils.debounce(() => {
            this.autoSave();
        }, 2000); // 2秒防抖

        form.addEventListener('change', (e) => {
            if (CONFIG.DEBUG) console.log('表单变化:', e.target.name);
            debouncedSave();
        });
    }
}

// 处理管理器
class ProcessingManager {
    constructor() {
        this.isProcessing = false;
        this.progressInterval = null;
        this.startTime = null;
        this.lastStatus = null; // 记录上一次的状态，避免不必要的更新
    }

    async startProcessing() {
        console.log('=== DEBUG: startProcessing开始执行 ===');
        console.log('DEBUG: this.isProcessing =', this.isProcessing);
        console.log('DEBUG: this =', this);
        
        if (this.isProcessing) {
            console.log('DEBUG: 当前正在处理，返回警告');
            this.showMessage('正在处理中，请稍候...', 'warning');
            return;
        }

        const configForm = document.getElementById('configForm');
        const promptForm = document.getElementById('promptForm');
        
        console.log('DEBUG: configForm元素:', configForm);
        console.log('DEBUG: promptForm元素:', promptForm);
        
        if (!configForm) {
            console.error('ERROR: 配置表单不存在');
            this.showMessage('配置表单不存在', 'error');
            return;
        }

        if (!promptForm) {
            console.error('ERROR: 提示词表单不存在');
            this.showMessage('提示词表单不存在', 'error');
            return;
        }

        // 从两个表单收集数据
        const formData = new FormData();
        
        // 从 configForm 获取数据
        for (let [key, value] of new FormData(configForm)) {
            formData.append(key, value);
        }
        
        // 从 promptForm 获取数据（覆盖可能的重复字段）
        for (let [key, value] of new FormData(promptForm)) {
            formData.set(key, value);
        }
        
        // 验证必要参数
        const directory = formData.get('directory_path');
        console.log('DEBUG: 目录路径:', directory);
        if (!directory) {
            this.showMessage('请输入处理目录路径', 'error');
            return;
        }

        const selectedProvider = formData.get('selected_provider');
        console.log('DEBUG: 提供商:', selectedProvider);
        if (!selectedProvider) {
            this.showMessage('请选择AI服务商', 'error');
            return;
        }

        const selectedModel = formData.get('selected_model');
        console.log('DEBUG: 模型:', selectedModel);
        if (!selectedModel) {
            this.showMessage('请选择AI模型', 'error');
            return;
        }

        // 从configForm中获取API key，如果没有的话
        let apiKey = formData.get('api_key');
        console.log('DEBUG: API Key:', apiKey ? '已配置' : '未配置');
        if (!apiKey) {
            // 使用自定义对话框代替 prompt
            apiKey = await new Promise((resolve) => {
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

                document.getElementById('submit_api_key').onclick = function() {
                    const value = document.getElementById('api_key_input').value.trim();
                    overlay.remove();
                    resolve(value);
                };
                document.getElementById('cancel_api_key').onclick = function() {
                    overlay.remove();
                    resolve('');
                };
                dialog.querySelector('#api_key_input').focus();
            });
            
            if (!apiKey) {
                this.showMessage('必须提供API Key', 'error');
                return;
            }
        }
        
        const selectedPrompt = formData.get('selected_prompt');
        console.log('DEBUG: Prompt:', selectedPrompt);
        if (!selectedPrompt) {
            this.showMessage('请选择提示词', 'error');
            return;
        }

        // 显示进度容器
        const progressContainer = document.getElementById('processing-progress');
        console.log('DEBUG: 进度容器元素:', progressContainer);
        if (progressContainer) {
            progressContainer.style.display = 'block';
            progressContainer.classList.add('visible');
            console.log('DEBUG: 进度容器已显示');
        } else {
            console.error('ERROR: 找不到进度容器元素');
        }

        // 确保状态显示区域可见
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = '准备开始...';
            console.log('DEBUG: 状态文本已设置');
        }

        this.isProcessing = true;
        this.startTime = Date.now();
        this.updateUI({ status: 'started', progress: 0 });

        try {
            // 正确地向 /start_processing 路由发送请求
            const response = await fetch(CONFIG.API_ENDPOINTS.START_PROCESSING, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: '启动失败' }));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            if (result.status === 'started') {
                this.showMessage(result.message, 'success');
                this.startProgressMonitoring();
            } else {
                throw new Error(result.message || '启动失败');
            }
        } catch (error) {
            console.error('启动处理失败:', error);
            this.showMessage(`启动失败: ${error.message}`, 'error');
            this.isProcessing = false;
            
            // 隐藏进度容器
            const progressContainer = document.getElementById('processing-progress');
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
        }
    }

    async startProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }

        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(CONFIG.API_ENDPOINTS.GET_STATUS);
                const status = await response.json();
                this.updateUI(status);

                if (status.status === 'completed' || status.status === 'error' || status.status === 'cancelled') {
                    this.isProcessing = false;
                    clearInterval(this.progressInterval);
                    this.progressInterval = null;
                    
                    if (status.status === 'completed') {
                        const duration = (Date.now() - this.startTime) / 1000;
                        this.showMessage(`处理完成！耗时: ${Utils.formatDuration(duration)}`, 'success');
                    } else if (status.status === 'error') {
                        this.showMessage(`处理失败: ${status.error}`, 'error');
                    }
                }
            } catch (error) {
                console.error('获取状态失败:', error);
            }
        }, CONFIG.API_ENDPOINTS.UI_UPDATE_INTERVAL);
    }

    // 辅助函数：比较两个对象是否相同
    areStatusesEqual(status1, status2) {
        if (!status1 || !status2) return false;
        const keys = ['status', 'progress', 'current_file', 'processed_files_count', 'total_files'];
        for (const key of keys) {
            if (status1[key] !== status2[key]) return false;
        }
        // 比较results的长度
        if ((status1.results && status1.results.length) !== (status2.results && status2.results.length)) {
            return false;
        }
        return true;
    }

    updateUI(status) {
        console.log('=== DEBUG: updateUI开始执行 ===');
        console.log('DEBUG: 接收到的状态数据:', status);
        console.log('DEBUG: 状态类型:', typeof status);
        console.log('DEBUG: 状态键:', Object.keys(status));
        
        // 检查状态是否真的有变化，避免不必要的更新
        if (this.lastStatus && this.areStatusesEqual(this.lastStatus, status)) {
            console.log('DEBUG: 状态未变化，跳过UI更新');
            return;
        }
        this.lastStatus = {...status}; // 保存当前状态的副本
        
        // 更新进度条 - 新版本
        const progressFill = document.getElementById('progressFill');
        const progressPercentage = document.getElementById('progressPercentage');
        
        console.log('DEBUG: progressFill元素:', progressFill);
        console.log('DEBUG: progressPercentage元素:', progressPercentage);
        
        if (progressFill) {
            const width = `${status.progress || 0}%`;
            progressFill.style.width = width;
            console.log('DEBUG: 进度条宽度已设置为:', width);
        } else {
            console.error('ERROR: 未找到progressFill元素');
        }
        
        if (progressPercentage) {
            const text = `${status.progress || 0}%`;
            progressPercentage.textContent = text;
            console.log('DEBUG: 进度百分比文本已设置为:', text);
        } else {
            console.error('ERROR: 未找到progressPercentage元素');
        }

        // 更新状态显示 - 新版本
        const statusTitle = document.getElementById('statusTitle');
        const statusMessage = document.getElementById('statusMessage');
        const statusIcon = document.getElementById('statusIcon');
        
        console.log('DEBUG: statusTitle元素:', statusTitle);
        console.log('DEBUG: statusMessage元素:', statusMessage);
        console.log('DEBUG: statusIcon元素:', statusIcon);
        
        if (statusTitle && statusMessage && statusIcon) {
            const statusInfo = this.getStatusInfo(status.status || 'idle');
            console.log('DEBUG: 获取到的状态信息:', statusInfo);
            
            statusTitle.textContent = statusInfo.title;
            statusMessage.textContent = statusInfo.message;
            statusIcon.textContent = statusInfo.icon;
            
            console.log('DEBUG: 状态显示已更新:', statusInfo.title, statusInfo.message);
        } else {
            console.error('ERROR: 未找到状态显示元素');
            console.log('DEBUG: statusTitle存在:', !!statusTitle);
            console.log('DEBUG: statusMessage存在:', !!statusMessage);
            console.log('DEBUG: statusIcon存在:', !!statusIcon);
        }

        // 显示详细信息 - 新版本
        const currentFile = document.getElementById('currentFile');
        const progressFiles = document.getElementById('progressFiles');
        const elapsedTime = document.getElementById('elapsedTime');
        
        console.log('DEBUG: currentFile元素:', currentFile);
        console.log('DEBUG: progressFiles元素:', progressFiles);
        console.log('DEBUG: elapsedTime元素:', elapsedTime);
        
        if (currentFile) {
            const fileText = status.current_file || '-';
            currentFile.textContent = fileText;
            console.log('DEBUG: 当前文件已更新为:', fileText);
        }
        
        if (progressFiles) {
            const processed = status.processed_files_count || 0;
            const total = status.total_files || 0;
            // 修复：进度显示从1/n开始而不是0/n开始
            const displayProcessed = processed === 0 ? 1 : processed;
            const progressText = `${displayProcessed} / ${total}`;
            progressFiles.textContent = progressText;
            console.log('DEBUG: 处理进度已更新为:', progressText);
        }
        
        if (elapsedTime && this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const timeText = Utils.formatDuration(elapsed);
            elapsedTime.textContent = timeText;
            console.log('DEBUG: 耗时已更新为:', timeText);
        }

        // 更新面板样式
        console.log('DEBUG: 更新面板样式，状态:', status.status || 'idle');
        this.updatePanelStyle(status.status || 'idle');
        
        // 处理结果显示 - 在处理过程中和完成时都显示结果
        if (status.results && status.results.length > 0) {
            console.log('DEBUG: 显示处理结果，数量:', status.results.length);
            console.log('DEBUG: 当前状态:', status.status);
            this.displayResults(status.results);
        }
        
        console.log('=== DEBUG: updateUI执行完成 ===');
    }

    getStatusInfo(status) {
        const statusMap = {
            'idle': {
                title: '待机',
                message: '等待开始处理...',
                icon: '⏸️'
            },
            'started': {
                title: '准备处理',
                message: '正在初始化处理流程...',
                icon: '🚀'
            },
            'scanning': {
                title: '扫描文件',
                message: '正在扫描目录中的文件...',
                icon: '🔍'
            },
            'processing': {
                title: '正在处理',
                message: status.current_file ?
                    `正在处理文件: ${status.current_file}` :
                    '正在处理文件...',
                icon: '⚙️'
            },
            'completed': {
                title: '处理完成',
                message: '所有文件处理完成！',
                icon: '✅'
            },
            'error': {
                title: '处理错误',
                message: `处理失败: ${status.error || '未知错误'}`,
                icon: '❌'
            },
            'cancelled': {
                title: '已取消',
                message: '处理已被用户取消',
                icon: '⏹️'
            }
        };
        
        return statusMap[status] || statusMap['idle'];
    }

    updatePanelStyle(status) {
        const panel = document.getElementById('processing-progress');
        if (!panel) return;
        
        // 移除所有状态类
        panel.classList.remove('idle', 'processing', 'completed', 'error');
        
        // 添加当前状态类
        panel.classList.add(status);
        
        // 特殊处理状态图标
        const statusIcon = document.getElementById('statusIcon');
        const progressGlow = document.querySelector('.progress-glow');
        
        if (status === 'processing') {
            if (progressGlow) {
                progressGlow.classList.add('active');
            }
        } else {
            if (progressGlow) {
                progressGlow.classList.remove('active');
            }
        }
        
        // 显示/隐藏取消按钮
        const cancelBtn = document.getElementById('cancelProcessing');
        if (cancelBtn) {
            cancelBtn.style.display = status === 'processing' ? 'inline-block' : 'none';
        }
    }

    displayResults(results) {
        console.log('DEBUG: 显示结果数据:', results);
        
        // 获取结果区域
        const resultsArea = document.getElementById('results-area');
        const resultsTable = document.getElementById('results-table').querySelector('tbody');
        
        if (!resultsArea || !resultsTable) {
            console.error('结果区域或表格未找到');
            return;
        }

        // 检查是否需要更新 - 比较现有行数和新结果数量
        const existingRows = resultsTable.querySelectorAll('tr');
        if (existingRows.length === results.length) {
            console.log('DEBUG: 结果数量未变化，跳过更新');
            return;
        }

        // 清空现有内容
        resultsTable.innerHTML = '';

        // 添加结果行
        results.forEach(result => {
            const row = document.createElement('tr');
            
            // 源文件列
            const sourceCell = document.createElement('td');
            const sourceFileName = result.source ? result.source.split('/').pop().split('\\').pop() : '';
            sourceCell.textContent = Utils.escapeHtml(sourceFileName);
            sourceCell.style.wordBreak = 'break-all';
            sourceCell.style.maxWidth = '300px';
            sourceCell.style.overflow = 'hidden';
            sourceCell.style.textOverflow = 'ellipsis';
            sourceCell.style.whiteSpace = 'nowrap';
            row.appendChild(sourceCell);
            
            // 结果文件列
            const outputCell = document.createElement('td');
            if (result.output) {
                const outputFileName = result.output.split('/').pop().split('\\').pop();
                const filePath = result.output;
                
                // 创建链接到结果文件
                const link = document.createElement('a');
                link.href = `#`;
                link.textContent = Utils.escapeHtml(outputFileName);
                link.style.textDecoration = 'none';
                link.style.color = '#007bff';
                link.style.wordBreak = 'break-all';
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    // 可以在这里添加文件查看功能
                    alert(`文件路径: ${filePath}`);
                });
                
                outputCell.appendChild(link);
            } else {
                outputCell.textContent = '处理失败';
                outputCell.style.color = '#dc3545';
            }
            
            outputCell.style.wordBreak = 'break-all';
            outputCell.style.maxWidth = '400px';
            outputCell.style.overflow = 'hidden';
            outputCell.style.textOverflow = 'ellipsis';
            outputCell.style.whiteSpace = 'nowrap';
            
            row.appendChild(outputCell);
            
            resultsTable.appendChild(row);
        });

        // 显示结果区域（只在第一次显示时添加动画）
        if (resultsArea.style.display !== 'block') {
            resultsArea.style.display = 'block';
            resultsArea.classList.add('visible');
        }
        
        console.log(`DEBUG: 已显示 ${results.length} 个结果`);
    }

    async cancelProcessing() {
        console.log('=== DEBUG: cancelProcessing开始执行 ===');
        console.log('DEBUG: 当前处理状态:', this.isProcessing);
        
        if (!this.isProcessing) {
            console.log('DEBUG: 当前不在处理状态，无需取消');
            this.showMessage('当前不在处理状态', 'info');
            return;
        }

        try {
            // 发送取消请求到服务器
            console.log('DEBUG: 发送取消请求到服务器');
            const response = await fetch(CONFIG.API_ENDPOINTS.CANCEL_PROCESSING, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                console.log('DEBUG: 取消请求发送成功');
                
                // 停止进度监控
                if (this.progressInterval) {
                    clearInterval(this.progressInterval);
                    this.progressInterval = null;
                }
                
                // 重置处理状态
                this.isProcessing = false;
                
                // 隐藏进度容器
                const progressContainer = document.getElementById('processing-progress');
                if (progressContainer) {
                    progressContainer.style.display = 'none';
                }
                
                // 更新状态为已取消
                this.updateUI({
                    status: 'cancelled',
                    progress: 0,
                    error: '用户取消了处理'
                });
                
                this.showMessage('处理已取消', 'warning');
                console.log('DEBUG: 处理已成功取消');
            } else {
                throw new Error('取消请求失败');
            }
        } catch (error) {
            console.error('取消处理失败:', error);
            this.showMessage(`取消处理失败: ${error.message}`, 'error');
        }
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.getElementById('message');
        if (!messageDiv) return;

        messageDiv.className = `alert alert-${type === 'error' ? 'danger' : type}`;
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
        messageDiv.style.animation = 'none';
        messageDiv.offsetHeight; // 触发重绘
        messageDiv.style.animation = 'fixedSlideIn 0.3s ease-out';

        // 更快自动隐藏 - 2秒
        setTimeout(() => {
            messageDiv.style.animation = 'fixedFadeOut 0.3s ease-out';
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 300);
        }, 2000);

        if (CONFIG.DEBUG) console.log(`消息 [${type}]: ${message}`);
    }
}

// 回收站管理器
class TrashManager {
    static async deleteItem(type, name) {
        if (!confirm(`确定要删除${type === 'provider' ? 'AI提供者' : '提示词'} "${name}" 吗？`)) {
            return;
        }

        const form = document.createElement('form');
        form.method = 'POST';
        
        const field = document.createElement('input');
        field.type = 'hidden';
        field.name = type === 'provider' ? 'provider_name_to_delete' : 'prompt_name_to_delete';
        field.value = name;
        
        const typeField = document.createElement('input');
        typeField.type = 'hidden';
        typeField.name = 'form_type';
        typeField.value = type === 'provider' ? 'delete_provider_form' : 'delete_prompt_form';
        
        form.appendChild(field);
        form.appendChild(typeField);
        
        document.body.appendChild(form);
        form.submit();
    }

    static async restoreItem(type, name) {
        const form = document.createElement('form');
        form.method = 'POST';
        
        const field = document.createElement('input');
        field.type = 'hidden';
        field.name = type === 'provider' ? 'provider_name_to_restore' : 'prompt_name_to_restore';
        field.value = name;
        
        const typeField = document.createElement('input');
        typeField.type = 'hidden';
        typeField.name = 'form_type';
        typeField.value = type === 'provider' ? 'restore_provider_form' : 'restore_prompt_form';
        
        form.appendChild(field);
        form.appendChild(typeField);
        
        document.body.appendChild(form);
        form.submit();
    }

    static async permanentDeleteItem(type, name) {
        if (!confirm(`确定要永久删除${type === 'provider' ? 'AI提供者' : '提示词'} "${name}" 吗？此操作不可恢复！`)) {
            return;
        }

        const form = document.createElement('form');
        form.method = 'POST';
        
        const field = document.createElement('input');
        field.type = 'hidden';
        field.name = type === 'provider' ? 'provider_name_to_permanent_delete' : 'prompt_name_to_permanent_delete';
        field.value = name;
        
        const typeField = document.createElement('input');
        typeField.type = 'hidden';
        typeField.name = 'form_type';
        typeField.value = type === 'provider' ? 'permanent_delete_provider_form' : 'permanent_delete_prompt_form';
        
        form.appendChild(field);
        form.appendChild(typeField);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// UI管理器
class UIManager {
    static setupThemeToggle() {
        const toggle = document.getElementById('themeToggle');
        if (!toggle) return;

        toggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            localStorage.setItem('theme', 
                document.body.classList.contains('dark-theme') ? 'dark' : 'light'
            );
        });

        // 加载主题偏好
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
    }

    static setupExpandableSections() {
        const toggles = document.querySelectorAll('.expandable-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const target = document.querySelector(toggle.dataset.target);
                if (target) {
                    target.classList.toggle('expanded');
                    toggle.classList.toggle('expanded');
                }
            });
        });
    }

    static setupFileDropZone() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('directoryInput');
        
        if (!dropZone || !fileInput) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragover');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === '') {
                // 拖拽的是文件夹
                const directoryPath = files[0].webkitRelativePath.split('/')[0];
                fileInput.value = directoryPath;
            }
        });
    }

    static setupLoadingAnimations() {
        // 为按钮添加加载动画
        const buttons = document.querySelectorAll('button[type="submit"]');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                if (!button.disabled) {
                    button.classList.add('loading');
                    button.disabled = true;
                    
                    setTimeout(() => {
                        button.classList.remove('loading');
                        button.disabled = false;
                    }, CONFIG.ANIMATION_DURATION);
                }
            });
        });
    }
}

// 全局变量
let processingManager;

// 点击页面其他地方关闭所有下拉菜单
document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown')) {
        document.querySelectorAll('.dropdown-content').forEach(el => {
            el.classList.remove('show');
        });
        document.querySelectorAll('.prompt-content-area, .trash-content-area').forEach(el => {
            el.style.display = 'none';
        });
    }
});

window.addEventListener('scroll', () => {
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        el.classList.remove('show');
    });
}, true);

window.addEventListener('resize', () => {
    document.querySelectorAll('.dropdown-content.show').forEach(el => {
        el.classList.remove('show');
    });
});

// 初始化函数
document.addEventListener('DOMContentLoaded', () => {
    if (CONFIG.DEBUG) {
        console.log('初始化优化版本的前端脚本...');
    }

    // 初始化各个管理器
    processingManager = new ProcessingManager();
    
    // 设置开始处理按钮事件监听器
    const startButton = document.getElementById('start-process-btn');
    console.log('DEBUG: 查找开始处理按钮:', startButton);
    console.log('DEBUG: 按钮元素详情:', {
        id: startButton ? startButton.id : null,
        type: startButton ? startButton.type : null,
        onclick: startButton ? startButton.onclick : null,
        disabled: startButton ? startButton.disabled : null,
        tagName: startButton ? startButton.tagName : null
    });
    
    if (startButton) {
        console.log('DEBUG: 开始处理按钮已找到，准备绑定事件监听器');
        
        // 立即调用方式：直接执行startProcessing逻辑
        startButton.onclick = function(e) {
            console.log('=== DEBUG: 开始处理按钮被点击 (onclick) ===');
            e.preventDefault();
            e.stopPropagation();
            
            if (typeof processingManager !== 'undefined' && processingManager) {
                processingManager.startProcessing();
            } else {
                console.error('ERROR: processingManager未定义');
                alert('❌ 系统错误：processingManager未定义');
            }
        };
        
        console.log('DEBUG: onclick事件已绑定');
        
        // 添加调试按钮点击日志
        startButton.addEventListener('click', function(e) {
            console.log('=== DEBUG: 开始处理按钮被点击 (addEventListener) ===');
        });
        
    } else {
        console.error('ERROR: 未找到开始处理按钮');
        // 延迟重试查找按钮
        setTimeout(() => {
            const retryButton = document.getElementById('start-process-btn');
            if (retryButton) {
                console.log('DEBUG: 延迟重试找到按钮，重新绑定事件');
                retryButton.onclick = function(e) {
                    console.log('=== DEBUG: 重试绑定的点击事件 ===');
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof processingManager !== 'undefined' && processingManager) {
                        processingManager.startProcessing();
                    }
                };
            }
        }, 1000);
    }

    // 设置取消处理按钮事件监听器
    const cancelButton = document.getElementById('cancelProcessing');
    console.log('DEBUG: 查找取消处理按钮:', cancelButton);
    
    if (cancelButton) {
        console.log('DEBUG: 取消处理按钮已找到，准备绑定事件监听器');
        
        cancelButton.onclick = function(e) {
            console.log('=== DEBUG: 取消处理按钮被点击 ===');
            e.preventDefault();
            e.stopPropagation();
            
            if (typeof processingManager !== 'undefined' && processingManager) {
                if (processingManager.isProcessing) {
                    // 确认取消操作
                    if (confirm('确定要取消当前处理吗？')) {
                        console.log('DEBUG: 用户确认取消处理');
                        processingManager.cancelProcessing();
                    } else {
                        console.log('DEBUG: 用户取消取消操作');
                    }
                } else {
                    console.log('DEBUG: 当前不在处理状态，不需要取消');
                    processingManager.showMessage('当前不在处理状态', 'info');
                }
            } else {
                console.error('ERROR: processingManager未定义');
                alert('❌ 系统错误：processingManager未定义');
            }
        };
        
        console.log('DEBUG: 取消按钮onclick事件已绑定');
        
        // 添加调试按钮点击日志
        cancelButton.addEventListener('click', function(e) {
            console.log('=== DEBUG: 取消处理按钮被点击 (addEventListener) ===');
        });
        
    } else {
        console.error('ERROR: 未找到取消处理按钮');
        // 延迟重试查找取消按钮
        setTimeout(() => {
            const retryCancelButton = document.getElementById('cancelProcessing');
            if (retryCancelButton) {
                console.log('DEBUG: 延迟重试找到取消按钮，重新绑定事件');
                retryCancelButton.onclick = function(e) {
                    console.log('=== DEBUG: 重试绑定的取消按钮点击事件 ===');
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof processingManager !== 'undefined' && processingManager && processingManager.isProcessing) {
                        if (confirm('确定要取消当前处理吗？')) {
                            processingManager.cancelProcessing();
                        }
                    }
                };
            }
        }, 1000);
    }

    // 设置配置自动保存
    ConfigManager.setupFormChangeHandlers();
    ConfigManager.setupAutoSave();

    // 设置UI增强功能
    UIManager.setupThemeToggle();
    UIManager.setupExpandableSections();
    UIManager.setupFileDropZone();
    UIManager.setupLoadingAnimations();

    // 设置回收站功能
    window.TrashManager = TrashManager;

    // 将processingManager暴露到全局
    window.processingManager = processingManager;

    if (CONFIG.DEBUG) {
        console.log('前端脚本初始化完成');
    }
});

// 导出全局函数（向后兼容）
window.startProcessing = function() {
    if (window.processingManager) {
        window.processingManager.startProcessing();
    }
};

// 为了兼容性，将主要管理器暴露到全局
window.ProcessingManager = ProcessingManager;
window.ConfigManager = ConfigManager;
window.UIManager = UIManager;
window.Utils = Utils;

// 添加下拉菜单相关函数（从原版本复制）
// 切换下拉菜单显示/隐藏
window.toggleDropdown = function(dropdownId) {
    console.log('DEBUG: toggleDropdown called with:', dropdownId);
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) {
        console.error('Dropdown not found:', dropdownId);
        return;
    }
    
    let content;
    if (dropdownId === 'prompt-content-dropdown') {
        content = document.getElementById('prompt-content-options');
    } else if (dropdownId === 'trash-dropdown') {
        content = document.getElementById('trash-options');
    } else {
        content = dropdown.querySelector('.dropdown-content');
    }
    
    if (!content) {
        console.error('Dropdown content not found for:', dropdownId);
        return;
    }
    
    console.log('DEBUG: Found dropdown content, current classes:', content.className);
    
    document.querySelectorAll('.dropdown-content').forEach(el => {
        if (el.classList.contains('show') && el !== content) {
            el.classList.remove('show');
        }
    });
    
    if (dropdownId === 'prompt-content-dropdown' || dropdownId === 'trash-dropdown') {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
        console.log('DEBUG: Toggled special dropdown, new display:', content.style.display);
    } else {
        content.classList.toggle('show');
        console.log('DEBUG: After toggle, classes:', content.className);
        if (content.classList.contains('show')) {
            positionDropdown(dropdown, content);
        }
    }
};

window.positionDropdown = function(dropdown, content) {
    const selected = dropdown.querySelector('.dropdown-selected');
    if (!selected) return;
    const rect = selected.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const dropdownMaxHeight = 320;
    let top = rect.bottom + 6;
    let left = rect.left;
    let width = rect.width;

    if (top + dropdownMaxHeight > viewportHeight) {
        top = rect.top - dropdownMaxHeight - 6;
        if (top < 0) {
            top = 4;
        }
    }

    if (left + width > window.innerWidth) {
        left = window.innerWidth - width - 8;
    }
    if (left < 8) {
        left = 8;
    }

    content.style.top = top + 'px';
    content.style.left = left + 'px';
    content.style.width = width + 'px';
};

// 选择提供商并自动更新模型（无刷新版本）
window.selectProvider = function(providerName) {
    console.log('DEBUG: Selecting provider (AJAX):', providerName);
    
    // 获取当前表单数据
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_provider', providerName);
    
    // 获取隐藏字段中的当前值
    const currentModelInput = document.querySelector('input[name="selected_model"]');
    const currentPromptInput = document.querySelector('input[name="selected_prompt"]');
    const directoryPathInput = document.getElementById('directory_path');
    
    formData.append('selected_model', currentModelInput ? currentModelInput.value : '');
    formData.append('selected_prompt', currentPromptInput ? currentPromptInput.value : '');
    formData.append('directory_path', directoryPathInput ? directoryPathInput.value : '');
    formData.append('auto_save', 'true');
    
    // 显示加载状态
    processingManager.showMessage('正在保存配置...', 'info');
    
    // 关闭下拉菜单
    document.querySelectorAll('.dropdown-content').forEach(el => {
        el.classList.remove('show');
    });
    document.querySelectorAll('.prompt-content-area, .trash-content-area').forEach(el => {
        el.style.display = 'none';
    });
    
    // AJAX提交，不刷新页面
    fetch('/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // 保存成功后，更新页面上的显示值
            // 更新提供商显示
            const providerDisplay = document.querySelector('#provider-dropdown .dropdown-selected span:first-child');
            if (providerDisplay) {
                providerDisplay.textContent = providerName;
            }
            
            // 更新隐藏字段
            if (currentModelInput) {
                // 从providers-data获取新提供商的模型列表，并自动选择第一个
                try {
                    const providersDataScript = document.getElementById('providers-data');
                    if (providersDataScript) {
                        const providersData = JSON.parse(providersDataScript.textContent);
                        const provider = providersData[providerName];
                        if (provider && provider.models && Object.keys(provider.models).length > 0) {
                            const firstModel = Object.keys(provider.models)[0];
                            currentModelInput.value = firstModel;
                            // 更新模型显示
                            const modelDisplay = document.querySelector('#model-dropdown .dropdown-selected span:first-child');
                            if (modelDisplay) {
                                modelDisplay.textContent = firstModel;
                            }
                        }
                    }
                } catch (e) {
                    console.error('解析providers-data失败:', e);
                }
            }
            
            if (currentPromptInput) {
                currentPromptInput.value = currentPromptInput.value;
            }
            
            processingManager.showMessage('✅ 配置已保存', 'success');
        } else {
            throw new Error('保存失败');
        }
    })
    .catch(error => {
        console.error('选择失败:', error);
        processingManager.showMessage('❌ 保存失败: ' + error.message, 'error');
    });
};

// 选择Prompt并自动保存到config.json（无刷新版本）
window.selectPrompt = function(promptName) {
    console.log('DEBUG: Selecting prompt (AJAX):', promptName);
    
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_prompt', promptName);
    formData.append('selected_provider', document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '');
    formData.append('selected_model', document.querySelector('input[name="selected_model"]') ? document.querySelector('input[name="selected_model"]').value : '');
    formData.append('directory_path', document.getElementById('directory_path') ? document.getElementById('directory_path').value : '');
    formData.append('auto_save', 'true');
    
    // 显示加载状态
    processingManager.showMessage('正在保存配置...', 'info');
    
    // 关闭下拉菜单
    document.querySelectorAll('.dropdown-content').forEach(el => {
        el.classList.remove('show');
    });
    document.querySelectorAll('.prompt-content-area, .trash-content-area').forEach(el => {
        el.style.display = 'none';
    });
    
    fetch('/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // 更新页面上的显示值
            const promptDisplay = document.querySelector('#prompt-dropdown .dropdown-selected span:first-child');
            if (promptDisplay) {
                promptDisplay.textContent = promptName;
            }
            // 更新隐藏字段
            const promptInput = document.querySelector('input[name="selected_prompt"]');
            if (promptInput) {
                promptInput.value = promptName;
            }
            processingManager.showMessage('✅ 配置已保存', 'success');
        } else {
            throw new Error('保存失败');
        }
    })
    .catch(error => {
        console.error('选择失败:', error);
        processingManager.showMessage('❌ 保存失败: ' + error.message, 'error');
    });
};

// 选择模型并自动保存到config.json（无刷新版本）
window.selectModel = function(modelName) {
    console.log('DEBUG: Selecting model (AJAX):', modelName);
    
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_model', modelName);
    formData.append('selected_provider', document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '');
    formData.append('selected_prompt', document.querySelector('input[name="selected_prompt"]') ? document.querySelector('input[name="selected_prompt"]').value : '');
    formData.append('directory_path', document.getElementById('directory_path') ? document.getElementById('directory_path').value : '');
    formData.append('auto_save', 'true');
    
    // 显示加载状态
    processingManager.showMessage('正在保存配置...', 'info');
    
    // 关闭下拉菜单
    document.querySelectorAll('.dropdown-content').forEach(el => {
        el.classList.remove('show');
    });
    document.querySelectorAll('.prompt-content-area, .trash-content-area').forEach(el => {
        el.style.display = 'none';
    });
    
    fetch('/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // 更新页面上的显示值
            const modelDisplay = document.querySelector('#model-dropdown .dropdown-selected span:first-child');
            if (modelDisplay) {
                modelDisplay.textContent = modelName;
            }
            // 更新隐藏字段
            const modelInput = document.querySelector('input[name="selected_model"]');
            if (modelInput) {
                modelInput.value = modelName;
            }
            processingManager.showMessage('✅ 配置已保存', 'success');
        } else {
            throw new Error('保存失败');
        }
    })
    .catch(error => {
        console.error('选择失败:', error);
        processingManager.showMessage('❌ 保存失败: ' + error.message, 'error');
    });
};

// 删除提供商功能
window.deleteProvider = function(providerName) {
    if (!confirm(`确定要删除AI提供商 '${providerName}' 吗？`)) {
        return;
    }
    
    // 使用URL编码处理中文名称
    const formData = new FormData();
    formData.append('form_type', 'delete_provider_form');
    formData.append('provider_name_to_delete', encodeURIComponent(providerName));
    
    console.log('DEBUG: Deleting provider:', providerName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('DEBUG: Provider deletion successful, reloading page');
            window.location.reload();
        } else {
            console.error('DEBUG: Provider deletion failed with status:', response.status);
            alert('删除失败，请重试');
        }
    })
    .catch(error => {
        console.error('删除提供商失败:', error);
        alert('删除失败: ' + error.message);
    });
};

// 删除模型功能
window.deleteModel = function(providerName, modelName) {
    if (!confirm(`确定要从提供商 '${providerName}' 中删除模型 '${modelName}' 吗？`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('form_type', 'delete_model_form');
    formData.append('provider_name_for_model_delete', providerName);
    formData.append('model_name_to_delete', modelName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('删除模型失败:', error);
        alert('删除失败: ' + error.message);
    });
};

// 删除Prompt功能
window.deletePrompt = function(promptName) {
    if (!confirm(`确定要删除Prompt '${promptName}' 吗？`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('form_type', 'delete_prompt_form');
    formData.append('prompt_name_to_delete', promptName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('删除Prompt失败:', error);
        alert('删除失败: ' + error.message);
    });
};

// 恢复提供商功能
window.restoreProvider = function(providerName) {
    const formData = new FormData();
    formData.append('form_type', 'restore_provider_form');
    formData.append('provider_name_to_restore', providerName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('恢复提供商失败:', error);
        alert('恢复失败: ' + error.message);
    });
};

// 恢复Prompt功能
window.restorePrompt = function(promptName) {
    const formData = new FormData();
    formData.append('form_type', 'restore_prompt_form');
    formData.append('prompt_name_to_restore', promptName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('恢复Prompt失败:', error);
        alert('恢复失败: ' + error.message);
    });
};

// 永久删除提供商功能
window.permanentDeleteProvider = function(providerName) {
    console.log('DEBUG: permanentDeleteProvider called with:', providerName);
    if (!confirm(`确定要永久删除AI提供商 '${providerName}' 吗？此操作不可恢复！`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('form_type', 'permanent_delete_provider_form');
    formData.append('provider_name_to_permanent_delete', providerName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('DEBUG: Permanent delete successful, reloading page');
            window.location.reload();
        } else {
            console.error('DEBUG: Permanent delete failed with status:', response.status);
            alert('永久删除失败，请重试');
        }
    })
    .catch(error => {
        console.error('永久删除提供商失败:', error);
        alert('永久删除失败: ' + error.message);
    });
};

// 永久删除Prompt功能
window.permanentDeletePrompt = function(promptName) {
    console.log('DEBUG: permanentDeletePrompt called with:', promptName);
    if (!confirm(`确定要永久删除Prompt '${promptName}' 吗？此操作不可恢复！`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('form_type', 'permanent_delete_prompt_form');
    formData.append('prompt_name_to_permanent_delete', promptName);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('DEBUG: Permanent delete successful, reloading page');
            window.location.reload();
        } else {
            console.error('DEBUG: Permanent delete failed with status:', response.status);
            alert('永久删除失败，请重试');
        }
    })
    .catch(error => {
        console.error('永久删除Prompt失败:', error);
        alert('永久删除失败: ' + error.message);
    });
};

// 新增提供商处理函数
window.handleProviderAddNew = function() {
    // 创建一个简单的输入对话框
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';
    
    const dialog = document.createElement('div');
    dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;min-width:400px;max-width:90%;';
    dialog.innerHTML = `
        <h3 style="margin:0 0 15px 0;">新增服务商</h3>
        <div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">服务商名称:</label>
            <input type="text" id="new_provider_name" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="如: 阿里通义">
        </div>
        <div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">API地址:</label>
            <input type="text" id="new_provider_url" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="如: https://api.openai.com/v1">
        </div>
        <div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">API Key:</label>
            <input type="text" id="new_provider_apikey" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="可选">
        </div>
        <div style="margin-bottom:15px;">
            <label style="display:block;margin-bottom:5px;">模型名称:</label>
            <input type="text" id="new_provider_model" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="可选，如: gpt-4">
        </div>
        <div style="text-align:right;">
            <button id="cancel_new_provider" style="padding:8px 15px;margin-right:10px;cursor:pointer;">取消</button>
            <button id="submit_new_provider" style="padding:8px 15px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;">确定</button>
        </div>
    `;
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    // 聚焦第一个输入框
    dialog.querySelector('#new_provider_name').focus();
    
    // 提交按钮事件
    document.getElementById('submit_new_provider').onclick = function() {
        const name = document.getElementById('new_provider_name').value.trim();
        const url = document.getElementById('new_provider_url').value.trim();
        const apiKey = document.getElementById('new_provider_apikey').value.trim();
        const modelName = document.getElementById('new_provider_model').value.trim();
        
        if (!name) {
            alert('请输入服务商名称');
            return;
        }
        if (!url) {
            alert('请输入API地址');
            return;
        }
        
        // 处理模型配置
        let models = {};
        if (modelName) {
            models[modelName] = modelName;
        } else {
            models['默认模型'] = name.toLowerCase().replace(/\s+/g, '-') + '-model';
        }
        
        // 关闭对话框
        overlay.remove();
        
        // 提交表单
        const formData = new FormData();
        formData.append('form_type', 'save_provider_form');
        formData.append('provider_name', name);
        formData.append('base_url', url);
        formData.append('api_key_for_save', apiKey);
        formData.append('models', JSON.stringify(models));
        
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                setTimeout(() => {
                    window.location.reload();
                }, 100);
            } else {
                alert('添加失败，请重试');
            }
        })
        .catch(error => {
            console.error('添加提供商失败:', error);
            alert('添加失败: ' + error.message);
        });
    };
    
    // 取消按钮事件
    document.getElementById('cancel_new_provider').onclick = function() {
        overlay.remove();
    };
};

// 添加模型功能
window.handleModelAddNew = function() {
    const currentProvider = document.querySelector('input[name="selected_provider"]').value;
    if (!currentProvider) {
        alert('请先选择一个服务商');
        return;
    }

    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';

    const dialog = document.createElement('div');
    dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;min-width:400px;max-width:90%;';
    dialog.innerHTML = `
        <h3 style="margin:0 0 15px 0;">新增模型 - ${currentProvider}</h3>
        <div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">模型显示名称:</label>
            <input type="text" id="new_model_display" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="如: GPT-4">
        </div>
        <div style="margin-bottom:15px;">
            <label style="display:block;margin-bottom:5px;">模型ID:</label>
            <input type="text" id="new_model_id" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="如: gpt-4">
        </div>
        <div style="text-align:right;">
            <button id="cancel_new_model" style="padding:8px 15px;margin-right:10px;cursor:pointer;">取消</button>
            <button id="submit_new_model" style="padding:8px 15px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;">确定</button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    dialog.querySelector('#new_model_display').focus();

    document.getElementById('submit_new_model').onclick = function() {
        const modelDisplay = document.getElementById('new_model_display').value.trim();
        const modelId = document.getElementById('new_model_id').value.trim();

        if (!modelDisplay) {
            alert('请输入模型显示名称');
            return;
        }
        if (!modelId) {
            alert('请输入模型ID');
            return;
        }

        overlay.remove();

        const formData = new FormData();
        formData.append('form_type', 'add_model_form');
        formData.append('provider_name_for_model', currentProvider);
        formData.append('model_display_name', modelDisplay);
        formData.append('model_id', modelId);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                setTimeout(() => {
                    window.location.reload();
                }, 100);
            } else {
                alert('添加失败，请重试');
            }
        })
        .catch(error => {
            console.error('添加模型失败:', error);
            alert('添加失败: ' + error.message);
        });
    };

    document.getElementById('cancel_new_model').onclick = function() {
        overlay.remove();
    };

    overlay.onclick = function(e) {
        if (e.target === overlay) {
            overlay.remove();
        }
    };
};

window.handlePromptAddNew = function() {
    // 创建一个简单的输入对话框
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';

    const dialog = document.createElement('div');
    dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;min-width:400px;max-width:90%;';
    dialog.innerHTML = `
        <h3 style="margin:0 0 15px 0;">新增Prompt</h3>
        <div style="margin-bottom:10px;">
            <label style="display:block;margin-bottom:5px;">Prompt名称:</label>
            <input type="text" id="new_prompt_name" style="width:100%;padding:8px;box-sizing:border-box;" placeholder="如: 文章总结">
        </div>
        <div style="margin-bottom:15px;">
            <label style="display:block;margin-bottom:5px;">Prompt内容:</label>
            <textarea id="new_prompt_content" style="width:100%;min-height:100px;padding:8px;box-sizing:border-box;" placeholder="请输入Prompt内容..."></textarea>
        </div>
        <div style="text-align:right;">
            <button id="cancel_new_prompt" style="padding:8px 15px;margin-right:10px;cursor:pointer;">取消</button>
            <button id="submit_new_prompt" style="padding:8px 15px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;">确定</button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    // 聚焦第一个输入框
    dialog.querySelector('#new_prompt_name').focus();

    // 提交按钮事件
    document.getElementById('submit_new_prompt').onclick = function() {
        const name = document.getElementById('new_prompt_name').value.trim();
        const content = document.getElementById('new_prompt_content').value.trim();

        if (!name) {
            alert('请输入Prompt名称');
            return;
        }
        if (!content) {
            alert('请输入Prompt内容');
            return;
        }

        // 关闭对话框
        overlay.remove();

        // 提交表单
        const formData = new FormData();
        formData.append('form_type', 'save_prompt_form');
        formData.append('prompt_name', name);
        formData.append('prompt_content', content);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                setTimeout(() => {
                    window.location.reload();
                }, 100);
            } else {
                alert('添加失败，请重试');
            }
        })
        .catch(error => {
            console.error('添加Prompt失败:', error);
            alert('添加失败: ' + error.message);
        });
    };

    // 取消按钮事件
    document.getElementById('cancel_new_prompt').onclick = function() {
        overlay.remove();
    };
};

// 保存API Key函数
window.saveApiKey = function() {
    const selectedProvider = document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '';
    if (!selectedProvider) {
        alert('请先选择AI提供商');
        return;
    }
    
    const apiKeyInput = document.getElementById('api_key');
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';
    
    if (!apiKey) {
        alert('请输入API Key');
        return;
    }
    
    const formData = new FormData();
    formData.append('form_type', 'save_api_key_form');
    formData.append('provider_name_for_key', selectedProvider);
    formData.append('api_key_for_save', apiKey);
    
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            // 显示成功消息
            const messageDiv = document.getElementById('message');
            if (messageDiv) {
                messageDiv.className = 'alert alert-success';
                messageDiv.textContent = 'API Key保存成功！';
                messageDiv.style.display = 'block';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
            }
            console.log('DEBUG: API Key saved successfully for provider:', selectedProvider);
        } else {
            alert('保存失败，请重试');
        }
    })
    .catch(error => {
        console.error('保存API Key失败:', error);
        alert('保存失败: ' + error.message);
    });
};

// 展开/折叠内容函数
window.toggleContent = function(contentId) {
    const content = document.getElementById(contentId);
    if (content) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }
};

// ==================== 目录浏览器功能 ====================

let browserCurrentPath = '';
let browserSelectedPath = '';

// 打开目录浏览器
window.openDirectoryBrowser = function() {
    const modal = document.getElementById('directory-browser-modal');
    if (!modal) return;
    
    modal.style.display = 'flex';
    browserCurrentPath = '';
    browserSelectedPath = '';
    
    // 获取当前输入框的路径作为初始路径
    const dirInput = document.getElementById('directory_path');
    if (dirInput && dirInput.value) {
        const initialPath = dirInput.value;
        navigateToPath(initialPath);
    } else {
        // 否则从根目录开始
        loadDirectoryContents('');
    }
    
    // 点击遮罩层关闭
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeDirectoryBrowser();
        }
    };
    
    // ESC键关闭
    document.addEventListener('keydown', handleEscKey);
};

// 处理ESC键
function handleEscKey(e) {
    if (e.key === 'Escape') {
        closeDirectoryBrowser();
    }
}

// 关闭目录浏览器
window.closeDirectoryBrowser = function() {
    const modal = document.getElementById('directory-browser-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    document.removeEventListener('keydown', handleEscKey);
};

// 加载目录内容
function loadDirectoryContents(path) {
    const url = new URL('/get_directory_contents', window.location.origin);
    if (path) {
        url.searchParams.append('path', path);
    }
    
    fetch(url.toString())
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderDirectoryContents(data);
            } else {
                alert('加载失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('加载目录内容失败:', error);
            alert('加载失败: ' + error.message);
        });
}

// 渲染目录内容
function renderDirectoryContents(data) {
    const listEl = document.getElementById('directory-list');
    const pathEl = document.getElementById('browser-current-path');
    const backBtn = document.getElementById('browser-back-btn');
    const selectBtn = document.getElementById('select-directory-btn');
    
    if (!listEl || !pathEl) return;
    
    browserCurrentPath = data.path || '';
    pathEl.textContent = data.path || '选择驱动器';
    
    // 更新返回按钮
    if (data.parent) {
        backBtn.style.display = 'inline-block';
        backBtn.dataset.parentPath = data.parent;
    } else {
        backBtn.style.display = 'none';
    }
    
    // 清空列表
    listEl.innerHTML = '';
    
    // 如果有驱动器列表
    if (data.drives && data.drives.length > 0) {
        data.drives.forEach(drive => {
            const item = createDirectoryItem(drive, drive, '💻');
            listEl.appendChild(item);
        });
    }
    
    // 如果有子目录
    if (data.directories && data.directories.length > 0) {
        data.directories.forEach(dir => {
            const item = createDirectoryItem(dir.name, dir.path, '📂');
            listEl.appendChild(item);
        });
    } else if (!data.drives || data.drives.length === 0) {
        listEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">此目录下没有子目录</div>';
    }
    
    // 更新选择按钮状态
    if (data.path) {
        selectBtn.disabled = false;
        browserSelectedPath = data.path;
    } else {
        selectBtn.disabled = true;
        browserSelectedPath = '';
    }
}

// 创建目录项
function createDirectoryItem(name, path, icon) {
    const item = document.createElement('div');
    item.className = 'directory-item';
    item.innerHTML = `
        <span class="directory-icon">${icon}</span>
        <span class="directory-name">${escapeHtml(name)}</span>
    `;
    item.onclick = function() {
        navigateToPath(path);
    };
    return item;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 导航到指定路径
window.navigateToPath = function(path) {
    loadDirectoryContents(path);
};

// 返回上级
window.goBack = function() {
    const backBtn = document.getElementById('browser-back-btn');
    if (backBtn && backBtn.dataset.parentPath) {
        navigateToPath(backBtn.dataset.parentPath);
    }
};

// 刷新目录
window.refreshDirectory = function() {
    loadDirectoryContents(browserCurrentPath);
};

// 直接跳转到输入的路径
window.goToDirectPath = function() {
    const input = document.getElementById('direct-path-input');
    if (input && input.value.trim()) {
        navigateToPath(input.value.trim());
    }
};

// 选择当前目录
window.selectDirectory = function() {
    if (browserSelectedPath) {
        const dirInput = document.getElementById('directory_path');
        if (dirInput) {
            dirInput.value = browserSelectedPath;
        }
        closeDirectoryBrowser();
        
        // 保存配置
        saveDirectoryPath(browserSelectedPath);
    }
};

// 保存目录路径到配置
function saveDirectoryPath(path) {
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('directory_path', path);
    formData.append('selected_provider', document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '');
    formData.append('selected_model', document.querySelector('input[name="selected_model"]') ? document.querySelector('input[name="selected_model"]').value : '');
    formData.append('selected_prompt', document.querySelector('input[name="selected_prompt"]') ? document.querySelector('input[name="selected_prompt"]').value : '');
    formData.append('auto_save', 'true');
    
    fetch('/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok && processingManager) {
            processingManager.showMessage('✅ 目录已选择', 'success');
        }
    })
    .catch(error => {
        console.error('保存目录路径失败:', error);
    });
}