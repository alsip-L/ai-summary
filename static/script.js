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
            apiKey = prompt('请输入API Key:');
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
        }

        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(CONFIG.API_ENDPOINTS.GET_STATUS);
                const status = await response.json();
                this.updateUI(status);

                if (status.status === 'completed' || status.status === 'error') {
                    this.isProcessing = false;
                    clearInterval(this.progressInterval);
                    
                    if (status.status === 'completed') {
                        const duration = (Date.now() - this.startTime) / 1000;
                        this.showMessage(`处理完成！耗时: ${Utils.formatDuration(duration)}`, 'success');
                    } else {
                        this.showMessage(`处理失败: ${status.error}`, 'error');
                    }
                }
            } catch (error) {
                console.error('获取状态失败:', error);
            }
        }, CONFIG.API_ENDPOINTS.UI_UPDATE_INTERVAL);
    }

    updateUI(status) {
        console.log('=== DEBUG: updateUI开始执行 ===');
        console.log('DEBUG: 接收到的状态数据:', status);
        console.log('DEBUG: 状态类型:', typeof status);
        console.log('DEBUG: 状态键:', Object.keys(status));
        
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

        // 显示结果区域
        resultsArea.style.display = 'block';
        resultsArea.classList.add('fade-in');
        
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

        // 5秒后自动隐藏
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);

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
    
    // 对于prompt-content-dropdown和trash-dropdown，内容区域有特殊的选择器
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
    
    // 关闭其他下拉框
    document.querySelectorAll('.dropdown-content').forEach(el => {
        if (el.classList.contains('show') && el !== content) {
            el.classList.remove('show');
        }
    });
    
    // 同时处理prompt-content-options和trash-options
    if (dropdownId === 'prompt-content-dropdown' || dropdownId === 'trash-dropdown') {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
        console.log('DEBUG: Toggled special dropdown, new display:', content.style.display);
    } else {
        content.classList.toggle('show');
        console.log('DEBUG: After toggle, classes:', content.className);
    }
};

// 选择提供商并自动更新模型
window.selectProvider = function(providerName) {
    console.log('DEBUG: Selecting provider (optimized):', providerName);
    
    // 获取当前表单数据
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_provider', providerName);
    formData.append('selected_model', document.querySelector('input[name="selected_model"]') ? document.querySelector('input[name="selected_model"]').value : '');
    formData.append('selected_prompt', document.querySelector('input[name="selected_prompt"]') ? document.querySelector('input[name="selected_prompt"]').value : '');
    formData.append('directory_path', document.getElementById('directory_path') ? document.getElementById('directory_path').value : '');
    formData.append('auto_save', 'true');
    
    // 提交表单并刷新页面
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            throw new Error('保存失败');
        }
    })
    .catch(error => {
        console.error('选择失败:', error);
        alert('选择失败: ' + error.message);
    });
};

// 选择Prompt并自动保存到config.json
window.selectPrompt = function(promptName) {
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_prompt', promptName);
    formData.append('selected_provider', document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '');
    formData.append('selected_model', document.querySelector('input[name="selected_model"]') ? document.querySelector('input[name="selected_model"]').value : '');
    formData.append('directory_path', document.getElementById('directory_path') ? document.getElementById('directory_path').value : '');
    formData.append('auto_save', 'true');
    
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
        console.error('选择失败:', error);
    });
};

// 选择模型并自动保存到config.json
window.selectModel = function(modelName) {
    const formData = new FormData();
    formData.append('form_type', 'config_selection_form');
    formData.append('selected_model', modelName);
    formData.append('selected_provider', document.querySelector('input[name="selected_provider"]') ? document.querySelector('input[name="selected_provider"]').value : '');
    formData.append('selected_prompt', document.querySelector('input[name="selected_prompt"]') ? document.querySelector('input[name="selected_prompt"]').value : '');
    formData.append('directory_path', document.getElementById('directory_path') ? document.getElementById('directory_path').value : '');
    formData.append('auto_save', 'true');
    
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
        console.error('选择失败:', error);
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
    // 使用TrashManager中可能存在的showProviderForm函数，或者创建一个简单的prompt方式
    const name = prompt('请输入新提供商名称:');
    if (!name) return;
    
    const url = prompt('请输入API地址:');
    if (!url) return;
    
    const apiKey = prompt('请输入API Key (可选):') || '';
    const modelName = prompt('请输入模型名称 (可选，留空使用默认):') || '';
    
    // 处理模型配置
    let models;
    if (modelName) {
        models = {};
        models[modelName] = modelName;
    } else {
        models = {};
        models['默认模型'] = name.toLowerCase().replace(/\s+/g, '-') + '-model';
    }
    
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

// 新增Prompt处理函数
window.handlePromptAddNew = function() {
    const name = prompt('请输入新Prompt名称:');
    if (!name) return;
    
    const content = prompt('请输入Prompt内容:');
    if (!content) return;
    
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
            window.location.reload();
        } else {
            alert('添加失败，请重试');
        }
    })
    .catch(error => {
        console.error('添加Prompt失败:', error);
        alert('添加失败: ' + error.message);
    });
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