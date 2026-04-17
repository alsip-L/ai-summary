# AI Summary

一个基于 Flask 和 OpenAI API 的智能文本处理 Web 应用，支持批量处理 txt 文件并生成摘要。

## 📋 功能特性

- **AI 提供商管理** - 添加、编辑、删除 AI 服务提供商，支持多个模型
- **自定义提示词** - 创建和管理 AI 处理模板
- **批量文件处理** - 扫描目录批量处理 txt 文件
- **回收站功能** - 软删除与恢复机制
- **目录浏览** - 内置文件浏览器，支持选择处理目录
- **处理状态追踪** - 实时显示处理进度，支持取消操作
- **用户偏好记住** - 自动保存用户的选择配置

## 🛠 技术栈

- **后端**: Flask, OpenAI SDK
- **前端**: HTML5, CSS3, JavaScript
- **配置**: JSON 格式
- **容器化**: Docker, Docker Compose

## 🚀 快速开始

### 环境要求

- Python 3.11+
- pip 包管理器
- Docker (可选，用于容器化部署)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd ai_summary
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置**
   编辑 `config.json` 文件，添加您的 AI 提供商配置：
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

4. **运行应用**
   ```bash
   # Windows
   python run.py
   # 或
   python app.py

   # Linux/macOS
   python3 run.py
   ```

5. **访问应用**
   打开浏览器访问: http://localhost:5000

## 📖 功能详细说明

### AI 提供商管理

在 "AI提供者" 区域可以：

- **添加提供商**: 输入名称、Base URL、API Key 和模型配置
- **编辑提供商**: 修改现有配置
- **删除提供商**: 移至回收站（软删除）
- **管理模型**: 添加或删除提供商下的模型

### 提示词管理

在 "Prompt设置" 区域可以：

- **创建提示词**: 设置名称和内容
- **编辑提示词**: 修改提示词模板
- **删除提示词**: 移至回收站

提示词内容将作为 system prompt 发送给 AI。

### 文件处理

1. 选择包含 txt 文件的目录
2. 选择 AI 提供商和模型
3. 选择提示词模板
4. 点击 "开始处理"
5. 等待处理完成，查看生成的 md 文件

处理过程中可以：
- 查看实时进度
- 取消正在进行的处理
- 查看已处理/失败的文件列表

### 回收站

回收站包含所有被软删除的提供商和提示词。可以：

- **恢复**: 将项目恢复到正常列表
- **永久删除**: 从系统中彻底删除

### 目录浏览

点击目录选择器可以：

- 查看驱动器列表 (Windows)
- 浏览目录结构
- 选择包含待处理文件的目录

## ⚙️ 配置说明

### config.json 结构

```json
{
  "providers": [
    {
      "name": "提供商名称",
      "base_url": "API Base URL",
      "api_key": "API密钥",
      "models": {
        "显示名称": "模型ID"
      }
    }
  ],
  "custom_prompts": {
    "提示词名称": "提示词内容"
  },
  "trash": {
    "custom_prompts": {},
    "providers": {}
  },
  "user_preferences": {
    "selected_provider": "默认提供商",
    "selected_model": "默认模型",
    "selected_prompt": "默认提示词",
    "directory_path": "默认目录"
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

### 系统设置

所有配置均通过 Web 界面或 `config.json` 文件管理，无需设置环境变量。在侧边栏的 **系统设置** 面板中可以修改：

| 配置项 | 说明 | 是否需要重启 |
|--------|------|------------|
| 日志级别 | DEBUG/INFO/WARNING/ERROR/CRITICAL | 即时生效 |
| Flask密钥 | Flask Session 加密密钥 | 需重启 |
| 监听地址 | 服务绑定的IP地址 | 需重启 |
| 监听端口 | 服务端口号 | 需重启 |
| Debug模式 | Flask调试模式 | 需重启 |

## 🌐 Web 界面使用指南

### 主页面布局

```
┌─────────────────────────────────────────┐
│           AI Summary                    │
├─────────────────────────────────────────┤
│ [目录选择] [AI提供者 ▾] [模型 ▾] [Prompt ▾] │
│                                         │
│ [开始处理]  [取消]                      │
├─────────────────────────────────────────┤
│ 状态: 就绪    进度: 0%                  │
│ ░░░░░░░░░░░░░░░░░░░░                   │
├─────────────────────────────────────────┤
│ AI提供者管理 │ Prompt设置 │ 回收站      │
├─────────────────────────────────────────┤
│ (内容区域)                               │
└─────────────────────────────────────────┘
```

### 操作流程

1. **选择目录**: 点击目录选择器，选择包含 txt 文件的文件夹
2. **配置AI**: 从下拉菜单选择提供商、模型和提示词
3. **开始处理**: 点击按钮启动处理任务
4. **查看结果**: 处理完成后在同一目录生成对应的 md 文件

## 🐳 Docker 部署

### 标准部署

1. **构建镜像**
   ```bash
   docker build -t ai-summary-app:latest .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name ai-summary \
     --restart unless-stopped \
     -p 5000:5000 \
     -v "$(pwd)/config.json:/app/config.json:ro" \
     -v "$(pwd)/data:/app/data" \
     -e FLASK_ENV=production \
     ai-summary-app:latest
   ```

3. **使用 Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Alpine Linux 特定部署 (aarch64)

专为 aarch64 架构的 Alpine Linux 系统优化：

```bash
# 构建镜像
./build-alpine.sh

# 运行应用
./run-alpine.sh

# 或使用 docker-compose
docker-compose -f docker-compose.alpine.yml up -d
```

### Docker 环境变量

本项目的所有业务配置（日志级别、密钥、端口等）均通过 `config.json` 管理，可在 Web 界面的系统设置中直接修改，无需使用环境变量。Docker 中仅保留了 Python 运行时优化变量 `PYTHONUNBUFFERED`。

### Docker 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/config.json` | 配置文件（只读） |
| `/app/data` | 数据目录 |
| `/app/output` | 输出目录 |
| `/app/temp` | 临时目录 |

### Docker 健康检查

容器内置健康检查：
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1
```

查看健康状态：
```bash
docker inspect ai-summary --format='{{.State.Health.Status}}'
```

### Docker 备份与恢复

**备份**：
```bash
# 备份配置文件
cp config.json config.json.backup

# 备份数据
tar -czf data-backup.tar.gz data/
```

**恢复**：
```bash
# 恢复配置
cp config.json.backup config.json

# 恢复数据
tar -xzf data-backup.tar.gz
```

## 🔌 API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET/POST | 主页面 |
| `/start_processing` | POST | 启动文件处理 |
| `/get_processing_status` | GET | 获取处理状态 |
| `/cancel_processing` | POST | 取消处理 |
| `/clear_session` | GET | 清理会话 |
| `/get_available_drives` | GET | 获取可用驱动器 |
| `/get_directory_contents` | GET | 获取目录内容 |
| `/view_result` | GET | 查看处理结果 |
| `/save_system_settings` | POST | 保存系统设置 |

## 🔍 故障排除

### 常见问题

**Q: 应用无法启动？**
- 检查 Python 版本是否为 3.11+
- 确认所有依赖已正确安装
- 检查 config.json 格式是否正确

**Q: 文件处理失败？**
- 确认 API Key 配置正确
- 检查目录路径是否存在
- 查看日志获取详细错误信息

**Q: 无法连接到 AI 提供商？**
- 检查网络连接
- 确认 Base URL 正确
- 验证 API Key 有效性

**Q: Docker 容器启动失败？**
- 检查端口 5000 是否被占用
- 确认配置文件存在
- 查看容器日志: `docker logs <container-name>`

### 日志级别设置

通过环境变量设置：
```bash
export DEBUG_LEVEL=DEBUG  # 开发环境
export DEBUG_LEVEL=ERROR   # 生产环境
```

## 📁 项目结构

```
ai_summary/
├── app.py                 # Flask 应用入口（蓝图注册+启动）
├── core/                  # 核心模块
│   ├── __init__.py
│   ├── config_manager.py  # 配置管理器
│   ├── exceptions.py      # 自定义异常
│   └── logger.py          # 日志管理
├── managers/              # 数据管理模块
│   ├── __init__.py
│   ├── file_manager.py    # 文件路径管理
│   ├── model_manager.py   # 大模型管理
│   ├── prompt_manager.py  # 提示词管理
│   └── trash_manager.py   # 回收站管理
├── services/              # 服务层
│   ├── __init__.py
│   ├── file_service.py    # 文件服务
│   ├── prompt_service.py  # 提示词服务
│   ├── provider_service.py # 提供商服务
│   └── state_service.py   # 处理状态服务
├── processors/            # 处理器
│   ├── __init__.py
│   ├── ai_processor.py    # AI 调用与响应处理
│   └── task_processor.py  # 异步任务执行
├── routes/                # 路由层（Flask蓝图）
│   ├── __init__.py
│   ├── main_route.py      # 主页与配置选择
│   ├── processing_route.py # 文件处理路由
│   ├── directory_route.py # 目录浏览路由
│   ├── result_route.py    # 结果查看路由
│   └── settings_route.py  # 系统设置路由
├── helpers/               # 辅助工具
│   ├── __init__.py
│   └── web_helpers.py     # URL解码/会话消息/选择管理
├── docs/                  # 项目文档
│   ├── feature_modules_analysis.md
│   └── project_function_analysis.md
├── static/                # 前端静态资源
│   ├── script.js
│   └── style.css
├── templates/             # HTML 模板
│   ├── index.html
│   └── simple_test.html
├── tests/                 # 测试
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_managers.py
│   ├── test_all_features.py
│   ├── test_comprehensive.py
│   └── test_full_features.py
├── .gitignore             # Git 忽略规则
├── run.py                 # 运行脚本
├── config.json            # 配置文件
├── requirements.txt       # Python 依赖
├── dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── README.md              # 项目说明
└── DOCKER_DEPLOYMENT.md   # Docker 部署文档
```

### 模块说明

- **core/** - 核心功能模块，包括配置管理、日志、异常处理
- **managers/** - 数据管理模块，提供商、提示词、文件路径、回收站的CRUD操作
- **services/** - 服务层，封装业务逻辑，提供对管理器的统一调用接口
- **processors/** - 处理器，执行AI调用和异步文件处理任务
- **routes/** - 路由层，Flask蓝图，按功能域划分的Web路由
- **helpers/** - 辅助工具，URL解码、会话消息、选择管理
- **docs/** - 项目文档
- **static/** - 前端静态资源
- **templates/** - Flask模板文件
- **tests/** - 单元测试和集成测试

## 📄 许可证

MIT License

## 🙏 致谢

- Flask 框架
- OpenAI API
- 所有开源贡献者
