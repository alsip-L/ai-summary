---
name: project-issues-fix
overview: 全面检查项目代码中的Bug、安全问题、功能缺陷和代码质量问题，并逐一修复。
todos:
  - id: fix-delete-model-route
    content: 在 app.py 添加 delete_model_form 后端路由处理
    status: completed
  - id: fix-frontend-issues
    content: 修复 script.js 双重编码和进度显示 1/0 问题
    status: completed
  - id: add-result-viewer
    content: 添加 /view_result 路由并将前端 alert 改为查看链接
    status: completed
  - id: cleanup-config-deprecated
    content: 清理 config.json 测试数据并修复 deprecated 模块引用
    status: completed
---

## 用户需求

用户要求检查项目是否还有其他问题。

## 问题清单

基于代码审查，发现以下需要修复的问题：

### Bug（功能缺陷）

1. **删除模型功能缺失后端路由**：前端 `script.js` 发送 `form_type: 'delete_model_form'`，但 `app.py` 中没有对应的处理分支，删除模型按钮点击后无效果
2. **前端 deleteProvider 双重编码**：`script.js` 第1286行使用 `encodeURIComponent(providerName)`，而 FormData 本身会自动编码，导致中文 provider 名被双重编码，后端 `safe_url_decode` 解码后可能仍然乱码
3. **前端进度显示 1/0 异常**：`script.js` 第405行 `processed === 0 ? 1 : processed`，当任务刚开始状态为 processing 但 processed=0 时显示 "1/0"

### 代码质量

4. **config.json 测试残留数据**：`VerifyTest` prompt 是测试遗留，需清理
5. **deprecated 模块互相引用**：`ai_processor.py` 第196行引用同为 deprecated 的 `file_processor.py`

### UX 体验

6. **结果文件只能 alert 显示路径**：点击结果文件链接弹 alert，无法直接查看/下载

## 排除项（用户已确认不需修复）

- Flask Secret Key 硬编码（本地服务器）
- API Key 明文存储（用户要求频繁修改，不用环境变量）
- 目录遍历风险（本地服务器可接受）
- ProcessingState 单例限制（设计如此，单任务处理）

## 技术栈

- 后端：Flask (Python)
- 前端：原生 JavaScript + HTML/CSS
- 配置管理：ConfigManager 单例（core/config_manager.py）
- 数据存储：config.json 文件

## 实施方案

### 1. 补充删除模型后端路由（Bug 修复 - 严重）

在 `app.py` 的 POST 路由分支中添加 `delete_model_form` 处理，调用已有的 `delete_model_from_provider` 函数。该函数在 `utils.py` 中已存在并可用。

### 2. 修复前端双重编码（Bug 修复 - 中等）

移除 `script.js` 第1286行的 `encodeURIComponent`，让 FormData 自行处理编码，与 deletePrompt 等其他删除操作保持一致。

### 3. 修复前端进度显示逻辑（Bug 修复 - 低）

修改 `script.js` 第405行的逻辑：仅在 `processed > 0` 时显示实际数字，`processed === 0` 且 `total > 0` 时显示 `0/total`，而非 `1/0`。

### 4. 清理 config.json 测试数据

移除 `VerifyTest` prompt，保留 `SummaryPrompt`（用户实际使用的）。

### 5. 修复 deprecated 模块引用

在 `ai_processor.py` 的 `process_file` 兼容函数中，移除对 `file_processor.py` 的引用，改为内联读取文件逻辑，保持模块独立性。

### 6. 结果文件查看功能

添加 Flask 后端路由 `/view_result` 提供文件内容查看，前端将 alert 改为在新窗口打开查看页面。

## 目录结构

```
d:/git/ai_summary/
├── app.py                      # [MODIFY] 添加 delete_model_form 路由 + /view_result 路由
├── static/script.js            # [MODIFY] 修复双重编码、进度显示、结果查看链接
├── config.json                 # [MODIFY] 清理测试残留数据
├── processors/ai_processor.py  # [MODIFY] 移除对 deprecated file_processor 的引用
```