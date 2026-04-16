# AI Summary 项目全面功能测试 Spec

## Why

项目已完成基本功能和bug修复，需要对所有功能进行系统性测试，确保每个功能都能正常工作，特别是用户反馈的"服务商删除"等功能。

## What Changes

- 创建全面的功能测试用例
- 验证每个功能模块的正确性
- 确保58个测试全部通过
- 验证数据完整性和一致性

## Impact

- Affected specs: 所有功能模块
- Affected code: app.py, utils.py, managers/, static/script.js, templates/

## ADDED Requirements

### Requirement: 后端基础功能测试
The system SHALL 正确处理所有后端路由请求。

#### Scenario: 主页加载
- **WHEN** 访问主页 GET /
- **THEN** 返回200状态码，页面包含AI相关内容

#### Scenario: 静态资源加载
- **WHEN** 访问 CSS 和 JS 静态资源
- **THEN** 返回200状态码

#### Scenario: 测试页面加载
- **WHEN** 访问 GET /simple_test
- **THEN** 返回200状态码

### Requirement: 服务商管理功能测试
The system SHALL 正确执行服务商的所有CRUD操作。

#### Scenario: 添加服务商
- **WHEN** POST 新增服务商表单
- **THEN** 服务商被添加到config.json，返回302重定向

#### Scenario: 更新API Key
- **WHEN** POST 更新API Key表单
- **THEN** API Key被更新，返回302重定向

#### Scenario: 删除服务商到回收站
- **WHEN** POST 删除服务商表单
- **THEN** 服务商从providers列表移除，进入trash.providers

#### Scenario: 从回收站恢复服务商
- **WHEN** POST 恢复服务商表单
- **THEN** 服务商从trash.providers恢复，回到providers列表

#### Scenario: 永久删除服务商
- **WHEN** POST 永久删除服务商表单
- **THEN** 服务商从trash.providers中彻底删除

### Requirement: Prompt管理功能测试
The system SHALL 正确执行Prompt的所有CRUD操作。

#### Scenario: 添加Prompt
- **WHEN** POST 新增Prompt表单
- **THEN** Prompt被添加到config.json，返回302重定向

#### Scenario: 删除Prompt到回收站
- **WHEN** POST 删除Prompt表单
- **THEN** Prompt从custom_prompts移除，进入trash.custom_prompts

#### Scenario: 从回收站恢复Prompt
- **WHEN** POST 恢复Prompt表单
- **THEN** Prompt从trash.custom_prompts恢复，回到custom_prompts

#### Scenario: 永久删除Prompt
- **WHEN** POST 永久删除Prompt表单
- **THEN** Prompt从trash.custom_prompts中彻底删除

### Requirement: 配置选择功能测试
The system SHALL 正确保存和加载用户配置。

#### Scenario: 保存配置选择
- **WHEN** POST 配置选择表单
- **THEN** 配置被保存到user_preferences，返回302重定向

### Requirement: 处理状态API测试
The system SHALL 正确返回处理状态。

#### Scenario: 获取处理状态
- **WHEN** GET /get_processing_status
- **THEN** 返回JSON包含status字段，状态码200

#### Scenario: 取消处理
- **WHEN** POST /cancel_processing
- **THEN** 在空闲状态返回400，否则返回200

#### Scenario: 清理会话
- **WHEN** GET /clear_session
- **THEN** Session被清空，返回200

### Requirement: JavaScript功能测试
The system SHALL 正确执行所有JavaScript函数。

#### Scenario: JavaScript语法检查
- **WHEN** node --check script.js
- **THEN** 无语法错误

#### Scenario: 无prompt()调用
- **WHEN** 检查script.js内容
- **THEN** 不存在被阻塞的prompt()调用

#### Scenario: 关键函数定义检查
- **WHEN** 检查以下函数定义
- **THEN** handleProviderAddNew, handlePromptAddNew, selectProvider, selectPrompt, deleteProvider, deletePrompt, startProcessing, updateUI, showMessage, processingManager实例 全部存在

### Requirement: 模板功能测试
The system SHALL 正确渲染所有页面元素。

#### Scenario: 页面元素存在
- **WHEN** 检查index.html
- **THEN** 服务商下拉菜单、模型下拉菜单、Prompt下拉菜单、目录输入框、开始按钮、状态显示 全部存在

#### Scenario: 事件绑定正确
- **WHEN** 检查index.html
- **THEN** handleProviderAddNew、handlePromptAddNew、开始按钮onclick事件 全部正确绑定

### Requirement: 配置文件测试
The system SHALL 正确维护配置数据结构。

#### Scenario: 必需字段存在
- **WHEN** 检查config.json
- **THEN** providers, current_provider, custom_prompts, current_prompt, file_paths, trash, user_preferences 全部存在

#### Scenario: 服务商结构完整
- **WHEN** 检查providers中的服务商
- **THEN** name, base_url, api_key, models 字段全部存在

#### Scenario: Trash结构正确
- **WHEN** 检查config.json
- **THEN** trash.providers 和 trash.custom_prompts 都是字典{}而非数组[]

### Requirement: Utils模块测试
The system SHALL 正确提供所有工具函数。

#### Scenario: 函数定义检查
- **WHEN** 检查utils.py
- **THEN** load_config, save_config, load_custom_prompts, save_custom_prompts, scan_txt_files, process_file, save_response, load_providers, save_provider 全部定义

## MODIFIED Requirements

无

## REMOVED Requirements

无