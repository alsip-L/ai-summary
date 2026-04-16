---
name: codebase-feature-inventory
overview: 全面梳理AI Summary项目的功能模块和特性清单，按层级关系组织，为后续重构提供优先级评估依据
todos:
  - id: output-analysis
    content: 将上述功能模块分析整理为结构化文档输出给用户
    status: completed
---

## 产品概述

AI Summary 是一个基于 Flask + OpenAI API 的智能文本批量处理 Web 应用，核心功能是扫描目录中的 txt 文件，通过 AI 模型生成摘要并保存为 md 文件。

## 核心特性

- AI 提供商管理（多服务商、多模型配置）
- 自定义提示词管理（创建/编辑/删除/选择）
- 批量文件处理（目录扫描、AI调用、结果保存）
- 实时处理进度追踪与取消控制
- 回收站软删除与恢复机制
- 目录浏览器（可视化选择处理目录）
- 用户偏好持久化与自动保存
- 系统设置热更新（日志级别即时生效）

## 功能模块与特性清单

### 一、核心业务功能（高业务价值）

| 编号 | 功能模块 | 当前位置 | 描述 | 代码健康度 |
| --- | --- | --- | --- | --- |
| F1 | 批量文件处理引擎 | app.py/run_processing_task + utils.py/FileManager | 扫描目录中txt文件，逐个调用AI生成摘要，保存为同名md文件。支持多编码读取(utf-8/gbk) | 重复3处 |
| F2 | AI调用与客户端管理 | app.py + utils.py/FileManager.process_file + processors/ai_processor.py | 基于OpenAI SDK调用大模型，传入system prompt和文件内容。processors/中有未启用的重试机制 | 重复3处 |
| F3 | 处理状态追踪 | services/state_service.py (ProcessingState) | 线程安全的单例状态管理器，跟踪idle/scanning/processing/completed/error/cancelled六种状态，含进度、结果列表、历史记录 | 唯一真实使用 |
| F4 | 异步任务调度 | app.py/start_processing路由 + threading.Thread | 后台线程执行处理任务，前端2秒轮询获取状态 | 正常 |


### 二、配置与数据管理功能（高业务价值）

| 编号 | 功能模块 | 当前位置 | 描述 | 代码健康度 |
| --- | --- | --- | --- | --- |
| F5 | 统一配置管理 | core/config_manager.py (ConfigManager) | 线程安全单例，支持点号路径访问(如providers.0.name)、深拷贝保护、批量更新、热重载 | 正常 |
| F6 | AI提供商管理 | app.py/ProviderManager + utils.py/ProviderManager + managers/model_manager.py + services/provider_service.py | 管理AI服务商的名称、base_url、api_key、模型列表的CRUD操作 | **重复4处** |
| F7 | 提示词管理 | app.py/PromptManager + utils.py/PromptManager + managers/prompt_manager.py + services/prompt_service.py | 管理自定义system prompt的CRUD，含验证逻辑(名称/内容非空、长度限制) | **重复4处** |
| F8 | 用户偏好管理 | utils.py/UserPreferencesManager | 持久化用户选择的provider/model/prompt/directory，优先级：session > 偏好 > 默认值 | 正常 |
| F9 | 回收站管理 | utils.py + managers/trash_manager.py | 提供商和提示词的软删除(移入回收站)、恢复、永久删除。操作原子性依赖多次config.set | 重复2处 |


### 三、Web接口服务（中业务价值）

| 编号 | API路由 | 描述 |
| --- | --- | --- |
| F10 | GET/POST / | 主页面路由，处理10+种form_type的表单提交(config_selection/save_provider/save_prompt/delete_provider/delete_prompt/restore/permanent_delete/add_model/delete_model/save_api_key) |
| F11 | POST /start_processing | 启动异步处理任务，验证参数后创建后台线程 |
| F12 | GET /get_processing_status | 返回ProcessingState的当前状态字典 |
| F13 | POST /cancel_processing | 设置取消标志并更新状态 |
| F14 | GET /get_available_drives | 获取系统驱动器列表(Windows)或根目录(Linux) |
| F15 | GET /get_directory_contents | 获取指定目录的子目录列表，支持上级导航 |
| F16 | GET /view_result | 读取md/txt结果文件内容，含目录遍历防护 |
| F17 | POST /save_system_settings | 保存系统设置(debug_level/flask_secret_key/host/port/debug)，支持日志级别热更新 |
| F18 | GET /clear_session | 清理Flask session |


### 四、前端功能（中业务价值）

| 编号 | 功能模块 | 位置 | 描述 |
| --- | --- | --- | --- |
| F19 | ProcessingManager | script.js | 处理任务启动、进度监控(2s轮询)、UI更新、取消操作 |
| F20 | ConfigManager(前端) | script.js | 自动保存(30s间隔 + 2s防抖)、表单变化监听、AJAX无刷新提交 |
| F21 | 自定义下拉菜单 | script.js + index.html | 提供商/模型/Prompt选择器，支持动态切换(无刷新)、新增/删除 |
| F22 | 目录浏览器 | script.js + index.html | 模态框，支持驱动器浏览、子目录导航、直接路径输入、选择后自动保存 |
| F23 | 结果文件查看器 | script.js | 模态框显示md文件内容，含XSS防护(HTML转义) |
| F24 | 回收站前端 | script.js/TrashManager | 软删除确认、恢复、永久删除(二次确认) |
| F25 | 系统设置面板 | index.html + script.js | 日志级别/Flask密钥/监听地址/端口/Debug模式配置，区分即时生效与需重启 |
| F26 | 暗黑主题切换 | script.js/UIManager | localStorage持久化主题偏好 |
| F27 | 消息通知系统 | script.js/ProcessingManager.showMessage | 顶部消息条，支持success/error/warning/info，自动2s消失+动画 |
| F28 | 提供商/模型新增对话框 | script.js | 动态创建模态对话框，支持新增服务商(名称/URL/Key/模型)和单独添加模型 |


### 五、基础设施工具（低业务价值但高必要性）

| 编号 | 功能模块 | 位置 | 描述 | 代码健康度 |
| --- | --- | --- | --- | --- |
| F29 | 统一日志管理 | core/logger.py | 基于Python logging，控制台输出，支持热更新日志级别 | 正常 |
| F30 | 自定义异常体系 | core/exceptions.py | 6种异常类(AISummaryException/ConfigError/ProviderError/FileProcessingError/ValidationError/ProcessingError/TrashError) | 正常 |
| F31 | URL安全解码 | app.py/safe_url_decode + safe_url_decode_form | 支持utf-8/gbk/gb2312多编码的URL解码 | 正常 |
| F32 | 前端工具函数 | script.js/Utils | debounce防抖、escapeHtml防XSS、formatBytes/formatDuration格式化 | 正常 |
| F33 | Session消息机制 | app.py/set_session_message | 统一的Flash消息设置与读取 | 正常 |


### 六、部署与运维（低业务价值但高必要性）

| 编号 | 功能模块 | 位置 | 描述 |
| --- | --- | --- | --- |
| F34 | Docker镜像构建 | dockerfile | Python 3.11-slim + gunicorn(2 workers, 120s timeout) + 健康检查 |
| F35 | Docker Compose编排 | docker-compose.yml | 单容器部署，挂载config.json/data/logs/output卷 |
| F36 | 快速启动脚本 | start.bat / start.sh | Windows/Linux快速启动 |


### 七、测试（低完整度）

| 编号 | 功能模块 | 位置 | 描述 |
| --- | --- | --- | --- |
| F37 | 单元测试 | tests/test_core.py + tests/test_managers.py | 核心模块和管理器测试 |
| F38 | 功能测试 | test_all_features.py + test_comprehensive.py + test_full_features.py | 根目录的3个综合测试文件 |


---

## 关键架构问题（重构决策依据）

### 问题1：严重代码重复（最高优先级）

- **ProviderManager**: app.py(轻量版) + utils.py(完整版) + managers/model_manager.py(完整版) + services/provider_service.py(deprecated)
- **PromptManager**: app.py(轻量版) + utils.py(完整版) + managers/prompt_manager.py(完整版+验证) + services/prompt_service.py(deprecated)
- **FileManager**: utils.py(完整版) + managers/file_manager.py(路径管理版) + services/file_service.py(deprecated) + processors/file_processor.py(deprecated)
- **TrashManager**: utils.py(完整版) + managers/trash_manager.py(完整版)
- **debug_print**: app.py + utils.py 各定义一次

### 问题2：废弃代码未清理

- `services/` 下3个模块(provider_service/prompt_service/file_service)标记deprecated，未被引用
- `processors/` 下2个模块(ai_processor/file_processor)标记deprecated，未被引用
- `core/config.py` 仅做转发，已废弃
- `utils.py` 中大量"向后兼容"包装函数(20+个)

### 问题3：app.py职责过重

- 包含5个业务类(ProviderManager/PromptManager/SelectionManager)
- 包含10+种表单处理逻辑
- 包含9个路由
- 包含异步任务执行逻辑
- 总计约780行，混合路由/业务逻辑/工具函数

### 问题4：配置存储单一文件风险

- 所有数据(providers/prompts/trash/preferences/system_settings)存储在单个config.json
- 无数据版本控制，无备份机制
- 高频写入(每次选择变更都写文件)存在性能和可靠性风险

### 问题5：前端script.js过于庞大

- 单文件约2100行，包含5个类+20+个全局函数
- 业务逻辑(表单提交/API调用)与UI逻辑(下拉菜单/动画)未分离