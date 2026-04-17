# AI Summary

基于 Flask + OpenAI API 的智能文本批量处理 Web 应用。扫描目录中的 txt 文件，调用 AI 生成摘要，输出为 md 文件。

## 功能特性

- **AI 提供商管理** - 添加/编辑/删除 AI 服务提供商，支持多模型配置
- **自定义提示词** - 创建和管理 AI 处理模板，作为 system prompt 发送
- **批量文件处理** - 扫描目录批量处理 txt 文件，自动跳过已处理文件
- **实时进度追踪** - 轮询式进度更新，支持取消操作
- **回收站** - 软删除与恢复机制
- **目录浏览** - 内置文件浏览器，支持直接输入路径
- **用户偏好** - 自动保存选择配置

## 技术栈

- **后端**: Flask, OpenAI SDK, Pydantic v2
- **前端**: 原生 HTML/CSS/JS，组件化设计
- **架构**: 分层架构 + Repository 模式
- **容器化**: Docker, Docker Compose, Gunicorn

## 快速开始

### 环境要求

- Python 3.11+
- pip

### 安装

```bash
git clone <repository-url>
cd ai_summary
pip install -r requirements.txt
```

### 配置

编辑 `config.json`，添加 AI 提供商：

```json
{
  "providers": [
    {
      "name": "your-provider",
      "base_url": "https://api.example.com/v1",
      "api_key": "your-api-key",
      "models": {
        "model-name": "model-id"
      }
    }
  ],
  "custom_prompts": {
    "default": "请总结以下内容的要点"
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
| `/api/providers/<name>` | PUT | 更新提供商 |
| `/api/providers/<name>` | DELETE | 删除提供商（移入回收站） |
| `/api/providers/<name>/api-key` | PUT | 更新 API Key |
| `/api/providers/<name>/models` | POST | 添加模型 |
| `/api/providers/<name>/models/<model_name>` | DELETE | 删除模型 |

### 提示词 `/api/prompts`

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/prompts/` | GET | 列出所有提示词 |
| `/api/prompts/` | POST | 创建提示词 |
| `/api/prompts/<name>` | DELETE | 删除提示词（移入回收站） |

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
| `/api/settings/trash/restore/provider/<name>` | POST | 恢复提供商 |
| `/api/settings/trash/restore/prompt/<name>` | POST | 恢复提示词 |
| `/api/settings/trash/provider/<name>` | DELETE | 永久删除提供商 |
| `/api/settings/trash/prompt/<name>` | DELETE | 永久删除提示词 |
| `/api/settings/system` | GET/PUT | 系统设置 |
| `/api/settings/preferences` | GET/PUT | 用户偏好 |

## 项目结构

```
ai_summary/
├── app.py                  # Flask 应用入口
├── run.py                  # 运行脚本
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── core/                   # 核心模块
│   ├── config_manager.py   # 配置管理（单例+线程安全+原子写入）
│   ├── exceptions.py       # 自定义异常层级
│   └── logger.py           # 日志管理
├── models/                 # Pydantic 数据模型
│   └── processing.py       # 处理状态模型
├── repositories/           # 数据访问层（Repository 模式）
│   ├── provider_repo.py    # 提供商 CRUD
│   ├── prompt_repo.py      # 提示词 CRUD
│   └── trash_repo.py       # 回收站 CRUD
├── services/               # 业务服务层
│   ├── processing_service.py  # 文件处理编排
│   ├── state_service.py    # 处理状态管理（线程安全单例）
│   ├── provider_service.py # 提供商服务
│   ├── prompt_service.py   # 提示词服务
│   └── task_service.py     # 任务服务
├── api/                    # API 蓝图层
│   ├── providers.py        # 提供商路由
│   ├── prompts.py          # 提示词路由
│   ├── tasks.py            # 任务路由
│   ├── files.py            # 文件路由
│   ├── settings.py         # 设置路由
│   └── pages.py            # 页面路由
├── frontend/               # 前端资源
│   ├── index.html          # 主页面
│   ├── css/                # 样式
│   │   ├── base.css        # 设计系统变量
│   │   ├── layout.css      # 布局
│   │   ├── components.css  # 组件
│   │   └── processing.css  # 处理面板
│   └── js/                 # 脚本
│       ├── app.js          # 入口+初始化
│       ├── api.js          # API 调用封装
│       ├── state.js        # 前端状态
│       ├── utils.js        # 工具函数
│       └── components/     # UI 组件
│           ├── provider-panel.js
│           ├── prompt-panel.js
│           ├── task-progress.js
│           ├── directory-browser.js
│           ├── trash-panel.js
│           └── result-table.js
├── data/                   # 数据目录
├── output/                 # 输出目录
├── logs/                   # 日志目录
├── tests/                  # 测试
├── dockerfile              # Docker 构建文件
└── docker-compose.yml      # Docker Compose 配置
```

### 架构分层

| 层 | 目录 | 职责 |
|----|------|------|
| API 层 | `api/` | Flask Blueprint，HTTP 路由与请求/响应处理 |
| 服务层 | `services/` | 业务逻辑编排 |
| 数据访问层 | `repositories/` | 对 config.json 的 CRUD 操作 |
| 模型层 | `models/` | Pydantic 数据模型，类型安全验证 |
| 核心层 | `core/` | 配置管理、日志、异常 |

## 配置说明

### config.json

```json
{
  "providers": [
    {
      "name": "提供商名称",
      "base_url": "API Base URL",
      "api_key": "API密钥",
      "models": { "显示名称": "模型ID" }
    }
  ],
  "custom_prompts": { "提示词名称": "提示词内容" },
  "trash": { "custom_prompts": {}, "providers": {} },
  "user_preferences": {
    "selected_provider": "",
    "selected_model": "",
    "selected_prompt": "",
    "directory_path": ""
  },
  "system_settings": {
    "debug_level": "ERROR",
    "flask_secret_key": "your-secret-key",
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
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
  -v "$(pwd)/config.json:/app/config.json:ro" \
  -v "$(pwd)/data:/app/data" \
  ai-summary-app:latest
```

生产环境使用 Gunicorn（2 workers，120s timeout），内置健康检查。

### 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/config.json` | 配置文件（只读） |
| `/app/data` | 数据目录 |
| `/app/output` | 输出目录 |
| `/app/logs` | 日志目录 |

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
