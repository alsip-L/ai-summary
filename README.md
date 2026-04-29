# AI Summary

基于 FastAPI + OpenAI API 的智能文本批量处理 Web 应用。扫描目录中的 txt 文件，调用 AI 生成摘要，输出为 md 文件。

## 功能特性

- **AI 提供商管理** - 添加/编辑/删除 AI 服务提供商，支持多模型配置
- **自定义提示词** - 创建和管理 AI 处理模板，作为 system prompt 发送
- **批量文件处理** - 扫描目录批量处理 txt 文件，支持跳过已处理文件
- **流式 AI 输出** - 调用 OpenAI 兼容 API 流式生成，实时推送 token
- **实时进度追踪** - 轮询式进度更新，支持取消操作
- **实时日志面板** - WebSocket 推送日志，前端实时展示处理过程
- **回收站** - 软删除与恢复机制
- **目录浏览** - 内置文件浏览器，支持直接输入路径
- **用户偏好** - 自动保存选择配置
- **管理后台** - SQLAdmin 数据库管理界面（`/admin`）
- **增强 API 文档** - OpenAPI 规范增强，含标签分组、字段描述、示例和通用错误响应
- **Python SDK** - 类型安全的同步/异步客户端，含重试机制和异常层次
- **一键启动** - Windows `start.bat` / Linux `start.sh` 脚本

## 技术栈

- **后端**: FastAPI, SQLAlchemy 2.0, Pydantic v2, OpenAI SDK, Uvicorn
- **前端**: Vue 3, Pinia, Vite
- **数据库**: SQLite
- **管理后台**: SQLAdmin
- **架构**: 分层架构（Router → Schema → Service → Repository → Model）
- **SDK**: httpx, Pydantic v2, 指数退避重试
- **容器化**: Docker, Docker Compose

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+ (前端构建)
- pip

### 方式一：一键启动

```bash
# Windows
start.bat

# Linux/macOS (Docker)
./start.sh
```

脚本会自动检查环境、安装依赖、构建前端并启动应用。

### 方式二：手动安装

```bash
git clone <repository-url>
cd ai_summary

# 创建配置文件
cp config.example.json config.json

pip install -r requirements.txt

# 构建前端
cd frontend-vue
npm install
npm run build
cd ..
```

### 配置

编辑 `config.json`，配置系统设置（首次使用已从 `config.example.json` 复制）：

```json
{
  "system_settings": {
    "debug_level": "INFO",
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
4. **查看进度** - 实时进度条和日志面板展示处理过程
5. **查看结果** - 处理完成后在原目录生成对应的 md 文件

## API 路由

交互式 API 文档：`/api/docs`（Swagger UI）| `/api/redoc`（ReDoc）

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
| `/api/tasks/failed` | GET | 获取失败记录 |
| `/api/tasks/failed` | DELETE | 清除失败记录 |
| `/api/tasks/retry` | POST | 重试失败记录 |

### 文件 `/api/files`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/files/drives` | GET | 获取可用驱动器（Windows） |
| `/api/files/directory` | GET | 获取目录内容（?path=xxx） |
| `/api/files/result` | GET | 查看处理结果（?path=xxx） |

### 回收站 `/api/settings/trash`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/settings/trash/` | GET | 获取回收站内容 |
| `/api/settings/trash/restore/provider/{name}` | POST | 恢复提供商 |
| `/api/settings/trash/restore/prompt/{name}` | POST | 恢复提示词 |
| `/api/settings/trash/provider/{name}` | DELETE | 永久删除提供商 |
| `/api/settings/trash/prompt/{name}` | DELETE | 永久删除提示词 |

### 设置 `/api/settings`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/settings/preferences` | GET | 获取用户偏好 |
| `/api/settings/preferences` | PUT | 更新用户偏好 |

### 日志 `/api/logs`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/logs/status` | GET | 获取日志状态 |
| `/api/logs/ws` | WebSocket | 实时日志推送 |

### 系统 `/api/system`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/system/info` | GET | 获取系统信息 |
| `/api/system/rebuild-frontend` | POST | 重建前端 |

## Python SDK

项目内置 Python SDK 客户端（`sdk/`），提供类型安全的 API 调用接口。

### 安装

```bash
pip install ai-summary-sdk
```

### 同步客户端

```python
from ai_summary_sdk import AISummaryClient

with AISummaryClient(base_url="http://localhost:5000") as client:
    # 提供商管理
    providers = client.providers.list()
    client.providers.create(name="openai", base_url="https://api.openai.com/v1",
                            api_key="sk-xxx", models_map={"GPT-4": "gpt-4"})

    # 提示词管理
    client.prompts.create(name="摘要生成", content="请对以下文本生成摘要。")

    # 任务处理
    client.tasks.start(provider="openai", model="gpt-4", api_key="sk-xxx",
                       prompt="摘要生成", directory="C:/data/texts")
    status = client.tasks.status()
```

### 异步客户端

```python
import asyncio
from ai_summary_sdk import AsyncAISummaryClient

async def main():
    async with AsyncAISummaryClient(base_url="http://localhost:5000") as client:
        providers = await client.providers.list()
        status = await client.tasks.status()

asyncio.run(main())
```

### 异常层次

| 异常 | 说明 |
|------|------|
| `AISummarySDKError` | SDK 基础异常 |
| `ConnectionError` | 服务不可达或网络异常 |
| `AuthenticationError` | API Key 无效或缺失 |
| `ValidationError` | 请求参数不合法 |
| `APIError` | 服务端返回非 2xx 状态码 |
| `NotFoundError` | 资源不存在 (HTTP 404) |

SDK 对可重试错误（HTTP 503、网络超时）自动进行指数退避重试。

## 项目结构

```
ai_summary/
├── run.py                  # 应用入口脚本
├── config.example.json   # 配置模板（首次使用需复制为 config.json）
├── requirements.txt        # Python 依赖
├── start.bat               # Windows 一键启动脚本
├── start.sh                # Linux/macOS Docker 启动脚本
├── core/                   # 核心模块
│   ├── config.py           # 配置管理（单例+线程安全+原子写入）
│   ├── errors.py           # 自定义异常层级
│   ├── log.py              # 日志管理（含 WebSocket 日志推送）
│   └── utils.py            # 工具函数（多编码文件读取）
├── app/                    # FastAPI 应用主包
│   ├── main.py             # FastAPI 应用创建与配置
│   ├── database.py         # SQLAlchemy 数据库配置（SQLite）
│   ├── dependencies.py     # FastAPI 依赖注入
│   ├── models.py           # SQLAlchemy ORM 模型
│   ├── admin.py            # SQLAdmin 管理后台视图
│   ├── openapi_config.py   # OpenAPI 规范增强配置
│   ├── routers/            # API 路由层
│   │   ├── providers.py    # 提供商 CRUD 路由
│   │   ├── prompts.py      # 提示词 CRUD 路由
│   │   ├── tasks.py        # 任务处理路由
│   │   ├── files.py        # 文件浏览路由
│   │   ├── trash.py        # 回收站路由
│   │   ├── settings.py     # 设置/偏好路由
│   │   ├── logs.py         # 日志 WebSocket 路由
│   │   └── system.py       # 系统信息路由
│   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── common.py       # 通用响应模型（SuccessResponse/ErrorResponse）
│   │   ├── provider.py     # Provider 相关 Schema
│   │   ├── prompt.py       # Prompt 相关 Schema
│   │   ├── settings.py     # Settings 相关 Schema
│   │   └── task.py         # Task 相关 Schema
│   ├── services/           # 业务服务层
│   │   ├── provider_service.py  # 提供商业务逻辑
│   │   ├── prompt_service.py    # 提示词业务逻辑
│   │   ├── task_service.py      # 任务处理服务
│   │   ├── task_runner.py       # 任务运行器
│   │   ├── ai_client.py         # AI 客户端（OpenAI API 调用）
│   │   ├── file_processor.py    # 文件处理器
│   │   ├── processing_state.py  # 处理状态管理
│   │   ├── trash_service.py     # 回收站业务逻辑
│   │   ├── settings_service.py  # 设置/偏好业务逻辑
│   │   ├── file_browser_service.py  # 文件浏览服务
│   │   └── failed_record_service.py # 失败记录服务
│   └── repositories/       # 数据访问层（Repository 模式）
│       ├── provider_repo.py     # 提供商数据访问
│       ├── prompt_repo.py       # 提示词数据访问
│       ├── trash_repo.py        # 回收站数据访问
│       ├── settings_repo.py     # 设置数据访问
│       └── failed_record_repo.py # 失败记录数据访问
├── sdk/                    # Python SDK 客户端
│   ├── ai_summary_sdk/     # SDK 包
│   │   ├── client.py       # 同步客户端
│   │   ├── async_client.py # 异步客户端
│   │   ├── models.py       # 数据模型
│   │   ├── exceptions.py   # 异常类
│   │   ├── _base.py        # 基础客户端
│   │   └── _retry.py       # 重试逻辑
│   ├── tests/              # SDK 测试
│   ├── build_sdk.py        # 构建脚本
│   └── pyproject.toml      # 项目配置
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
│   │       ├── TrashPanel.vue
│   │       └── LogPanel.vue
│   └── dist/               # 构建输出
├── data/                   # 数据目录（SQLite 数据库）
├── tests/                  # 测试
│   ├── test_core.py        # 核心模块测试
│   ├── test_repositories.py # Repository 层测试
│   ├── test_services.py    # Service 层测试
│   ├── test_integration.py # API 集成测试
│   ├── test_ai_client.py   # AI 客户端测试
│   ├── test_file_processor.py # 文件处理器测试
│   ├── test_processing_state.py # 处理状态测试
│   ├── test_task_runner.py # 任务运行器测试
│   ├── test_retry.py       # 重试机制测试
│   ├── test_failed_record_service.py # 失败记录服务测试
│   └── test_settings_repo.py # 设置 Repository 测试
├── logs/                   # 日志输出目录
├── output/                 # 处理结果输出目录
├── dockerfile              # Docker 构建文件（三阶段构建）
└── docker-compose.yml      # Docker Compose 配置
```

### 架构分层

| 层 | 目录 | 职责 |
|----|------|------|
| API 路由层 | `app/routers/` | FastAPI Router，HTTP 路由与请求/响应处理 |
| Schema 层 | `app/schemas/` | Pydantic 模型，请求体验证与字段描述 |
| 服务层 | `app/services/` | 业务逻辑编排 |
| 数据访问层 | `app/repositories/` | Repository 模式，SQLAlchemy CRUD |
| 模型层 | `app/models.py` | SQLAlchemy ORM 模型定义 |
| 核心层 | `core/` | 配置管理、日志、异常、工具函数 |

### 异常层次

```
AISummaryException (基类)
├── RetryableError (可重试基类)
│   ├── NetworkError (网络错误)
│   └── RateLimitError (限流错误)
├── ProviderError (提供商错误)
├── FileProcessingError (文件处理错误)
└── ValidationError (验证错误)
```

## 配置说明

### config.json

基于 `config.example.json` 创建，包含以下配置项：

| 字段 | 默认值 | 说明 |
| `debug_level` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR），修改即时生效 |
| `secret_key` | - | 应用密钥，生产环境请更换 |
| `host` | `0.0.0.0` | 监听地址，修改需重启 |
| `port` | `5000` | 监听端口，修改需重启 |
| `debug` | `false` | 调试模式（开启 Uvicorn reload），修改需重启 |

```json
{
  "system_settings": {
    "debug_level": "INFO",
    "secret_key": "your-secret-key",
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  }
}
```

## Docker 部署

```bash
# 首次部署：创建配置文件
cp config.example.json config.json
# 编辑 config.json 填入实际密钥和凭据

# 构建并运行
docker-compose up -d

# 或手动构建
docker build -t ai-summary-app:latest .
docker run -d --name ai-summary -p 5000:5000 \
  -v "$(pwd)/config.json:/app/config.json" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/output:/app/output" \
  --restart unless-stopped \
  ai-summary-app:latest
```

三阶段构建：前端在 `node:20-slim` 中构建，Python 依赖在 `python:3.11-alpine` 中预编译，运行使用 `python:3.11-alpine`，内置 Uvicorn + 健康检查。

### 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/config.json` | 配置文件 |
| `/app/data` | 数据目录（SQLite 数据库） |
| `/app/logs` | 日志输出目录 |
| `/app/output` | 处理结果输出目录 |

### 配置管理

所有配置通过 `config.json` 管理（首次使用需从 `config.example.json` 复制），无需环境变量。修改日志级别即时生效，修改端口/地址需重启容器：

```bash
docker restart ai-summary
```

### 常用命令

```bash
docker logs -f ai-summary          # 查看日志
docker restart ai-summary           # 重启
docker exec -it ai-summary /bin/bash  # 进入容器调试
docker inspect ai-summary --format='{{.State.Health.Status}}'  # 健康检查
```

## 故障排除

**应用无法启动？**
- 检查 Python 版本是否为 3.11+
- 确认 `config.json` 存在且格式正确（首次使用需 `cp config.example.json config.json`）
- 检查端口 5000 是否被占用

**前端页面空白？**
- 确认已构建前端：`cd frontend-vue && npm install && npm run build`
- 检查 `frontend-vue/dist/` 目录是否存在

**文件处理失败？**
- 确认 API Key 配置正确
- 检查 Base URL 和网络连接
- 查看日志面板获取详细错误信息

**Docker 容器启动失败？**
- 查看容器日志: `docker logs <container-name>`
- 端口被占用: `netstat -tulpn | grep :5000`，或更换端口 `-p 8080:5000`
- 构建失败: `docker build --no-cache -t ai-summary-app .`

## 许可证

MIT License
