* [x] file\_browser\_service.py 语法错误已修复，模块可正常导入

* [x] file\_browser\_service.py 重复类体已删除，文件结构正确

* [x] file\_browser\_service.py \_validate\_path 正确过滤根目录路径

* [x] TaskService 不再将 db session 存储为实例变量

* [x] TaskService 后台线程无法访问请求级 db session

* [x] ProcessingState 取消流程无冗余状态写入

* [x] ConfigManager 多线程并发初始化不会重复加载配置

* [x] TaskService.start() 校验目录路径是否在 allowed\_paths 内

* [x] 不允许的目录路径被拒绝并返回错误

* [x] UserPreference 表中的 API Key 以加密形式存储

* [x] 加密的 API Key 可正确解密读取

* [x] 旧版明文 API Key 数据兼容（解密失败时回退为明文）

* [x] WebSocket 日志端点需要认证才能连接

* [x] 未认证的 WebSocket 连接被拒绝

* [x] 已认证的 WebSocket 连接正常接收日志

* [x] AIClient 重试等待期间可响应取消请求

* [x] TaskRunner 重试等待期间可响应取消请求

* [x] 前端不再自动尝试默认密钥获取 API Token

* [x] 所有修改后的 Python 文件通过 py\_compile 语法检查

