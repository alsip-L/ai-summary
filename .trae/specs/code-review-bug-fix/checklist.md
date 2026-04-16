# Checklist

- [x] core/logger.py 没有导入错误，debug_print 函数工作正常
- [x] core/config.py 单例模式正确实现，配置读写正常
- [x] core/exceptions.py 所有异常类正确定义
- [x] processors/file_processor.py 文件操作正确处理异常
- [x] processors/ai_processor.py AI调用逻辑正确，错误处理完善
- [x] managers/provider_manager.py 提供商CRUD操作正常
- [x] managers/prompt_manager.py 提示词管理功能正常
- [x] managers/trash_manager.py 回收站功能正常
- [x] app/routes.py 路由正确，状态管理线程安全
- [x] app/__init__.py 应用工厂正确创建应用
- [x] utils/validators.py 验证函数正确处理各种输入
- [x] utils/helpers.py 辅助函数正常工作
- [x] 所有单元测试通过
- [x] 没有发现新的bug
