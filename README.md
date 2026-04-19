# AI Summary

基于 FastAPI + OpenAI API 的智能文本批量处理 Web 应用。扫描目录中的 txt 文件，调用 AI 生成摘要，输出为 md 文件。

## 功能特性

- **AI 提供商管理** - 添加/编辑/删除 AI 服务提供商，支持多模型配置
- **自定义提示词** - 创建和管理 AI 处理模板，作为 system prompt 发送
- **批量文件处理** - 扫描目录批量处理 txt 文件，自动跳过已处理文件
- **实时进度追踪** - 轮询式进度更新，支持取消操作
- **回收站** - 软删除与恢复机制
- **目录浏览** - 内置文件浏览器，支持直接输入路径
- **用户偏好** - 自动保存选择配置
- **管理后台** - SQLAdmin 数据库管理界面

## 技术栈

- **后端**: FastAPI, SQLAlchemy 2.0, Pydantic v2, OpenAI SDK, Uvicorn
- **前端**: Vue 3, Pinia, Vite
- **数据库**: SQLite
- **架构**: 分层架构 + Repository 模式
- **容器化**: Docker, Docker Compose

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+ (前端构建)
- pip

### 安装

```bash
git clone <repository-url>
cd ai_summary
pip install -r requirements.txt
```

### 配置

编辑 `config.json`，配置系统设置：

```json
{
  "system_settings": {
    "debug_level": "ERROR",
    "secret_key": "your-secret-key",
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  }
}
```

### 运行

```bash
# Windows
python run.py

# Linux/macOS
python3 run.py
```

访问 http://localhost:5000

## 使用流程

1. **选择目录** - 在侧边栏输入或浏览选择包含 txt 文件的目录
2. **配置 AI** - 选择提供商、模型和提示词
3. **开始处理** - 点击"开始处理"按钮
4. **查看结果** - 处理完成后在原目录生成对应的 md 文件

## API 路由

### 提供商 `/api/providers`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/providers/` | GET | 列出所有活跃提供商 |
| `/api/providers/` | POST | 创建提供商 |
| `/api/providers/{name}` | DELETE | 删除提供商（移入回收站） |
| `/api/providers/{name}/api-key` | PUT | 更新 API Key |
| `/api/providers/{name}/models` | POST | 添加模型 |
| `/api/providers/{name}/models/{model_name}` | DELETE | 删除模型 |

### 提示词 `/api/prompts`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/prompts/` | GET | 列出所有提示词 |
| `/api/prompts/` | POST | 创建提示词 |
| `/api/prompts/{name}` | DELETE | 删除提示词（移入回收站） |

### 任务 `/api/tasks`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/start` | POST | 启动处理任务 |
| `/api/tasks/status` | GET | 获取处理状态 |
| `/api/tasks/cancel` | POST | 取消处理任务 |

### 文件 `/api/files`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/files/drives` | GET | 获取可用驱动器（Windows） |
| `/api/files/directory` | GET | 获取目录内容（?path=xxx） |
| `/api/files/result` | GET | 查看处理结果（?path=xxx） |

### 设置 `/api/settings`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/settings/trash` | GET | 获取回收站内容 |
| `/api/settings/trash/restore/provider/{name}` | POST | 恢复提供商 |
| `/api/settings/trash/restore/prompt/{name}` | POST | 恢复提示词 |
| `/api/settings/trash/provider/{name}` | DELETE | 永久删除提供商 |
| `/api/settings/trash/prompt/{name}` | DELETE | 永久删除提示词 |
| `/api/settings/preferences` | GET/PUT | 用户偏好 |

## 项目结构

```
ai_summary/
├── run.py                  # 应用入口脚本
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── core/                   # 核心模块
│   ├── config.py           # 配置管理（单例+线程安全+原子写入）
│   ├── errors.py           # 自定义异常层级
│   ├── log.py              # 日志管理
│   └── utils.py            # 工具函数（多编码文件读取）
├── app/                    # FastAPI 应用主包
│   ├── main.py             # FastAPI 应用创建与配置
│   ├── database.py         # SQLAlchemy 数据库配置（SQLite）
│   ├── dependencies.py     # FastAPI 依赖注入
│   ├── models.py           # SQLAlchemy ORM 模型
│   ├── admin.py            # SQLAdmin 管理后台视图
│   ├── routers/            # API 路由层
│   │   ├── providers.py    # 提供商 CRUD 路由
│   │   ├── prompts.py      # 提示词 CRUD 路由
│   │   ├── tasks.py        # 任务处理路由
│   │   ├── files.py        # 文件浏览路由
│   │   ├── trash.py        # 回收站路由
│   │   └── settings.py    # 设置/偏好路由
│   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── provider.py     # Provider 相关 Schema
│   │   ├── prompt.py       # Prompt 相关 Schema
│   │   ├── settings.py     # Settings 相关 Schema
│   │   └── task.py         # Task 相关 Schema
│   └── services/           # 业务服务层
│       ├── provider_service.py  # 提供商业务逻辑
│       ├── provider_repo.py     # 提供商数据访问（Repository）
│       ├── prompt_service.py    # 提示词业务逻辑
│       ├── prompt_repo.py       # 提示词数据访问
│       ├── task_service.py      # 任务处理服务（含 ProcessingState 单例）
│       ├── trash_service.py     # 回收站业务逻辑
│       ├── trash_repo.py        # 回收站数据访问
│       ├── settings_service.py  # 设置/偏好业务逻辑
│       └── file_browser_service.py  # 文件浏览服务
├── frontend-vue/           # Vue 3 前端项目
│   ├── src/
│   │   ├── App.vue         # 根组件
│   │   ├── composables/
│   │   │   └── useApi.js   # API 调用封装
│   │   ├── stores/         # Pinia 状态管理
│   │   │   ├── provider.js # 提供商 Store
│   │   │   ├── prompt.js   # 提示词 Store
│   │   │   ├── task.js     # 任务 Store
│   │   │   └── trash.js    # 回收站 Store
│   │   └── components/     # Vue 组件
│   │       ├── ProviderPanel.vue
│   │       ├── PromptPanel.vue
│   │       ├── TaskProgress.vue
│   │       ├── ResultTable.vue
│   │       ├── DirectoryBrowser.vue
│   │       └── TrashPanel.vue
│   └── dist/               # 构建输出
├── data/                   # 数据目录（SQLite 数据库）
├── tests/                  # 测试
├── dockerfile              # Docker 构建文件（多阶段构建）
└── docker-compose.yml      # Docker Compose 配置
```

### 架构分层

| 层 | 目录 | 职责 |
|----|------|------|
| API 路由层 | `app/routers/` | FastAPI Router，HTTP 路由与请求/响应处理 |
| Schema 层 | `app/schemas/` | Pydantic 模型，请求体验证 |
| 服务层 | `app/services/` | 业务逻辑编排 |
| 数据访问层 | `app/services/*_repo.py` | Repository 模式，SQLAlchemy CRUD |
| 模型层 | `app/models.py` | SQLAlchemy ORM 模型定义 |
| 核心层 | `core/` | 配置管理、日志、异常、工具函数 |

## 配置说明

### config.json

```json
{
  "system_settings": {
    "debug_level": "ERROR",
    "secret_key": "your-secret-key",
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "admin_username": "admin",
    "admin_password": "admin",
    "allowed_paths": []
  }
}
```

## Docker 部署

```bash
# 构建并运行
docker-compose up -d

# 或手动构建
docker build -t ai-summary-app:latest .
docker run -d --name ai-summary -p 5000:5000 \
  -v "$(pwd)/config.json:/app/config.json" \
  -v "$(pwd)/data:/app/data" \
  ai-summary-app:latest
```

使用 Uvicorn（ASGI 服务器），内置健康检查。

### 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/config.json` | 配置文件 |
| `/app/data` | 数据目录 |

## 故障排除

**应用无法启动？**
- 检查 Python 版本是否为 3.11+
- 确认 `config.json` 格式正确
- 检查端口 5000 是否被占用

**文件处理失败？**
- 确认 API Key 配置正确
- 检查 Base URL 和网络连接
- 查看日志获取详细错误信息

**Docker 容器启动失败？**
- 查看容器日志: `docker logs <container-name>`

## 许可证

MIT License
