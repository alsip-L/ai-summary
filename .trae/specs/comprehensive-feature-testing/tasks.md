# Tasks

- [x] Task 1: 创建测试脚本结构
  - [x] SubTask 1.1: 创建 TestResult 类用于收集测试结果
  - [x] SubTask 1.2: 创建 test_backend_basic 函数测试后端基础功能
  - [x] SubTask 1.3: 创建 test_provider_management 函数测试服务商管理
  - [x] SubTask 1.4: 创建 test_prompt_management 函数测试Prompt管理

- [x] Task 2: 实现后端基础功能测试
  - [x] SubTask 2.1: 测试主页加载 (GET /)
  - [x] SubTask 2.2: 测试CSS加载 (GET /static/style.css)
  - [x] SubTask 2.3: 测试JS加载 (GET /static/script.js)
  - [x] SubTask 2.4: 测试页面加载 (GET /simple_test)

- [x] Task 3: 实现服务商管理功能测试
  - [x] SubTask 3.1: 测试新增服务商到config.json
  - [x] SubTask 3.2: 测试更新API Key
  - [x] SubTask 3.3: 测试删除服务商到回收站（验证trash.providers变化）
  - [x] SubTask 3.4: 测试从回收站恢复服务商
  - [x] SubTask 3.5: 测试永久删除服务商

- [x] Task 4: 实现Prompt管理功能测试
  - [x] SubTask 4.1: 测试新增Prompt
  - [x] SubTask 4.2: 测试删除Prompt到回收站
  - [x] SubTask 4.3: 测试从回收站恢复Prompt
  - [x] SubTask 4.4: 测试永久删除Prompt

- [x] Task 5: 实现配置和处理状态API测试
  - [x] SubTask 5.1: 测试保存配置选择
  - [x] SubTask 5.2: 测试获取处理状态
  - [x] SubTask 5.3: 测试取消处理
  - [x] SubTask 5.4: 测试清理会话

- [x] Task 6: 实现JavaScript功能测试
  - [x] SubTask 6.1: 测试JavaScript语法 (node --check)
  - [x] SubTask 6.2: 测试无prompt()调用
  - [x] SubTask 6.3: 测试关键函数定义存在

- [x] Task 7: 实现模板功能测试
  - [x] SubTask 7.1: 测试页面元素存在
  - [x] SubTask 7.2: 测试事件绑定正确

- [x] Task 8: 实现配置文件测试
  - [x] SubTask 8.1: 测试必需字段存在
  - [x] SubTask 8.2: 测试服务商结构完整
  - [x] SubTask 8.3: 测试trash结构正确（providers和custom_prompts都是字典）

- [x] Task 9: 实现Utils模块测试
  - [x] SubTask 9.1: 测试关键函数定义

- [x] Task 10: 运行完整测试并验证结果
  - [x] SubTask 10.1: 执行测试脚本
  - [x] SubTask 10.2: 确认58/58测试全部通过

# Task Dependencies

- Task 2-9 可以在 Task 1 完成后并行执行
- Task 10 依赖 Task 2-9 全部完成