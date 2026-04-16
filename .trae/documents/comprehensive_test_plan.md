# AI Summary 项目 - 全面测试计划

## 项目结构

```
ai_summary/
├── app.py                      # Flask 主应用
├── utils.py                    # 工具函数
├── config.json                 # 配置文件
├── requirements.txt             # 依赖
├── run.py                      # 启动脚本
├── core/                       # 核心模块
│   ├── __init__.py
│   ├── config.py               # 配置管理
│   ├── logger.py              # 日志
│   └── exceptions.py           # 异常
├── managers/                   # 管理器
│   ├── __init__.py
│   ├── model_manager.py        # 大模型管理
│   ├── prompt_manager.py       # Prompt管理
│   ├── file_manager.py         # 文件路径管理
│   ├── provider_manager.py     # 提供商管理（旧）
│   └── trash_manager.py        # 回收站管理
├── processors/                  # 处理器
│   ├── __init__.py
│   ├── ai_processor.py         # AI处理
│   └── file_processor.py      # 文件处理
├── templates/                 # 模板
│   ├── index.html              # 主页面
│   └── simple_test.html        # 测试页面
├── static/                     # 静态资源
│   ├── script.js               # JavaScript
│   └── style.css              # 样式
└── tests/                      # 测试
    ├── test_core.py
    └── test_managers.py
```

---

## 后端 API 测试清单

### 1. 主页和静态资源

| 编号 | 测试项 | 端点 | 方法 | 预期结果 |
|-----|-------|------|------|---------|
| 1.1 | 主页加载 | `/` | GET | 200, 包含AI Summary内容 |
| 1.2 | CSS加载 | `/static/style.css` | GET | 200 |
| 1.3 | JS加载 | `/static/script.js` | GET | 200 |
| 1.4 | 测试页面 | `/simple_test` | GET | 200 |

### 2. 服务商管理

| 编号 | 测试项 | 端点 | 方法 | 数据 | 预期结果 |
|-----|-------|------|------|------|---------|
| 2.1 | 新增服务商 | `/` | POST | `form_type=save_provider_form`, `provider_name`, `base_url`, `api_key_for_save`, `models` | 302重定向 |
| 2.2 | 更新API Key | `/` | POST | `form_type=save_api_key_form`, `provider_name_for_key`, `api_key_for_save` | 302重定向 |
| 2.3 | 删除服务商 | `/` | POST | `form_type=delete_provider_form`, `provider_name_to_delete` | 302重定向 |
| 2.4 | 恢复服务商 | `/` | POST | `form_type=restore_provider_form`, `provider_name_to_restore` | 302重定向 |
| 2.5 | 永久删除服务商 | `/` | POST | `form_type=permanent_delete_provider_form`, `provider_name_to_permanent_delete` | 302重定向 |

### 3. Prompt管理

| 编号 | 测试项 | 端点 | 方法 | 数据 | 预期结果 |
|-----|-------|------|------|------|---------|
| 3.1 | 新增Prompt | `/` | POST | `form_type=save_prompt_form`, `prompt_name`, `prompt_content` | 302重定向 |
| 3.2 | 删除Prompt | `/` | POST | `form_type=delete_prompt_form`, `prompt_name_to_delete` | 302重定向 |
| 3.3 | 恢复Prompt | `/` | POST | `form_type=restore_prompt_form`, `prompt_name_to_restore` | 302重定向 |
| 3.4 | 永久删除Prompt | `/` | POST | `form_type=permanent_delete_prompt_form`, `prompt_name_to_permanent_delete` | 302重定向 |

### 4. 配置选择

| 编号 | 测试项 | 端点 | 方法 | 数据 | 预期结果 |
|-----|-------|------|------|------|---------|
| 4.1 | 保存配置选择 | `/` | POST | `form_type=config_selection_form`, `selected_provider`, `selected_model`, `selected_prompt`, `directory_path`, `auto_save` | 302重定向 |

### 5. 处理状态API

| 编号 | 测试项 | 端点 | 方法 | 预期结果 |
|-----|-------|------|------|---------|
| 5.1 | 获取处理状态 | `/get_processing_status` | GET | 200, JSON包含status字段 |
| 5.2 | 取消处理(空闲) | `/cancel_processing` | POST | 400 (无任务运行) |
| 5.3 | 取消处理(运行中) | `/cancel_processing` | POST | 200 (有任务运行) |

### 6. 会话管理

| 编号 | 测试项 | 端点 | 方法 | 预期结果 |
|-----|-------|------|------|---------|
| 6.1 | 清理会话 | `/clear_session` | GET | 返回清理成功消息 |

---

## 前端 JavaScript 测试清单

### 1. 函数定义检查

| 编号 | 函数名 | 检查项 |
|-----|-------|-------|
| 1.1 | `handleProviderAddNew` | 存在，无prompt()调用 |
| 1.2 | `handlePromptAddNew` | 存在，无prompt()调用 |
| 1.3 | `handleProviderSelect` | 存在 |
| 1.4 | `handlePromptSelect` | 存在 |
| 1.5 | `handleDeleteProvider` | 存在 |
| 1.6 | `handleDeletePrompt` | 存在 |
| 1.7 | `startProcessing` | 存在，无阻塞的prompt()调用 |
| 1.8 | `updateStatus` | 存在 |
| 1.9 | `showMessage` | 存在 |
| 1.10 | `showError` | 存在 |

### 2. 浏览器兼容性检查

| 编号 | 检查项 | 方法 |
|-----|-------|------|
| 2.1 | JavaScript语法 | `node --check` 无错误 |
| 2.2 | 无 `prompt()` 调用 | Grep搜索 |
| 2.3 | 无未定义的函数调用 | 控制台检查 |

---

## 模板测试清单

### 1. 页面元素检查

| 编号 | 元素ID/类 | 检查项 |
|-----|----------|-------|
| 1.1 | `providerDropdown` | 服务商下拉菜单存在 |
| 1.2 | `modelDropdown` | 模型下拉菜单存在 |
| 1.3 | `promptDropdown` | Prompt下拉菜单存在 |
| 1.4 | `directoryInput` | 目录输入框存在 |
| 1.5 | `startButton` | 开始按钮存在 |
| 1.6 | `statusDisplay` | 状态显示区域存在 |

### 2. 表单绑定检查

| 编号 | 元素 | 绑定函数 |
|-----|------|---------|
| 2.1 | `+ 新增服务商` 点击 | `handleProviderAddNew()` |
| 2.2 | `+ 新增Prompt` 点击 | `handlePromptAddNew()` |
| 2.3 | 开始按钮点击 | `startProcessing()` |
| 2.4 | 服务商选择 | `handleProviderSelect()` |
| 2.5 | Prompt选择 | `handlePromptSelect()` |

---

## 配置文件测试清单

### 1. 配置文件读写

| 编号 | 测试项 | 方法 |
|-----|-------|------|
| 1.1 | 加载配置 | `load_config()` |
| 1.2 | 保存配置 | `save_config()` |
| 1.3 | 配置文件不存在时创建默认 | 检查逻辑 |
| 1.4 | 配置文件损坏时处理 | 异常处理 |

### 2. 配置文件结构

| 编号 | 字段 | 类型 | 必需 |
|-----|------|------|------|
| 2.1 | `providers` | Array | 是 |
| 2.2 | `current_provider` | Object | 是 |
| 2.3 | `custom_prompts` | Object | 是 |
| 2.4 | `current_prompt` | String | 是 |
| 2.5 | `file_paths` | Object | 是 |
| 2.6 | `trash` | Object | 是 |
| 2.7 | `user_preferences` | Object | 是 |

---

## 实施步骤

### 第1步：后端API测试
- 使用 requests 库测试所有POST表单提交
- 验证302重定向和状态码
- 验证配置文件更新

### 第2步：前端JavaScript检查
- 使用 node --check 验证语法
- Grep搜索禁用函数
- 检查函数定义

### 第3步：模板元素检查
- 读取HTML检查必要元素
- 验证事件绑定

### 第4步：综合测试
- 启动Flask应用
- 使用test_client进行集成测试
- 验证完整的表单提交流程

### 第5步：生成测试报告
- 汇总所有测试结果
- 标识失败项和原因
- 提出修复建议

---

## 预期产出

1. **test_comprehensive.py** - 完整的测试脚本
2. **TEST_REPORT.md** - 测试报告，包含：
   - 测试执行结果
   - 发现的问题列表
   - 修复优先级建议
