# 目录选择器功能实现计划

## 需求分析
当前功能：用户需要手动在文本输入框中输入处理目录的完整路径
期望功能：点击后能打开目录浏览器来选择目录

## 技术方案（跨平台兼容）

**兼容性考虑**：不使用 tkinter（Linux Docker 环境下无 GUI），采用纯 Web 方案：

### 后端实现
- 添加 `/browse_directory` API：列出指定目录下的子目录
- 添加 `/get_drives` API（Windows）：获取可用的驱动器列表
- 支持跨平台路径处理

### 前端实现
- 创建一个模态框（Modal）作为目录浏览器
- 显示当前路径、目录列表、返回上一级按钮
- 支持直接跳转到指定路径
- 支持选择目录

## 修改文件列表

### 1. app.py
- 添加 `/get_directory_contents` 路由：列出目录内容
- 添加 `/get_available_drives` 路由（Windows）
- 实现路径处理逻辑

### 2. templates/index.html
- 添加目录浏览器模态框的 HTML 结构
- 在目录输入框旁边添加"📁 浏览"按钮

### 3. static/style.css
- 添加目录浏览器的样式
- 添加模态框的样式

### 4. static/script.js
- 实现目录浏览器的完整逻辑
- 实现路径导航、目录选择等功能

## 实现步骤

### 步骤 1：后端 API 实现
1. 创建 `/get_directory_contents?path=...` 端点
2. 返回指定路径下的所有子目录列表
3. 创建 `/get_available_drives` 端点（Windows）
4. 处理路径安全问题

### 步骤 2：前端界面修改
1. 在目录输入框旁边添加"📁 浏览"按钮
2. 添加目录浏览器模态框 HTML
3. 模态框包含：当前路径显示、目录列表、操作按钮

### 步骤 3：前端交互实现
1. 实现 `openDirectoryBrowser()` 函数
2. 实现 `navigateToPath()` 函数
3. 实现 `goBack()` 函数
4. 实现 `selectDirectory()` 函数
5. 实现模态框的打开/关闭

## 技术细节

### 后端 API 设计

```
GET /get_directory_contents?path=<path>
Response:
{
  "success": true,
  "path": "C:\\Users\\...",
  "parent": "C:\\Users",
  "directories": [
    {"name": "Documents", "path": "C:\\Users\\...\\Documents"},
    {"name": "Downloads", "path": "C:\\Users\\...\\Downloads"}
  ]
}

GET /get_available_drives
Response:
{
  "success": true,
  "drives": ["C:\\", "D:\\"]
}
```

### 前端目录浏览器结构
```
┌─────────────────────────────────┐
│  选择目录                [×]    │
├─────────────────────────────────┤
│ 📁 当前路径: C:\Users\...      │
│  [⬅️ 返回上级]  [刷新]         │
├─────────────────────────────────┤
│ 📂 Documents                    │
│ 📂 Downloads                    │
│ 📂 Pictures                     │
│ ...                             │
├─────────────────────────────────┤
│  或直接输入路径: [_________]   │
│              [取消]  [选择]     │
└─────────────────────────────────┘
```

### 兼容性
- ✅ Windows（支持驱动器）
- ✅ Linux（支持根目录 /）
- ✅ Docker 环境（无 GUI 依赖）
- ✅ 纯 Web 实现
