# Tasks

- [x] Task 1: 修复 file_browser_service.py 文件损坏（严重 - 语法错误导致模块无法导入）
  - [x] SubTask 1.1: 修复第35行未闭合的正则表达式字符串，补全为 `r'^[A-Za-z]:[\\/]?$', p)`
  - [x] SubTask 1.2: 删除第113行起重复的类体代码（从 `, p)  # 匹配 C:\...` 到文件末尾）
  - [x] SubTask 1.3: 验证修复后文件可正常导入且 `_validate_path` 功能正确

- [x] Task 2: 修复 TaskService db session 存储矛盾
  - [x] SubTask 2.1: 将 `_validate_and_create_client` 改为接收 db 参数而非使用 `self._db`
  - [x] SubTask 2.2: 移除 `self._db = db`，在 `start()` 和 `retry_failed()` 中将 db 作为局部变量传递
  - [x] SubTask 2.3: 验证后台线程无法访问请求级 db session

- [x] Task 3: 修复 ProcessingState 取消流程冗余
  - [x] SubTask 3.1: 在 `_run_processing_loop` 中，将 `is_cancelled()` + `cancel()` 替换为 `is_cancelled()` + 直接 break/return
  - [x] SubTask 3.2: 验证取消流程状态正确

- [x] Task 4: 修复 ConfigManager 初始化线程安全
  - [x] SubTask 4.1: 在 `__init__` 中使用 `_class_lock` 保护 `_loaded` 检查和 `_load()` 调用
  - [x] SubTask 4.2: 验证多线程并发初始化不会导致重复加载

- [x] Task 5: 任务目录路径校验 allowed_paths
  - [x] SubTask 5.1: 在 `TaskService.start()` 中增加目录路径的 `allowed_paths` 校验
  - [x] SubTask 5.2: 复用 `FileBrowserService._validate_path` 的路径校验逻辑
  - [x] SubTask 5.3: 验证不允许的目录被拒绝，允许的目录正常启动

- [x] Task 6: 用户偏好 API Key 加密存储
  - [x] SubTask 6.1: 在 `SettingsRepository.save()` 中对 `api_key` 字段调用 `encrypt_api_key` 加密
  - [x] SubTask 6.2: 在 `SettingsRepository.get_all()` 中对 `api_key` 字段调用 `decrypt_api_key` 解密
  - [x] SubTask 6.3: 处理旧数据兼容（明文数据解密失败时回退为明文）
  - [x] SubTask 6.4: 验证 API Key 加密存储和正确解密读取

- [x] Task 7: WebSocket 日志端点增加认证
  - [x] SubTask 7.1: 修改 `/api/logs/ws` 端点，在连接时校验 query parameter 中的 token
  - [x] SubTask 7.2: 前端 WebSocket 连接时附带 token 参数
  - [x] SubTask 7.3: 验证未认证连接被拒绝，已认证连接正常工作

- [x] Task 8: AI 调用重试期间可响应取消
  - [x] SubTask 8.1: 在 `AIClient.call` 中将 `time.sleep(delay)` 替换为分片 sleep + 取消检查
  - [x] SubTask 8.2: 在 `TaskRunner._process_file_with_retry` 中将 `time.sleep(delay)` 替换为分片 sleep + 取消检查
  - [x] SubTask 8.3: 验证重试等待期间取消能立即中断

- [x] Task 9: 移除前端默认密钥自动尝试
  - [x] SubTask 9.1: 移除 `App.vue` 中 `onMounted` 里自动使用默认密钥获取 token 的代码块
  - [x] SubTask 9.2: 改为需要用户手动输入密钥获取 token（或从其他安全方式获取）
  - [x] SubTask 9.3: 验证前端不再自动尝试默认密钥

# Task Dependencies
- Task 1 无依赖，应优先修复（阻塞其他验证）
- Task 2, 3, 4, 5 互相独立，可并行
- Task 6 依赖 Task 1（需要 file_browser_service 可导入）
- Task 7 前后端改动可并行
- Task 8 依赖 Task 3（取消机制相关）
- Task 9 无依赖，可独立进行
