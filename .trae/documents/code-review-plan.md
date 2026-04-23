# 项目代码问题检查计划

## 项目概述

AI Summary 是一个基于 FastAPI + Vue 3 + SQLite 的智能文本批量处理服务，通过 OpenAI 兼容 API 对 txt 文件进行 AI 摘要处理。项目包含后端 API、Vue 前端、Python SDK 和测试套件。

> 注：之前已有一轮修复（见 `.trae/specs/fix-code-issues/`），修复了语法错误、线程安全、路径校验等问题。本轮检查在此基础上进行。

---

## 发现的问题

### 🔴 严重问题（可能导致运行时错误或安全漏洞）

#### 1. TaskService 存在竞态条件 — 可能同时启动两个任务

**位置**: [task_service.py](file:///d:/git/ai_summary/app/services/task_service.py#L59-L100)

**问题**: `start()` 方法先调用 `self._state.is_running()` 检查是否有任务在运行，然后在后台线程中调用 `self._runner.run_batch()`，而 `run_batch()` 内部才调用 `self._state.start()` 设置状态为 "scanning"。在 `is_running()` 返回 False 到后台线程实际开始执行 `_state.start()` 之间存在时间窗口，另一个请求可能也通过 `is_running()` 检查并启动第二个任务。

**修复方案**: 在 `start()` 方法中，在启动后台线程之前就调用 `self._state.start()` 将状态设置为 "scanning"，确保原子性。后台线程失败时需要重置状态。

---

#### 2. 多个 API 端点缺少认证保护

**位置**: [tasks.py](file:///d:/git/ai_summary/app/routers/tasks.py#L46-L80), [files.py](file:///d:/git/ai_summary/app/routers/files.py#L16-L59)

**问题**: 以下端点没有 `require_auth` 依赖，任何人都可访问：
- `GET /api/tasks/status` — 可查看任务状态和结果
- `POST /api/tasks/cancel` — 可取消正在运行的任务
- `GET /api/tasks/failed` — 可查看失败记录
- `DELETE /api/tasks/failed` — 可清除失败记录
- `GET /api/files/drives` — 可浏览磁盘驱动器
- `GET /api/files/directory` — 可浏览目录结构
- `GET /api/files/result` — 可查看处理结果文件内容

对于个人项目，如果仅在内网使用，风险较低。但若暴露到公网，这些端点可被未授权访问。

**修复方案**: 为敏感端点添加 `Depends(require_auth)` 保护。对于只读端点（如 status、drives），可选择性保护。

---

#### 3. API 响应格式不一致

**位置**: [provider_service.py](file:///d:/git/ai_summary/app/services/provider_service.py#L11-L12), [prompt_service.py](file:///d:/git/ai_summary/app/services/prompt_service.py#L11-L12), [trash_service.py](file:///d:/git/ai_summary/app/services/trash_service.py#L11-L12)

**问题**: 
- `ProviderService.list_all()` 返回原始列表 `[{...}, {...}]`
- `PromptService.list_all()` 返回原始列表 `[{...}, {...}]`
- `TrashService.get_all()` 返回原始字典 `{providers: [...], custom_prompts: [...]}`
- 其他方法返回 `{"success": True, ...}` 格式

前端通过 `Array.isArray()` 判断做了兼容，但 API 格式不一致会让 SDK 和其他消费者困惑。

**修复方案**: 统一所有 API 响应为 `{"success": True, "data": ...}` 格式，或至少在列表接口也包裹 `{"success": True, ...}` 结构。

---

### 🟡 中等问题（代码质量、可维护性、潜在风险）

#### 4. `_interruptible_sleep` 代码重复

**位置**: [ai_client.py](file:///d:/git/ai_summary/app/services/ai_client.py#L68-L76), [task_runner.py](file:///d:/git/ai_summary/app/services/task_runner.py#L26-L34)

**问题**: `AIClient._interruptible_sleep()` 和 `TaskRunner._interruptible_sleep()` 实现完全相同，违反 DRY 原则。

**修复方案**: 提取为公共工具函数，放在 `core/utils.py` 或 `app/services/processing_state.py` 中。

---

#### 5. TaskService 每次请求重新创建，但依赖单例状态

**位置**: [dependencies.py](file:///d:/git/ai_summary/app/dependencies.py#L39-L40), [task_service.py](file:///d:/git/ai_summary/app/services/task_service.py#L23-L29)

**问题**: `get_task_service()` 每次请求都创建新的 `TaskService` 实例，而 `TaskService.__init__` 每次都创建新的 `TaskRunner`、`AIClient` 和 `FailedRecordService`。但 `ProcessingState` 是单例，所以所有实例共享同一状态。这种设计导致：
- 每次请求都创建不必要的对象
- 如果 `ProcessingState.reset()` 被调用，旧的 `TaskRunner`/`AIClient` 仍持有旧实例的引用

**修复方案**: 将 `TaskService` 也改为单例或应用级缓存，通过 FastAPI 的 `app.state` 存储。

---

#### 6. OpenAI 客户端在后台线程中未显式关闭

**位置**: [task_service.py](file:///d:/git/ai_summary/app/services/task_service.py#L94-L99)

**问题**: 后台线程中创建的 `OpenAI` 客户端使用 `httpx` 连接池，但从未显式关闭。虽然 Python GC 最终会回收，但可能导致连接泄漏。

**修复方案**: 在 `_run_in_thread` 函数中使用 `try/finally` 确保客户端关闭：
```python
def _run_in_thread():
    client = OpenAI(...)
    try:
        self._runner.run_batch(...)
    finally:
        client.close()
```

---

#### 7. 前端 API Token 不持久化，刷新页面丢失

**位置**: [useApi.js](file:///d:/git/ai_summary/frontend-vue/src/composables/useApi.js#L4-L5)

**问题**: `_apiToken` 存储在 JavaScript 变量中，页面刷新后丢失。用户每次刷新都需要重新输入 secret_key 获取 token。

**修复方案**: 将 token 存储在 `sessionStorage` 中，页面刷新后自动恢复。

---

#### 8. 前端不处理 401 错误自动重新认证

**位置**: [useApi.js](file:///d:/git/ai_summary/frontend-vue/src/composables/useApi.js#L32-L38)

**问题**: 当 API 返回 401 时（如 secret_key 被修改导致 token 失效），前端只是抛出错误，不会提示用户重新输入密钥。

**修复方案**: 在 `request()` 函数中捕获 401 错误，清除缓存的 token，并提示用户重新认证。

---

#### 9. FailedRecordService 静态方法自行创建数据库会话

**位置**: [failed_record_service.py](file:///d:/git/ai_summary/app/services/failed_record_service.py#L33-L61)

**问题**: `get_failed_records()`、`clear_failed_records()` 和 `get_sources_for_retry()` 是静态方法，使用 `get_db_session()` 自行创建会话，而不是使用请求级别的会话。这与其他 Service 使用依赖注入的 `db` 会话不一致。

**修复方案**: 将这些方法改为实例方法，接收 `db` 参数，或在路由层通过 `Depends(get_db)` 传入会话。

---

#### 10. SDK 导入了已弃用的 `ConnectionError`

**位置**: [_base.py](file:///d:/git/ai_summary/sdk/ai_summary_sdk/_base.py#L6)

**问题**: `_base.py` 第 6 行 `from .exceptions import ConnectionError` 导入了已弃用的别名。`exceptions.py` 中已将 `ConnectionError` 标记为弃用，推荐使用 `SDKConnectionError`。

**修复方案**: 将导入改为 `from .exceptions import SDKConnectionError`，并更新所有引用。

---

### 🟢 轻微问题（代码风格、小改进）

#### 11. config.json 和启动脚本使用默认弱凭据

**位置**: [config.json](file:///d:/git/ai_summary/config.json#L3), [start.bat](file:///d:/git/ai_summary/start.bat#L99), [start.sh](file:///d:/git/ai_summary/start.sh#L32)

**问题**: 默认配置使用 `default-dev-secret-key-please-change-in-prod` 和 `admin/admin`。虽然代码中有警告，但启动脚本在创建默认配置时也使用了这些弱凭据。

**修复方案**: 启动脚本创建默认配置时生成随机 secret_key，或至少在控制台输出醒目警告。

---

#### 12. ProviderCreate/PromptCreate 的 name 字段缺少 min_length 校验

**位置**: [provider.py](file:///d:/git/ai_summary/app/schemas/provider.py#L6), [prompt.py](file:///d:/git/ai_summary/app/schemas/prompt.py#L6)

**问题**: `ProviderCreate.name` 只有 `max_length=100` 没有 `min_length`，允许空字符串通过 Schema 校验（虽然 Service 层会检查）。`PromptCreate.name` 同理。

**修复方案**: 添加 `min_length=1` 约束，与 Service 层校验保持一致。

---

#### 13. FileProcessor.save_response 覆盖已有文件无备份

**位置**: [file_processor.py](file:///d:/git/ai_summary/app/services/file_processor.py#L52-L62)

**问题**: 保存 AI 响应时，如果目标 .md 文件已存在，直接覆盖，仅输出 warning 日志。用户可能意外丢失之前的处理结果。

**修复方案**: 对于个人项目，当前行为（覆盖+警告日志）可以接受。如需更安全，可在覆盖前备份旧文件。

---

#### 14. Docker 健康检查不验证 API 功能

**位置**: [dockerfile](file:///d:/git/ai_summary/dockerfile#L42-L43), [docker-compose.yml](file:///d:/git/ai_summary/docker-compose.yml#L18-L19)

**问题**: 健康检查仅 `curl -f http://localhost:5000/`，只验证 HTTP 服务是否响应，不验证 API 是否正常工作。

**修复方案**: 改为检查 API 端点如 `/api/system/info`，或添加专门的 `/health` 端点。

---

#### 15. docker-compose.yml 端口映射与配置端口不同步

**位置**: [docker-compose.yml](file:///d:/git/ai_summary/docker-compose.yml#L9)

**问题**: Docker Compose 固定映射 `5000:5000`，但用户可在 `config.json` 中修改端口。如果修改了端口，Docker 映射不会自动调整。

**修复方案**: 使用环境变量 `PORT` 并在 docker-compose.yml 中通过 `${PORT:-5000}:${PORT:-5000}` 动态映射。

---

## 实施步骤

### 步骤 1: 修复 TaskService 竞态条件（严重）
- 在 `TaskService.start()` 和 `retry_failed()` 中，启动后台线程前先调用 `self._state.start()` 占位
- 后台线程的 `run_batch`/`run_retry_batch` 不再调用 `self._state.start()`（已由主线程设置）
- 后台线程异常时重置状态

### 步骤 2: 为敏感 API 端点添加认证（严重）
- 为 `/api/tasks/cancel`、`DELETE /api/tasks/failed` 添加 `require_auth`
- 为 `/api/files/directory`、`/api/files/result` 添加 `require_auth`
- `/api/tasks/status`、`GET /api/tasks/failed`、`/api/files/drives` 可选择性保护

### 步骤 3: 统一 API 响应格式（严重）
- `ProviderService.list_all()` 返回 `ok(providers=...)` 
- `PromptService.list_all()` 返回 `ok(prompts=...)`
- `TrashService.get_all()` 返回 `ok(providers=..., custom_prompts=...)`
- 同步更新前端 store 中的数据解析逻辑
- 同步更新 SDK 的响应处理

### 步骤 4: 提取公共 `_interruptible_sleep`（中等）
- 将 `_interruptible_sleep` 移到 `processing_state.py` 或 `core/utils.py`
- `AIClient` 和 `TaskRunner` 引用公共实现

### 步骤 5: 修复 OpenAI 客户端资源泄漏（中等）
- 在 `_run_in_thread` 中用 `try/finally` 确保 `client.close()`

### 步骤 6: 前端 Token 持久化和 401 处理（中等）
- 将 token 存储到 `sessionStorage`
- 在 `request()` 中处理 401 错误，清除 token 并提示重新认证

### 步骤 7: 修复 SDK 弃用导入（轻微）
- `_base.py` 中将 `ConnectionError` 改为 `SDKConnectionError`

### 步骤 8: Schema 添加 min_length 校验（轻微）
- `ProviderCreate.name` 和 `PromptCreate.name` 添加 `min_length=1`

### 步骤 9: 验证
- 运行现有测试确保无回归
- 手动测试关键流程（启动任务、取消任务、查看状态）
