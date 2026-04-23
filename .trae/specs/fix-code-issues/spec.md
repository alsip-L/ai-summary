# 代码问题修复 Spec

## Why
项目中存在多个代码问题，包括一个导致模块无法导入的严重语法错误、线程安全隐患、逻辑缺陷和安全漏洞，需要系统性修复以保证应用稳定运行。

## What Changes
- 修复 `file_browser_service.py` 文件损坏（语法错误 + 类体重复）
- 修复 `TaskService` 中 db session 存储与注释矛盾的问题
- 修复 `ProcessingState` 取消流程中的冗余状态覆盖
- 修复 `ConfigManager.__init__` 线程安全问题
- 修复任务目录路径未校验 `allowed_paths` 的安全漏洞
- 修复用户偏好中 API Key 明文存储问题
- 修复 WebSocket 日志端点无认证问题
- 修复 `AIClient` 重试期间不可响应取消的问题
- 修复前端自动尝试默认密钥获取 token 的安全隐患

## Impact
- Affected code: `app/services/file_browser_service.py`, `app/services/task_service.py`, `app/services/processing_state.py`, `core/config.py`, `app/auth.py`, `app/routers/logs.py`, `app/services/ai_client.py`, `app/services/task_runner.py`, `frontend-vue/src/App.vue`

## ADDED Requirements

### Requirement: 修复 file_browser_service.py 文件损坏
系统 SHALL 修复 `file_browser_service.py` 中的语法错误和类体重复问题。该文件第35行正则表达式字符串字面量未闭合，且第113行起重复了整个类体，导致模块无法被 Python 导入。

#### Scenario: 文件修复后可正常导入
- **WHEN** Python 尝试导入 `app.services.file_browser_service`
- **THEN** 模块成功导入，无 SyntaxError

#### Scenario: 路径校验功能正常
- **WHEN** 用户访问文件浏览器
- **THEN** `_validate_path` 正确过滤根目录路径（如 `C:\`、`/`），仅允许 `allowed_paths` 白名单内的路径

### Requirement: 修复 TaskService db session 存储矛盾
系统 SHALL 移除 `TaskService` 中将 db session 存储为实例变量的做法。当前代码注释声明"不保存为实例变量以避免后台线程误用"，但第31行却执行了 `self._db = db`，存在后台线程误用 db session 的风险。

#### Scenario: db session 不被后台线程访问
- **WHEN** `TaskService` 启动后台处理线程
- **THEN** 后台线程无法访问请求级别的 db session

### Requirement: 修复 ProcessingState 取消流程冗余
系统 SHALL 修复 `_run_processing_loop` 中取消流程的冗余调用。当 `is_cancelled()` 返回 True 时，当前代码调用 `cancel()` 再次设置状态，但 `request_cancel()` 已经设置了所有相关字段（`_cancelled`、`_status`、`_error`），导致冗余写入。

#### Scenario: 取消流程无冗余状态写入
- **WHEN** 用户取消正在运行的任务
- **THEN** 状态仅被设置一次，无冗余的 `cancel()` 调用

### Requirement: 修复 ConfigManager 初始化线程安全
系统 SHALL 修复 `ConfigManager.__init__` 中的线程安全问题。当前 `__init__` 检查 `self._loaded` 时未持有类锁，两个线程可能同时看到 `_loaded` 为 False 并同时调用 `_load()`。

#### Scenario: 多线程并发创建 ConfigManager
- **WHEN** 多个线程同时首次调用 `ConfigManager()`
- **THEN** `_load()` 仅被调用一次，配置数据一致

### Requirement: 任务目录路径校验 allowed_paths
系统 SHALL 在 `TaskService.start()` 中增加对目录路径的 `allowed_paths` 校验。当前仅检查目录是否存在，未校验是否在允许的路径范围内，用户可处理系统任意目录的文件。

#### Scenario: 用户指定不允许的目录
- **WHEN** 用户启动任务时指定不在 `allowed_paths` 白名单内的目录
- **THEN** 返回错误提示"目录不在允许的访问范围内"

#### Scenario: 用户指定允许的目录
- **WHEN** 用户启动任务时指定在 `allowed_paths` 白名单内的目录
- **THEN** 任务正常启动

### Requirement: 用户偏好 API Key 加密存储
系统 SHALL 对存储在 `UserPreference` 表中的 API Key 进行加密，与 Provider 的 API Key 加密方式一致（Fernet 对称加密）。

#### Scenario: API Key 加密存储
- **WHEN** 用户保存包含 API Key 的偏好设置
- **THEN** API Key 在数据库中以加密形式存储

#### Scenario: API Key 正确解密读取
- **WHEN** 读取用户偏好中的 API Key
- **THEN** 正确解密并返回明文 API Key

### Requirement: WebSocket 日志端点增加认证
系统 SHALL 为 `/api/logs/ws` WebSocket 端点增加认证机制，防止未授权用户访问日志数据。

#### Scenario: 未认证连接被拒绝
- **WHEN** 未携带有效 token 的客户端连接 WebSocket 日志端点
- **THEN** 连接被拒绝或关闭

#### Scenario: 已认证连接正常工作
- **WHEN** 携带有效 token 的客户端连接 WebSocket 日志端点
- **THEN** 正常接收日志推送

### Requirement: AI 调用重试期间可响应取消
系统 SHALL 将 `AIClient.call` 和 `TaskRunner._process_file_with_retry` 中的 `time.sleep()` 替换为可中断的等待机制，使重试等待期间能响应取消请求。

#### Scenario: 重试等待期间用户取消
- **WHEN** AI 调用失败进入重试等待，用户在此期间请求取消
- **THEN** 等待立即中断，任务状态变为已取消

### Requirement: 移除前端默认密钥自动尝试
系统 SHALL 移除 `App.vue` 中自动使用默认密钥 `default-dev-secret-key-please-change-in-prod` 获取 API Token 的逻辑。此行为在用户修改密钥后仍会尝试默认值，存在安全隐患。

#### Scenario: 前端不自动尝试默认密钥
- **WHEN** 应用初始化时
- **THEN** 不自动使用默认密钥获取 token，需要用户手动输入密钥
