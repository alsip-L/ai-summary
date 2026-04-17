# AI Summary 项目重构计划

> 本文档供另一个 AI 执行重构时使用。包含完整的现状分析、目标架构、逐文件映射关系、分步执行计划和验证标准。

---

## 一、项目现状

### 1.1 技术栈

- Python 3.11+ / Flask 2.3+ / OpenAI SDK 1.12+
- 前端：原生 HTML + CSS + JavaScript（无框架）
- 存储：config.json（既是配置又是数据）
- 部署：Docker + Gunicorn

### 1.2 当前目录结构

```
ai_summary/
├── app.py                          # Flask 入口，注册蓝图
├── run.py                          # 启动脚本
├── config.json                     # 运行时配置+数据持久化
├── requirements.txt                # Flask, openai, gunicorn
├── core/
│   ├── config_manager.py           # 配置管理器（单例，线程安全，201行）
│   ├── logger.py                   # 日志管理（48行）
│   └── exceptions.py               # 异常类（30行）
├── managers/
│   ├── model_manager.py            # 提供商管理（88行，含 ModelConfig 数据类）
│   ├── prompt_manager.py           # 提示词管理（76行）
│   ├── file_manager.py             # 文件路径管理（163行）
│   └── trash_manager.py            # 回收站管理（158行）
├── processors/
│   ├── ai_processor.py             # AI 单文件处理（67行）
│   └── task_processor.py           # 批量任务编排（99行）
├── services/
│   └── state_service.py            # 处理状态管理（276行，单例）
├── routes/
│   ├── main_route.py               # 主页路由（256行，10+表单分支）
│   ├── processing_route.py         # 处理任务路由（57行）
│   ├── directory_route.py          # 目录浏览路由（65行）
│   ├── result_route.py             # 结果查看路由（51行）
│   └── settings_route.py           # 系统设置路由（67行）
├── helpers/
│   └── web_helpers.py              # Web 辅助函数（57行）
├── templates/
│   └── index.html                  # 主页面模板（380行）
├── static/
│   ├── script.js                   # 前端 JS（2176行）
│   └── style.css                   # 前端 CSS（2078行）
└── tests/                          # 5个测试文件
```

### 1.3 核心问题

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| 1 | **上帝路由** | `routes/main_route.py` 256行，10+表单分支 | AI 修改一个功能需理解整个文件 |
| 2 | **前端单文件过大** | `static/script.js` 2176行 | AI 上下文窗口无法完整理解 |
| 3 | **CSS 单文件过大** | `static/style.css` 2078行 | 同上 |
| 4 | **无类型约束** | managers 层用 dict 传递数据 | AI 无法推断接口契约 |
| 5 | **前后端耦合** | Jinja2 渲染 + form POST + session | AI 无法独立修改前后端 |
| 6 | **Manager 职责混杂** | managers 既做数据访问又做业务逻辑 | 不符合单一职责 |
| 7 | **file_manager.py 未被使用** | 163行代码无调用方 | 死代码 |

---

## 二、目标架构

### 2.1 目录结构

```
ai_summary/
├── app.py                          # Flask 应用工厂（仅注册蓝图+中间件）
├── run.py                          # 启动脚本（保留）
│
├── core/                           # 基础设施层（保留，微调）
│   ├── __init__.py
│   ├── config.py                   # 重命名自 config_manager.py，接口不变
│   ├── log.py                      # 重命名自 logger.py，接口不变
│   └── errors.py                   # 重命名自 exceptions.py，接口不变
│
├── models/                         # 【新增】数据模型层
│   ├── __init__.py
│   ├── provider.py                 # ProviderConfig, ModelVariant
│   ├── prompt.py                   # PromptConfig
│   ├── task.py                     # TaskStatus, TaskResult, ProcessingStatus
│   └── settings.py                 # UserPreferences, SystemSettings
│
├── repositories/                   # 【新增】数据访问层（从 managers 迁移）
│   ├── __init__.py
│   ├── provider_repo.py            # 提供商 CRUD
│   ├── prompt_repo.py              # 提示词 CRUD
│   └── trash_repo.py               # 回收站 CRUD
│
├── services/                       # 业务逻辑层（重组）
│   ├── __init__.py
│   ├── processing_service.py       # 合并 ai_processor + task_processor
│   └── state_service.py            # 保留，微调类型
│
├── api/                            # 【新增】RESTful API 层（替代 routes/）
│   ├── __init__.py
│   ├── providers.py                # /api/providers
│   ├── prompts.py                  # /api/prompts
│   ├── tasks.py                    # /api/tasks
│   ├── files.py                    # /api/files
│   ├── settings.py                 # /api/settings
│   └── pages.py                    # 页面路由（渲染 index.html）
│
├── frontend/                       # 【新增】前端独立目录
│   ├── index.html                  # 纯静态 HTML（无 Jinja2）
│   ├── js/
│   │   ├── app.js                  # 入口+初始化（~50行）
│   │   ├── api.js                  # API 客户端封装（~100行）
│   │   ├── state.js                # 前端状态管理（~80行）
│   │   ├── components/
│   │   │   ├── provider-panel.js   # 提供商配置面板（~200行）
│   │   │   ├── prompt-panel.js     # 提示词面板（~150行）
│   │   │   ├── task-progress.js    # 任务进度（~200行）
│   │   │   ├── directory-browser.js # 目录浏览器（~200行）
│   │   │   ├── trash-panel.js      # 回收站（~100行）
│   │   │   ├── settings-panel.js   # 系统设置（~100行）
│   │   │   └── result-table.js     # 结果表格（~80行）
│   │   └── utils.js                # 工具函数（~60行）
│   └── css/
│       ├── base.css                # CSS 变量 + 重置（~100行）
│       ├── layout.css              # 布局（~200行）
│       ├── components.css          # 组件样式（~800行）
│       └── themes.css              # 亮/暗主题（~200行）
│
├── config.json                     # 保留
├── requirements.txt                # 新增 pydantic 依赖
├── dockerfile                      # 更新静态文件路径
└── docker-compose.yml              # 保留
```

### 2.2 删除的文件/目录

| 删除项 | 原因 |
|--------|------|
| `managers/` 整个目录 | 迁移到 `repositories/` + `models/` |
| `processors/` 整个目录 | 合并到 `services/processing_service.py` |
| `routes/` 整个目录 | 迁移到 `api/` |
| `helpers/` 整个目录 | `safe_url_decode`/`safe_url_decode_form` 在 RESTful JSON API 模式下不再需要（JSON 请求体无需 URL 编码）；`set_session_message` 在无 session 模式下不再需要；`SelectionManager` 迁移到前端 `state.js` |
| `templates/` 整个目录 | 迁移到 `frontend/index.html`（纯静态） |
| `static/` 整个目录 | 迁移到 `frontend/js/` + `frontend/css/` |
| `managers/file_manager.py` | 死代码，无调用方 |

---

## 三、逐文件详细设计

### 3.1 models/ — 数据模型层

#### models/provider.py

```python
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    """AI 提供商配置"""
    name: str
    base_url: str
    api_key: str = Field(repr=False)
    models: dict[str, str] = Field(default_factory=dict)   # {display_name: model_id}
    is_active: bool = True
```

**迁移来源**：`managers/model_manager.py` 中的 `ModelConfig` 数据类

**映射关系**：
- `ModelConfig.name` → `ProviderConfig.name`
- `ModelConfig.base_url` → `ProviderConfig.base_url`
- `ModelConfig.api_key` → `ProviderConfig.api_key`
- `ModelConfig.models` → `ProviderConfig.models`
- `ModelConfig.is_active` → `ProviderConfig.is_active`

#### models/prompt.py

```python
from pydantic import BaseModel

class PromptConfig(BaseModel):
    """提示词配置"""
    name: str
    content: str
```

#### models/task.py

```python
from pydantic import BaseModel, Field
from enum import Enum

class TaskStatus(str, Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class TaskResult(BaseModel):
    """单个文件的处理结果"""
    source: str
    output: str | None = None
    error: str | None = None

class ProcessingStatus(BaseModel):
    """处理状态快照（只读视图）"""
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    total_files: int = 0
    processed_files_count: int = 0
    current_file: str = ""
    results: list[TaskResult] = Field(default_factory=list)
    error: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    cancelled: bool = False
```

**迁移来源**：`services/state_service.py` 中的 `ProcessingStatus` 数据类

#### models/settings.py

```python
from pydantic import BaseModel

class UserPreferences(BaseModel):
    """用户偏好"""
    selected_provider: str = ""
    selected_model: str = ""
    selected_prompt: str = ""
    directory_path: str = ""

class SystemSettings(BaseModel):
    """系统设置"""
    debug_level: str = "ERROR"
    flask_secret_key: str = "default-dev-secret-key-please-change-in-prod"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
```

---

### 3.2 repositories/ — 数据访问层

#### repositories/provider_repo.py

```python
from models.provider import ProviderConfig
from core.config import ConfigManager

class ProviderRepository:
    def __init__(self, config: ConfigManager):
        self._config = config

    def get_all(self) -> dict[str, ProviderConfig]:
        """获取所有活跃提供商"""
        providers = self._config.get("providers", [])
        return {
            p["name"]: ProviderConfig(**p)
            for p in providers
            if p.get("is_active", True)
        }

    def get_all_as_dict(self) -> dict[str, dict]:
        """获取所有活跃提供商（dict 格式，用于 API 响应）"""
        providers = self._config.get("providers", [])
        return {
            p["name"]: p
            for p in providers
            if p.get("is_active", True)
        }

    def get(self, name: str) -> ProviderConfig | None:
        return self.get_all().get(name)

    def save(self, provider: ProviderConfig) -> bool:
        providers = self._config.get("providers", [])
        for i, p in enumerate(providers):
            if p["name"] == provider.name:
                providers[i] = provider.model_dump()
                break
        else:
            providers.append(provider.model_dump())
        return self._config.set("providers", providers)

    def update_api_key(self, name: str, api_key: str) -> bool:
        provider = self.get(name)
        if not provider:
            return False
        provider.api_key = api_key
        return self.save(provider)

    def add_model_variant(self, provider_name: str, display_name: str, model_id: str) -> bool:
        provider = self.get(provider_name)
        if not provider:
            return False
        provider.models[display_name] = model_id
        return self.save(provider)

    def delete_model(self, provider_name: str, model_name: str) -> bool:
        provider = self.get(provider_name)
        if not provider or model_name not in provider.models:
            return False
        del provider.models[model_name]
        return self.save(provider)

    def delete(self, name: str) -> bool:
        """从活跃列表中移除提供商（不移入回收站）"""
        providers = self._config.get("providers", [])
        new_providers = [p for p in providers if p.get("name") != name]
        if len(new_providers) == len(providers):
            return False
        return self._config.set("providers", new_providers)
```

**迁移来源**：`managers/model_manager.py` 的 `ModelManager` 类

**方法映射**：
| ModelManager 方法 | ProviderRepository 方法 |
|---|---|
| `get_all()` | `get_all()` |
| `get_all_as_dict()` | `get_all_as_dict()` |
| `get(name)` | `get(name)` |
| `save(model)` | `save(provider)` |
| `update_api_key(name, key)` | `update_api_key(name, key)` |
| `add_model_variant(p, k, id)` | `add_model_variant(p, k, id)` |
| `delete_model(p, m)` | `delete_model(p, m)` |
| `delete(name)` | `delete(name)` |

#### repositories/prompt_repo.py

```python
from models.prompt import PromptConfig
from core.config import ConfigManager
from core.errors import ValidationError
from core.log import get_logger

logger = get_logger()

class PromptRepository:
    def __init__(self, config: ConfigManager):
        self._config = config

    def get_all(self) -> dict[str, PromptConfig]:
        prompts = self._config.get("custom_prompts", {})
        processed = {}
        for name, content in prompts.items():
            value = "\n".join(content) if isinstance(content, list) else content
            processed[name] = PromptConfig(name=name, content=value)
        return processed

    def get(self, name: str) -> PromptConfig | None:
        return self.get_all().get(name)

    def save(self, prompt: PromptConfig) -> bool:
        if not prompt.name or not prompt.name.strip():
            raise ValidationError("提示词名称不能为空")
        if not prompt.content:
            raise ValidationError("提示词内容不能为空")
        try:
            prompts = self._config.get("custom_prompts", {})
            is_new = prompt.name not in prompts
            prompts[prompt.name] = prompt.content
            self._config.set("custom_prompts", prompts)
            if is_new and len(prompts) == 1:
                self._config.set("current_prompt", prompt.name)
            return True
        except Exception as e:
            logger.error(f"保存提示词失败: {prompt.name}, {e}")
            return False

    def delete(self, name: str) -> bool:
        try:
            prompts = self._config.get("custom_prompts", {})
            if name not in prompts:
                return False
            del prompts[name]
            self._config.set("custom_prompts", prompts)
            current = self._config.get("current_prompt", "")
            if current == name:
                self._config.set("current_prompt", list(prompts.keys())[0] if prompts else "")
            return True
        except Exception as e:
            logger.error(f"删除提示词失败: {name}, {e}")
            return False
```

**迁移来源**：`managers/prompt_manager.py` 的 `PromptManager` 类

#### repositories/trash_repo.py

```python
from models.provider import ProviderConfig
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()

class TrashRepository:
    def __init__(self, config: ConfigManager):
        self._config = config
        self._provider_repo = ProviderRepository(config)
        self._prompt_repo = PromptRepository(config)

    def get_all(self) -> dict:
        return self._config.get("trash", {})

    def move_provider_to_trash(self, name: str) -> bool:
        try:
            provider = self._provider_repo.get(name)
            if not provider:
                return False
            # 从活跃列表删除（通过 ProviderRepository 封装）
            if not self._provider_repo.delete(name):
                return False
            # 移入回收站
            trash = self.get_all()
            trash.setdefault("providers", {})[name] = provider.model_dump()
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"移动提供商到回收站失败: {name}, {e}")
            return False

    def move_prompt_to_trash(self, name: str) -> bool:
        try:
            prompt = self._prompt_repo.get(name)
            if not prompt:
                return False
            if not self._prompt_repo.delete(name):
                return False
            trash = self.get_all()
            trash.setdefault("custom_prompts", {})[name] = prompt.content
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"移动提示词到回收站失败: {name}, {e}")
            return False

    def restore_provider(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False
            provider_data = trash_providers[name]
            provider = ProviderConfig(**provider_data)
            if not self._provider_repo.save(provider):
                return False
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"恢复提供商失败: {name}, {e}")
            return False

    def restore_prompt(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False
            content = trash_prompts[name]
            from models.prompt import PromptConfig
            if not self._prompt_repo.save(PromptConfig(name=name, content=content)):
                return False
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"恢复提示词失败: {name}, {e}")
            return False

    def permanent_delete_provider(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"永久删除提供商失败: {name}, {e}")
            return False

    def permanent_delete_prompt(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"永久删除提示词失败: {name}, {e}")
            return False
```

**迁移来源**：`managers/trash_manager.py` 的 `TrashManager` 类

---

### 3.3 services/ — 业务逻辑层

#### services/processing_service.py

```python
import os
from openai import OpenAI
from models.provider import ProviderConfig
from models.task import TaskResult
from services.state_service import ProcessingState
from core.log import get_logger
from core.errors import FileProcessingError, ProviderError

logger = get_logger()

class ProcessingService:
    """AI 文件处理服务 — 合并原 ai_processor.py + task_processor.py"""

    def __init__(self, state: ProcessingState):
        self._state = state

    # ---- 单文件处理（原 AIProcessor.process_file + save_response）----

    @staticmethod
    def read_file(file_path: str) -> str:
        for encoding in ["utf-8", "gbk"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise FileProcessingError(f"无法解码文件: {os.path.basename(file_path)}")

    @staticmethod
    def call_ai(client: OpenAI, content: str, system_prompt: str, model_id: str) -> str:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                stream=False,
            )
            if not completion or not completion.choices:
                raise ProviderError("API 返回空响应")
            return completion.choices[0].message.content
        except (FileProcessingError, ProviderError):
            raise
        except Exception as e:
            raise ProviderError(f"AI 调用失败: {str(e).splitlines()[0]}")

    @staticmethod
    def save_response(file_path: str, response: str) -> str:
        md_path = os.path.splitext(file_path)[0] + ".md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(response)
            return md_path
        except Exception as e:
            raise FileProcessingError(f"保存结果失败: {e}")

    def process_file(self, file_path: str, client: OpenAI, prompt: str, model_id: str) -> TaskResult:
        try:
            content = self.read_file(file_path)
            response = self.call_ai(client, content, prompt, model_id)
            output_path = self.save_response(file_path, response)
            return TaskResult(source=file_path, output=output_path)
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return TaskResult(source=file_path, error=str(e))

    # ---- 批量处理（原 task_processor.run_processing_task）----

    @staticmethod
    def scan_txt_files(directory: str) -> list[str]:
        if not os.path.isdir(directory):
            raise ValueError(f"目录不存在: {directory}")
        txt_files = []
        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith(".txt"):
                    txt_files.append(os.path.join(root, f))
        return txt_files

    def run_batch(self, directory: str, client: OpenAI, prompt: str, model_id: str) -> None:
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            txt_files = self.scan_txt_files(directory)
            if not txt_files:
                raise ValueError("未找到 txt 文件")

            self._state.start_processing(len(txt_files))

            for i, file_path in enumerate(txt_files):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                self._state.update_progress(i, os.path.basename(file_path))
                result = self.process_file(file_path, client, prompt, model_id)
                progress = int(((i + 1) / len(txt_files)) * 100)
                self._state.update_progress(i + 1, None, progress)
                self._state.add_result(result.source, result.output, result.error)

            self._state.complete()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e).splitlines()[0]}")
```

**迁移来源**：`processors/ai_processor.py` + `processors/task_processor.py`

**方法映射**：
| 原位置 | 新位置 |
|--------|--------|
| `AIProcessor.process_file()` | `ProcessingService.process_file()` |
| `AIProcessor.save_response()` | `ProcessingService.save_response()` |
| `run_processing_task()` | `ProcessingService.run_batch()` |

#### services/state_service.py

保留现有 `ProcessingState` 类，仅做以下微调：
1. 将内部 `ProcessingStatus` 数据类替换为 `models.task.ProcessingStatus`（Pydantic 模型，注意：此类名与原 dataclass 同名，替换后 import 路径从 `services.state_service` 改为 `models.task`）
2. `add_result()` 方法参数改为接受 `TaskResult` 对象
3. 其余接口不变

---

### 3.4 api/ — RESTful API 层

#### api/providers.py

```python
from flask import Blueprint, request, jsonify
from repositories.provider_repo import ProviderRepository
from repositories.trash_repo import TrashRepository
from models.provider import ProviderConfig
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()
provider_bp = Blueprint("api_providers", __name__, url_prefix="/api/providers")

def _repo() -> ProviderRepository:
    return ProviderRepository(ConfigManager())

@provider_bp.get("/")
def list_providers():
    """GET /api/providers/"""
    return jsonify(_repo().get_all_as_dict())

@provider_bp.post("/")
def create_provider():
    """POST /api/providers/ — 创建提供商"""
    data = request.get_json()
    try:
        provider = ProviderConfig(**data)
        if _repo().save(provider):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "保存失败"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@provider_bp.put("/<name>")
def update_provider(name: str):
    """PUT /api/providers/<name>"""
    data = request.get_json()
    data["name"] = name
    try:
        provider = ProviderConfig(**data)
        if _repo().save(provider):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "更新失败"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@provider_bp.delete("/<name>")
def delete_provider(name: str):
    """DELETE /api/providers/<name> — 移入回收站"""
    trash_repo = TrashRepository(ConfigManager())
    if trash_repo.move_provider_to_trash(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400

@provider_bp.put("/<name>/api-key")
def update_api_key(name: str):
    """PUT /api/providers/<name>/api-key"""
    api_key = request.get_json().get("api_key", "")
    if _repo().update_api_key(name, api_key):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "更新失败"}), 400

@provider_bp.post("/<name>/models")
def add_model(name: str):
    """POST /api/providers/<name>/models"""
    data = request.get_json()
    if _repo().add_model_variant(name, data.get("display_name", ""), data.get("model_id", "")):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "添加失败"}), 400

@provider_bp.delete("/<name>/models/<model_name>")
def delete_model(name: str, model_name: str):
    """DELETE /api/providers/<name>/models/<model_name>"""
    if _repo().delete_model(name, model_name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400
```

**迁移来源**：`routes/main_route.py` 中 `form_type == 'save_provider_form'`、`'delete_provider_form'`、`'save_api_key_form'`、`'add_model_form'`、`'delete_model_form'` 分支

#### api/prompts.py

```python
from flask import Blueprint, request, jsonify
from repositories.prompt_repo import PromptRepository
from repositories.trash_repo import TrashRepository
from core.config import ConfigManager

prompt_bp = Blueprint("api_prompts", __name__, url_prefix="/api/prompts")

def _repo() -> PromptRepository:
    return PromptRepository(ConfigManager())

@prompt_bp.get("/")
def list_prompts():
    """GET /api/prompts/"""
    prompts = _repo().get_all()
    # 将 PromptConfig 对象转为 {name: content} 的 dict 格式返回
    return jsonify({name: p.content for name, p in prompts.items()})

@prompt_bp.post("/")
def create_prompt():
    """POST /api/prompts/"""
    data = request.get_json()
    from models.prompt import PromptConfig
    prompt = PromptConfig(name=data.get("name", ""), content=data.get("content", ""))
    if _repo().save(prompt):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "保存失败"}), 400

@prompt_bp.delete("/<name>")
def delete_prompt(name: str):
    """DELETE /api/prompts/<name> — 移入回收站"""
    trash_repo = TrashRepository(ConfigManager())
    if trash_repo.move_prompt_to_trash(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400
```

**迁移来源**：`routes/main_route.py` 中 `form_type == 'save_prompt_form'`、`'delete_prompt_form'` 分支

#### api/tasks.py

```python
import threading
from flask import Blueprint, request, jsonify
from openai import OpenAI
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from services.processing_service import ProcessingService
from services.state_service import ProcessingState
from core.config import ConfigManager

task_bp = Blueprint("api_tasks", __name__, url_prefix="/api/tasks")

@task_bp.post("/start")
def start_task():
    """POST /api/tasks/start"""
    data = request.get_json()
    provider_name = data.get("provider", "")
    model_key = data.get("model", "")
    api_key = data.get("api_key", "")
    prompt_name = data.get("prompt", "")
    directory = data.get("directory", "")

    if not api_key:
        return jsonify({"success": False, "error": "API Key 未配置"}), 400

    # 验证目录
    import os
    if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
        return jsonify({"success": False, "error": "请提供有效的目录路径"}), 400

    config = ConfigManager()
    provider_repo = ProviderRepository(config)
    prompt_repo = PromptRepository(config)

    # 验证提供商
    provider = provider_repo.get(provider_name)
    if not provider:
        return jsonify({"success": False, "error": f"提供商 '{provider_name}' 未找到"}), 400

    # 验证模型
    if model_key not in provider.models:
        return jsonify({"success": False, "error": f"模型 '{model_key}' 未找到"}), 400
    model_id = provider.models[model_key]

    # 验证提示词
    prompt = prompt_repo.get(prompt_name)
    if not prompt:
        return jsonify({"success": False, "error": f"Prompt '{prompt_name}' 未找到"}), 400
    prompt_content = prompt.content

    # 启动后台线程
    client = OpenAI(api_key=api_key, base_url=provider.base_url)
    state = ProcessingState()
    service = ProcessingService(state)

    thread = threading.Thread(
        target=service.run_batch,
        args=(directory, client, prompt_content, model_id),
        daemon=True,
    )
    thread.start()

    return jsonify({"success": True, "message": "处理已启动"})

@task_bp.get("/status")
def get_status():
    """GET /api/tasks/status"""
    state = ProcessingState()
    return jsonify(state.get_dict())

@task_bp.post("/cancel")
def cancel_task():
    """POST /api/tasks/cancel"""
    state = ProcessingState()
    state_dict = state.get_dict()
    if state_dict["status"] not in ["processing", "scanning", "started", "idle"]:
        return jsonify({"success": False, "error": "当前没有正在进行的处理任务"}), 400
    state.set_cancelled()
    if state.is_running():
        state.cancel()
    return jsonify({"success": True, "message": "处理已取消"})
```

**迁移来源**：`routes/processing_route.py`

**API 映射**：
| 原端点 | 新端点 |
|--------|--------|
| `POST /start_processing` (form) | `POST /api/tasks/start` (JSON) |
| `GET /get_processing_status` | `GET /api/tasks/status` |
| `POST /cancel_processing` | `POST /api/tasks/cancel` |

#### api/files.py

```python
import sys
import os
from flask import Blueprint, request, jsonify
from core.log import get_logger

logger = get_logger()
file_bp = Blueprint("api_files", __name__, url_prefix="/api/files")

@file_bp.get("/drives")
def get_drives():
    """GET /api/files/drives"""
    try:
        drives = []
        if sys.platform == "win32":
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>= 1
        else:
            drives.append("/")
        return jsonify({"success": True, "drives": drives})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@file_bp.get("/directory")
def get_directory():
    """GET /api/files/directory?path=xxx"""
    path = request.args.get("path", "")
    if not path:
        return get_drives()
    if not os.path.exists(path) or not os.path.isdir(path):
        return jsonify({"success": False, "error": "路径不存在"}), 400

    parent = os.path.dirname(path)
    if sys.platform == "win32" and parent == "":
        parent = None
    elif parent == path:
        parent = None

    directories = []
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and not item.startswith("."):
                directories.append({"name": item, "path": item_path})
    except PermissionError:
        pass

    directories.sort(key=lambda x: x["name"].lower())
    return jsonify({"success": True, "path": path, "parent": parent, "directories": directories})

@file_bp.get("/result")
def view_result():
    """GET /api/files/result?path=xxx"""
    file_path = request.args.get("path", "")
    if not file_path:
        return jsonify({"error": "未提供文件路径"}), 400

    real_path = os.path.realpath(file_path)
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        return jsonify({"error": "文件不存在"}), 404
    if not real_path.endswith((".md", ".txt")):
        return jsonify({"error": "不支持的文件类型"}), 400

    for encoding in ["utf-8", "gbk"]:
        try:
            with open(real_path, "r", encoding=encoding) as f:
                content = f.read()
            return jsonify({
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(real_path),
                "content": content,
            })
        except UnicodeDecodeError:
            continue
    return jsonify({"error": "文件读取失败"}), 500
```

**迁移来源**：`routes/directory_route.py` + `routes/result_route.py`

**API 映射**：
| 原端点 | 新端点 |
|--------|--------|
| `GET /get_available_drives` | `GET /api/files/drives` |
| `GET /get_directory_contents` | `GET /api/files/directory` |
| `GET /view_result` | `GET /api/files/result` |

#### api/settings.py

```python
from flask import Blueprint, request, jsonify
from repositories.trash_repo import TrashRepository
from core.config import ConfigManager
from core.log import get_logger, update_log_level

logger = get_logger()
settings_bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")

@settings_bp.get("/trash")
def get_trash():
    """GET /api/settings/trash"""
    return jsonify(TrashRepository(ConfigManager()).get_all())

@settings_bp.post("/trash/restore/provider/<name>")
def restore_provider(name: str):
    if TrashRepository(ConfigManager()).restore_provider(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "恢复失败"}), 400

@settings_bp.post("/trash/restore/prompt/<name>")
def restore_prompt(name: str):
    if TrashRepository(ConfigManager()).restore_prompt(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "恢复失败"}), 400

@settings_bp.delete("/trash/provider/<name>")
def permanent_delete_provider(name: str):
    if TrashRepository(ConfigManager()).permanent_delete_provider(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400

@settings_bp.delete("/trash/prompt/<name>")
def permanent_delete_prompt(name: str):
    if TrashRepository(ConfigManager()).permanent_delete_prompt(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400

@settings_bp.put("/system")
def save_system_settings():
    """PUT /api/settings/system"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400

        config = ConfigManager()
        current = config.get("system_settings", {})

        old_debug_level = current.get("debug_level", "ERROR")
        old_host = current.get("host", "0.0.0.0")
        old_port = current.get("port", 5000)
        old_secret = current.get("flask_secret_key", "")
        old_debug = current.get("debug", False)

        if "debug_level" in data:
            current["debug_level"] = data["debug_level"].upper()
        if "flask_secret_key" in data and data["flask_secret_key"].strip():
            current["flask_secret_key"] = data["flask_secret_key"].strip()
        if "host" in data:
            current["host"] = data["host"].strip()
        if "port" in data:
            try:
                current["port"] = int(data["port"])
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "端口必须为数字"}), 400
        if "debug" in data:
            current["debug"] = bool(data["debug"])

        if config.set("system_settings", current):
            if current.get("debug_level") != old_debug_level:
                update_log_level(current["debug_level"])

            needs_restart = (
                current.get("host") != old_host
                or current.get("port") != old_port
                or current.get("flask_secret_key") != old_secret
                or current.get("debug") != old_debug
            )
            return jsonify({"success": True, "needs_restart": needs_restart})
        return jsonify({"success": False, "error": "保存失败"}), 500
    except Exception as e:
        logger.error(f"保存系统设置失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@settings_bp.get("/preferences")
def get_preferences():
    """GET /api/settings/preferences"""
    return jsonify(ConfigManager().get("user_preferences", {}))

@settings_bp.put("/preferences")
def save_preferences():
    """PUT /api/settings/preferences"""
    data = request.get_json()
    config = ConfigManager()
    current = config.get("user_preferences", {})
    current.update(data)
    if config.set("user_preferences", current):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "保存失败"}), 400
```

**迁移来源**：`routes/settings_route.py` + `routes/main_route.py` 中回收站相关分支 + 用户偏好保存逻辑

**API 映射**：
| 原端点/逻辑 | 新端点 |
|-------------|--------|
| `POST /save_system_settings` | `PUT /api/settings/system` |
| `form_type == 'restore_provider_form'` | `POST /api/settings/trash/restore/provider/<name>` |
| `form_type == 'restore_prompt_form'` | `POST /api/settings/trash/restore/prompt/<name>` |
| `form_type == 'permanent_delete_provider_form'` | `DELETE /api/settings/trash/provider/<name>` |
| `form_type == 'permanent_delete_prompt_form'` | `DELETE /api/settings/trash/prompt/<name>` |
| `_save_user_preferences()` | `PUT /api/settings/preferences` |
| `_load_user_preferences()` | `GET /api/settings/preferences` |

#### api/pages.py

```python
from flask import Blueprint, send_from_directory
import os

page_bp = Blueprint("pages", __name__)

@page_bp.route("/")
def index():
    """渲染主页面"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    return send_from_directory(frontend_dir, "index.html")
```

---

### 3.5 app.py — 应用工厂

```python
import sys
import codecs

# Windows 控制台 UTF-8 设置（保留）
if sys.platform == "win32":
    try:
        import locale
        locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
    except Exception:
        pass

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except Exception:
        pass

from flask import Flask
from core.config import ConfigManager

app = Flask(__name__, static_folder="frontend", static_url_path="/static")
app.secret_key = ConfigManager().get("system_settings.flask_secret_key", "default-dev-secret-key-please-change-in-prod")

# 注册 API 蓝图
from api.providers import provider_bp
from api.prompts import prompt_bp
from api.tasks import task_bp
from api.files import file_bp
from api.settings import settings_bp
from api.pages import page_bp

app.register_blueprint(provider_bp)
app.register_blueprint(prompt_bp)
app.register_blueprint(task_bp)
app.register_blueprint(file_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(page_bp)

if __name__ == "__main__":
    settings = ConfigManager().get("system_settings", {})
    debug_level = settings.get("debug_level", "ERROR").upper()
    host = settings.get("host", "0.0.0.0")
    port = settings.get("port", 5000)
    debug = settings.get("debug", False) or debug_level == "DEBUG"
    app.run(debug=debug, host=host, port=port)
```

---

### 3.6 frontend/ — 前端

#### frontend/js/api.js — 统一 API 客户端

```javascript
// 统一请求封装：处理 HTTP 错误和网络异常
async function request(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        const error = new Error(data.error || data.message || `HTTP ${response.status}`);
        error.status = response.status;
        error.data = data;
        throw error;
    }
    return data;
}

const API = {
    // 提供商
    providers: {
        list: () => request("/api/providers/"),
        create: (data) => request("/api/providers/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        update: (name, data) => request(`/api/providers/${encodeURIComponent(name)}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        delete: (name) => request(`/api/providers/${encodeURIComponent(name)}`, { method: "DELETE" }),
        updateApiKey: (name, apiKey) => request(`/api/providers/${encodeURIComponent(name)}/api-key`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify({api_key: apiKey}) }),
        addModel: (name, data) => request(`/api/providers/${encodeURIComponent(name)}/models`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        deleteModel: (name, modelName) => request(`/api/providers/${encodeURIComponent(name)}/models/${encodeURIComponent(modelName)}`, { method: "DELETE" }),
    },

    // 提示词
    prompts: {
        list: () => request("/api/prompts/"),
        create: (data) => request("/api/prompts/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        delete: (name) => request(`/api/prompts/${encodeURIComponent(name)}`, { method: "DELETE" }),
    },

    // 任务
    tasks: {
        start: (data) => request("/api/tasks/start", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        status: () => request("/api/tasks/status"),
        cancel: () => request("/api/tasks/cancel", { method: "POST" }),
    },

    // 文件
    files: {
        drives: () => request("/api/files/drives"),
        directory: (path) => request(`/api/files/directory?path=${encodeURIComponent(path)}`),
        result: (path) => request(`/api/files/result?path=${encodeURIComponent(path)}`),
    },

    // 设置
    settings: {
        getTrash: () => request("/api/settings/trash"),
        restoreProvider: (name) => request(`/api/settings/trash/restore/provider/${encodeURIComponent(name)}`, { method: "POST" }),
        restorePrompt: (name) => request(`/api/settings/trash/restore/prompt/${encodeURIComponent(name)}`, { method: "POST" }),
        permanentDeleteProvider: (name) => request(`/api/settings/trash/provider/${encodeURIComponent(name)}`, { method: "DELETE" }),
        permanentDeletePrompt: (name) => request(`/api/settings/trash/prompt/${encodeURIComponent(name)}`, { method: "DELETE" }),
        saveSystem: (data) => request("/api/settings/system", { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
        getPreferences: () => request("/api/settings/preferences"),
        savePreferences: (data) => request("/api/settings/preferences", { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) }),
    },
};
```

#### frontend/js/state.js — 前端状态管理

```javascript
const AppState = {
    selectedProvider: "",
    selectedModel: "",
    selectedPrompt: "",
    directoryPath: "",
    apiKey: "",

    async load() {
        const prefs = await API.settings.getPreferences();
        this.selectedProvider = prefs.selected_provider || "";
        this.selectedModel = prefs.selected_model || "";
        this.selectedPrompt = prefs.selected_prompt || "";
        this.directoryPath = prefs.directory_path || "";
    },

    async save() {
        await API.settings.savePreferences({
            selected_provider: this.selectedProvider,
            selected_model: this.selectedModel,
            selected_prompt: this.selectedPrompt,
            directory_path: this.directoryPath,
        });
    },
};
```

#### frontend/index.html

将 `templates/index.html` 转为纯静态 HTML：
1. 移除所有 Jinja2 语法（`{{ }}`、`{% %}`）
2. 移除服务端渲染的数据，改为页面加载时通过 `API` 获取
3. 引用拆分后的 JS/CSS 文件

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI批量总结助手</title>
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/layout.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/themes.css">
</head>
<body>
    <div class="container">
        <div class="sidebar" id="sidebar">
            <!-- 由 JS 动态渲染 -->
        </div>
        <div class="main-content" id="main-content">
            <!-- 由 JS 动态渲染 -->
        </div>
    </div>

    <div id="directory-browser-modal" class="modal-overlay" style="display: none;">
        <!-- 目录浏览器模态框 -->
    </div>

    <script src="/static/js/utils.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/state.js"></script>
    <script src="/static/js/components/provider-panel.js"></script>
    <script src="/static/js/components/prompt-panel.js"></script>
    <script src="/static/js/components/task-progress.js"></script>
    <script src="/static/js/components/directory-browser.js"></script>
    <script src="/static/js/components/trash-panel.js"></script>
    <script src="/static/js/components/settings-panel.js"></script>
    <script src="/static/js/components/result-table.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

#### 前端 JS 组件拆分指引

从 `static/script.js`（2176行）拆分到各组件文件，按功能域划分：

| 组件文件 | 负责的 UI 区域 | 对应原 script.js 中的大致内容 |
|----------|---------------|------------------------------|
| `provider-panel.js` | 提供商下拉框、模型下拉框、API Key 输入、新增/删除提供商和模型 | `selectProvider()`, `deleteProvider()`, `handleProviderAddNew()`, `selectModel()`, `deleteModel()`, `handleModelAddNew()`, `saveApiKey()` |
| `prompt-panel.js` | 提示词下拉框、内容查看、新增/删除提示词 | `selectPrompt()`, `deletePrompt()`, `handlePromptAddNew()` |
| `task-progress.js` | 开始处理按钮、进度条、状态轮询、取消按钮 | `startProcessing()`, `updateProcessingStatus()`, `cancelProcessing()`, 进度条渲染逻辑 |
| `directory-browser.js` | 目录浏览器模态框 | `openDirectoryBrowser()`, `closeDirectoryBrowser()`, `goBack()`, `refreshDirectory()`, `selectDirectory()`, `goToDirectPath()` |
| `trash-panel.js` | 回收站面板 | `restoreProvider()`, `permanentDeleteProvider()`, `restorePrompt()`, `permanentDeletePrompt()` |
| `settings-panel.js` | 系统设置面板、主题切换 | `saveSystemSettings()`, `toggleTheme()` |
| `result-table.js` | 处理结果表格 | 结果表格渲染逻辑 |
| `utils.js` | 工具函数 | `Utils` 类（debounce, escapeHtml, formatBytes, formatDuration） |

#### CSS 拆分指引

从 `static/style.css`（2078行）拆分：

| 文件 | 内容 |
|------|------|
| `base.css` | CSS 变量定义、reset 样式、通用字体/颜色 |
| `layout.css` | `.container`、`.sidebar`、`.main-content` 布局、响应式断点 |
| `components.css` | 所有组件样式：按钮、表单、下拉框、进度条、模态框、表格、alert |
| `themes.css` | `[data-theme="dark"]` 下的覆盖样式 |

---

## 四、分步执行计划

### Phase 1：后端数据层重构（无破坏性变更）

**目标**：新增 `models/` 和 `repositories/`，与旧代码并存，不删除任何旧文件。

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1.1 | 在 `requirements.txt` 中添加 `pydantic>=2.0.0` | `pip install -r requirements.txt` 成功 |
| 1.2 | 创建 `models/` 目录及 4 个模型文件 | `python -c "from models.provider import ProviderConfig; print(ProviderConfig(name='test', base_url='http://x', api_key='k'))"` 成功 |
| 1.3 | 创建 `repositories/` 目录及 3 个 repo 文件 | `python -c "from repositories.provider_repo import ProviderRepository; print('ok')"` 成功 |
| 1.4 | 在 `repositories/` 中编写单元测试，验证与 `managers/` 行为一致 | 对比 `ModelManager` 和 `ProviderRepository` 的输出一致 |

### Phase 2：后端 Service 层重构

| 步骤 | 操作 | 验证 |
|------|------|------|
| 2.1 | 创建 `services/processing_service.py`，合并 `ai_processor.py` + `task_processor.py` | 单元测试通过 |
| 2.2 | 微调 `services/state_service.py`，使用 `models.task.ProcessingStatus` | 现有测试通过 |

### Phase 3：后端 API 层重构

| 步骤 | 操作 | 验证 |
|------|------|------|
| 3.1 | 创建 `api/` 目录及 6 个 API 文件 | 所有蓝图可注册 |
| 3.2 | 更新 `app.py`，注册新蓝图，保留旧蓝图（双轨运行） | 旧端点仍可访问 |
| 3.3 | 用 curl/Postman 测试所有新 API 端点 | 每个端点返回正确 JSON |
| 3.4 | 确认新 API 行为与旧路由一致后，移除旧 `routes/` 注册 | 旧端点 404，新端点正常 |

### Phase 4：前端重构

| 步骤 | 操作 | 验证 |
|------|------|------|
| 4.1 | 创建 `frontend/` 目录结构 | 目录存在 |
| 4.2 | 编写 `frontend/js/api.js` | 浏览器控制台可调用 `API.providers.list()` |
| 4.3 | 编写 `frontend/js/state.js` | 状态加载/保存正常 |
| 4.4 | 将 `static/script.js` 拆分到 `frontend/js/components/` 各文件 | 每个文件 < 300 行 |
| 4.5 | 将 `static/style.css` 拆分到 `frontend/css/` 各文件 | 每个文件 < 300 行 |
| 4.6 | 将 `templates/index.html` 转为 `frontend/index.html`，移除 Jinja2 | 页面可正常加载 |
| 4.7 | 更新 `app.py` 的 `static_folder` 指向 `frontend/` | 静态资源可访问 |
| 4.8 | 端到端测试：完整走一遍"选择配置→开始处理→查看结果"流程 | 功能正常 |

### Phase 5：清理

| 步骤 | 操作 | 验证 |
|------|------|------|
| 5.1 | 删除 `managers/` 目录 | 无 import 引用 |
| 5.2 | 删除 `processors/` 目录 | 无 import 引用 |
| 5.3 | 删除 `routes/` 目录 | 无 import 引用 |
| 5.4 | 删除 `helpers/` 目录 | 无 import 引用 |
| 5.5 | 删除 `templates/` 目录 | 无引用 |
| 5.6 | 删除 `static/` 目录 | 无引用 |
| 5.7 | 更新 `dockerfile` 中的静态文件路径 | Docker 构建成功 |
| 5.8 | 运行全部测试 | 全部通过 |

---

## 五、API 端点完整对照表

| 原端点 | 方法 | 新端点 | 方法 | 请求格式变化 |
|--------|------|--------|------|-------------|
| `/` (config_selection_form) | POST | `/api/settings/preferences` | PUT | form → JSON |
| `/` (save_provider_form) | POST | `/api/providers/` | POST | form → JSON |
| `/` (save_prompt_form) | POST | `/api/prompts/` | POST | form → JSON |
| `/` (save_api_key_form) | POST | `/api/providers/<name>/api-key` | PUT | form → JSON |
| `/` (add_model_form) | POST | `/api/providers/<name>/models` | POST | form → JSON |
| `/` (delete_model_form) | POST | `/api/providers/<name>/models/<model>` | DELETE | form → 无 body |
| `/` (delete_provider_form) | POST | `/api/providers/<name>` | DELETE | form → 无 body |
| `/` (delete_prompt_form) | POST | `/api/prompts/<name>` | DELETE | form → 无 body |
| `/` (restore_provider_form) | POST | `/api/settings/trash/restore/provider/<name>` | POST | form → 无 body |
| `/` (restore_prompt_form) | POST | `/api/settings/trash/restore/prompt/<name>` | POST | form → 无 body |
| `/` (permanent_delete_provider_form) | POST | `/api/settings/trash/provider/<name>` | DELETE | form → 无 body |
| `/` (permanent_delete_prompt_form) | POST | `/api/settings/trash/prompt/<name>` | DELETE | form → 无 body |
| `/start_processing` | POST | `/api/tasks/start` | POST | form → JSON |
| `/get_processing_status` | GET | `/api/tasks/status` | GET | 无变化 |
| `/cancel_processing` | POST | `/api/tasks/cancel` | POST | 无变化 |
| `/get_available_drives` | GET | `/api/files/drives` | GET | 无变化 |
| `/get_directory_contents` | GET | `/api/files/directory` | GET | query param 不变 |
| `/view_result` | GET | `/api/files/result` | GET | query param 不变 |
| `/save_system_settings` | POST | `/api/settings/system` | PUT | JSON 不变 |
| `/clear_session` | GET | 删除 | — | 不再需要 session |

---

## 六、core/ 层重命名映射

| 原文件 | 新文件 | 注意事项 |
|--------|--------|---------|
| `core/config_manager.py` | `core/config.py` | 类名保持 `ConfigManager`，所有 import 路径从 `core.config_manager` 改为 `core.config` |
| `core/logger.py` | `core/log.py` | 类名保持 `get_logger`/`update_log_level`，import 路径从 `core.logger` 改为 `core.log`。避免与标准库 `logging` 同名冲突 |
| `core/exceptions.py` | `core/errors.py` | 类名保持不变，import 路径从 `core.exceptions` 改为 `core.errors` |

---

## 七、验证标准

每个 Phase 完成后必须满足：

1. **功能等价**：所有用户可见行为与重构前一致
2. **无死代码**：无未使用的 import、函数、文件
3. **文件大小**：每个 Python 文件 < 300 行，每个 JS 文件 < 300 行，每个 CSS 文件 < 300 行
4. **类型完整**：所有 `models/` 中的 Pydantic 模型覆盖所有传递的数据结构
5. **API 一致**：前端通过 `api.js` 统一调用，无直接 `fetch` 散落
6. **Docker 可构建**：`docker build .` 成功

---

## 八、对 AI 编程友好的设计原则总结

| 原则 | 具体做法 | 效果 |
|------|---------|------|
| 单文件 < 300 行 | 拆分上帝路由、巨型 JS/CSS | AI 上下文窗口可完整理解一个文件 |
| 每个文件单一职责 | 一个 API 文件只管一个资源 | AI 修改一个功能只需改 1-2 个文件 |
| Pydantic 类型定义 | 所有数据结构有模型类 | AI 看到模型就知道字段和类型 |
| RESTful API | 前后端通过 HTTP+JSON 通信 | AI 可独立修改前后端任一端 |
| Repository 隔离存储 | Service 不关心数据存在哪 | AI 改业务逻辑不需要理解存储实现 |
| 前端组件化 | 每个 UI 区域一个 JS 文件 | AI 修改 UI 组件不影响其他组件 |
| API 客户端封装 | `api.js` 统一所有后端调用 | 改接口只需改一处 |
| Service 无框架依赖 | 业务逻辑不 import Flask | AI 写业务逻辑不需要理解框架生命周期 |
