---
name: remove-env-vars-add-web-settings
overview: 移除所有环境变量依赖，将配置项（DEBUG_LEVEL、FLASK_SECRET_KEY、HOST、PORT等）迁移到config.json中，并在Web界面添加"系统设置"面板让用户可以直接修改这些值。
design:
  architecture:
    framework: html
  styleKeywords:
    - Consistent
    - Minimal
  fontSystem:
    fontFamily: PingFang-SC
    heading:
      size: 16px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 13px
      weight: 400
  colorSystem:
    primary:
      - "#007bff"
    background:
      - "#f9f9f9"
    text:
      - "#333333"
      - "#666666"
    functional:
      - "#28a745"
      - "#ffc107"
todos:
  - id: config-json-settings
    content: 在 config.json 和 ConfigManager 中新增 system_settings 默认配置
    status: completed
  - id: backend-env-removal
    content: 移除 app.py/utils.py/run.py/logger.py 中所有环境变量引用，改为从 config.json 读取
    status: completed
    dependencies:
      - config-json-settings
  - id: logger-hot-update
    content: 为 logger.py 增加日志级别热更新方法，新增 /save_system_settings API 路由
    status: completed
    dependencies:
      - backend-env-removal
  - id: frontend-settings-panel
    content: 在 index.html 和 script.js 中新增系统设置面板及交互逻辑
    status: completed
    dependencies:
      - logger-hot-update
  - id: docker-and-docs
    content: 更新 docker-compose.yml、dockerfile、README.md、DOCKER_DEPLOYMENT.md 移除环境变量
    status: completed
    dependencies:
      - backend-env-removal
---

## Product Overview

将项目中所有环境变量配置项迁移到 config.json 统一管理，并在 Web 界面新增"系统设置"面板，使用户可以在浏览器中直接修改所有配置项（包括日志级别、Flask密钥、监听地址、端口等），无需手动编辑配置文件或设置环境变量。

## Core Features

- 在 config.json 中新增 `system_settings` 配置节，包含：debug_level、flask_secret_key、host、port、debug
- Web 侧边栏新增"系统设置"可折叠面板，支持在线修改上述所有配置项
- 日志级别支持热更新（修改后立即生效，无需重启）
- 需要重启才能生效的配置项（host、port、flask_secret_key）在 UI 中明确提示
- 移除所有 `os.environ.get` / `os.getenv` 调用，统一从 config.json 读取
- 更新 Docker 部署文件，移除环境变量传递
- 更新 README 和部署文档

## Tech Stack

- 后端：Python + Flask（现有项目栈）
- 前端：HTML + CSS + 原生 JavaScript（现有项目栈）
- 配置存储：config.json（现有 ConfigManager 单例模式）
- 部署：Docker + docker-compose

## Implementation Approach

**核心策略**：将环境变量配置迁移到 config.json 的 `system_settings` 节，复用现有 ConfigManager 单例，在 Web 界面新增系统设置面板实现可视化编辑。

**关键决策**：

1. **日志级别热更新**：在 `core/logger.py` 中增加 `update_level()` 方法，Web 保存设置时调用该方法实时更新日志级别，无需重启
2. **需要重启的配置项**：host、port、flask_secret_key 修改后保存在 config.json，但需重启生效。UI 中用醒目提示告知用户
3. **启动顺序**：`run.py` 和 `app.py` 初始化时先加载 config.json 读取系统设置，不再依赖环境变量
4. **Docker 兼容**：移除 docker-compose.yml 和 dockerfile 中的 environment 段，所有配置通过 config.json 持久化卷挂载管理

## Implementation Notes

- `core/logger.py` 使用 `@lru_cache()` 缓存 logger 实例，需增加动态更新日志级别的静态方法，不破坏缓存机制
- `app.py` 的 `secret_key` 在 Flask 应用创建时设置，后续修改只影响 config.json 存储，需重启才生效
- `utils.py:14` 的 `DEBUG_LEVEL` 变量虽已定义但未被实际使用（日志均通过 `core/logger` 处理），可直接移除
- Docker 环境变量 `PYTHONDONTWRITEBYTECODE` 和 `PYTHONUNBUFFERED` 属于 Python 运行时优化，保留在 dockerfile 的 ENV 中（不属于用户可配置项）
- 修改系统设置的后端路由需返回是否需要重启的标识，前端据此显示提示

## Architecture Design

```
config.json
  └── system_settings (新增)
        ├── debug_level: "ERROR"
        ├── flask_secret_key: "default-dev-secret-key..."
        ├── host: "0.0.0.0"
        ├── port: 5000
        └── debug: false

Web UI (sidebar)
  └── 系统设置面板 (新增)
        ├── 日志级别下拉选择 (热更新)
        ├── Flask密钥输入框 (重启生效)
        ├── 监听地址输入框 (重启生效)
        ├── 端口输入框 (重启生效)
        ├── Debug模式开关 (重启生效)
        └── 保存按钮

API
  └── POST /save_system_settings (新增)
        ├── 读取表单数据
        ├── 写入 config.json
        ├── 热更新日志级别
        └── 返回 {success, needs_restart}
```

## Directory Structure

```
c:/Users/15832/Downloads/ai_summary/ai_summary/
├── config.json                    # [MODIFY] 新增 system_settings 配置节
├── app.py                         # [MODIFY] 移除环境变量读取，从 config.json 获取 secret_key 和 debug_level；新增 /save_system_settings 路由；将 system_settings 传入模板
├── utils.py                       # [MODIFY] 移除 DEBUG_LEVEL 环境变量引用
├── run.py                         # [MODIFY] 从 config.json 读取 host/port/debug，移除环境变量
├── core/
│   ├── config_manager.py          # [MODIFY] _default_config() 中增加 system_settings 默认值
│   └── logger.py                  # [MODIFY] 从 config.json 读取 debug_level；增加 update_level() 动态更新方法；移除环境变量引用
├── templates/
│   └── index.html                 # [MODIFY] 侧边栏新增系统设置折叠面板
├── static/
│   └── script.js                  # [MODIFY] 新增系统设置面板的交互逻辑和保存函数
├── docker-compose.yml             # [MODIFY] 移除 environment 段中的业务环境变量
├── dockerfile                     # [MODIFY] 移除 FLASK_APP/FLASK_ENV 业务环境变量，保留 Python 运行时变量
├── README.md                      # [MODIFY] 更新配置说明，移除环境变量文档
└── DOCKER_DEPLOYMENT.md           # [MODIFY] 更新部署文档，移除环境变量说明
```

## Design Style

在现有侧边栏底部（回收站下方）新增"系统设置"折叠面板，风格与现有回收站下拉面板保持一致。使用相同的 custom-dropdown 组件模式，展开后显示各配置项表单。

## Page Block Design (侧边栏新增区块)

- **系统设置面板**：使用 custom-dropdown 组件，点击展开/收起。展开后显示：
- 日志级别：下拉选择框（DEBUG/INFO/WARNING/ERROR/CRITICAL），旁边标注"即时生效"
- Flask密钥：文本输入框，旁边标注"需重启生效"
- 监听地址：文本输入框，旁边标注"需重启生效"
- 监听端口：数字输入框，旁边标注"需重启生效"
- Debug模式：开关/复选框，旁边标注"需重启生效"
- 保存按钮：点击后 AJAX 提交，成功后显示提示消息