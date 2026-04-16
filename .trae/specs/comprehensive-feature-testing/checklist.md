# Checklist

## 后端基础功能
- [x] 主页加载测试通过
- [x] CSS加载测试通过
- [x] JS加载测试通过
- [x] 测试页面加载测试通过

## 服务商管理功能
- [x] 新增服务商测试通过
- [x] 更新API Key测试通过
- [x] 删除服务商到回收站测试通过（验证数据变化）
- [x] 恢复服务商测试通过（验证数据变化）
- [x] 永久删除服务商测试通过（验证数据变化）

## Prompt管理功能
- [x] 新增Prompt测试通过
- [x] 删除Prompt到回收站测试通过
- [x] 恢复Prompt测试通过
- [x] 永久删除Prompt测试通过

## 配置和处理状态API
- [x] 保存配置选择测试通过
- [x] 获取处理状态测试通过
- [x] 取消处理测试通过
- [x] 清理会话测试通过

## JavaScript功能
- [x] JavaScript语法检查通过
- [x] prompt()调用检查通过（已清除）
- [x] handleProviderAddNew函数定义存在
- [x] handlePromptAddNew函数定义存在
- [x] selectProvider函数定义存在
- [x] selectPrompt函数定义存在
- [x] deleteProvider函数定义存在
- [x] deletePrompt函数定义存在
- [x] startProcessing函数定义存在
- [x] updateUI函数定义存在
- [x] showMessage函数定义存在
- [x] processingManager实例存在

## 模板功能
- [x] 服务商下拉菜单元素存在
- [x] 模型下拉菜单元素存在
- [x] Prompt下拉菜单元素存在
- [x] 目录输入框元素存在
- [x] 开始按钮元素存在
- [x] 状态显示元素存在
- [x] handleProviderAddNew事件绑定存在
- [x] handlePromptAddNew事件绑定存在
- [x] 开始按钮onclick事件绑定存在

## 配置文件
- [x] providers字段存在
- [x] current_provider字段存在
- [x] custom_prompts字段存在
- [x] current_prompt字段存在
- [x] file_paths字段存在
- [x] trash字段存在
- [x] user_preferences字段存在
- [x] 服务商name字段存在
- [x] 服务商base_url字段存在
- [x] 服务商api_key字段存在
- [x] 服务商models字段存在

## Utils模块
- [x] load_config函数定义存在
- [x] save_config函数定义存在
- [x] load_custom_prompts函数定义存在
- [x] save_custom_prompts函数定义存在
- [x] scan_txt_files函数定义存在
- [x] process_file函数定义存在
- [x] save_response函数定义存在
- [x] load_providers函数定义存在
- [x] save_provider函数定义存在

## 最终验证
- [x] 58/58测试全部通过
- [x] 项目正常运行（Flask应用状态码200）