# AI Summary 重构框架推荐方案

## 一、项目现状分析

| 维度 | 当前状态 | 痛点 |
|------|---------|------|
| **后端框架** | Flask + 手动蓝图 | 无依赖注入、无请求校验、无自动文档 |
| **数据层** | 单个 config.json 文件通过 ConfigManager 单例读写 | 无数据库、无事务、无并发安全、读写全量文件 |
| **前端** | 原生 JS + 全局对象 AppState | 无组件化、无构建工具、无类型安全 |
| **任务处理** | threading.Thread | 无任务队列、无持久化、无重试机制 |
| **模型校验** | Pydantic 仅在 Repository 层使用 | API 层无入参校验 |
| **测试** | unittest + 手动 mock | 测试覆盖不完整、集成测试依赖运行中的服务器 |

## 二、推荐方案：FastAPI + Vue 3 + SQLite

### 为什么选这个组合？

1. **FastAPI**：项目已使用 Pydantic，FastAPI 原生集成 Pydantic，迁移成本最低
2. **Vue 3**：渐进式框架，可逐步替换现有 JS，学习曲线平缓
3. **SQLite**：单文件数据库，无需额外部署，但提供真正的 SQL 查询和事务支持

### 对比其他方案

| 方案 | 优势 | 劣势 | 适合度 |
|------|------|------|--------|
| **FastAPI + Vue 3 + SQLite** ✅ | Pydantic 原生集成、自动 OpenAPI 文档、依赖注入、异步支持 | 需要学习 async/await | ⭐⭐⭐⭐⭐ |
| Flask + SQLAlchemy + Vue 3 | 保持 Flask 熟悉度 | Flask 缺少现代特性（DI、自动文档），Pydantic 集成需额外工作 | ⭐⭐⭐ |
| Django + DRF + React | 全栈方案、admin 后台 | 过重、与现有 Pydantic 模型冲突、迁移成本高 | ⭐⭐ |
| FastAPI + React + PostgreSQL | React 生态丰富 | React 学习成本高、PostgreSQL 需额外部署 | ⭐⭐⭐ |

## 三、重构步骤

### 阶段 1：后端核心迁移（Flask → FastAPI）

**目标**：将 Flask 应用迁移到 FastAPI，保持 API 端点兼容

#### 步骤 1.1：项目结构调整
```
ai_summary/
├── app/                    # FastAPI 应用
│   ├── main.py             # FastAPI 入口 + 生命周期
│   ├── dependencies.py     # 依赖注入容器
│   ├── routers/            # 路由（替代 Flask 蓝图）
│   │   ├── providers.py
│   │   ├── prompts.py
│   │   ├── tasks.py
│   │   ├── files.py
│   │   ├── trash.py
│   │   └── settings.py
│   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── provider.py
│   │   ├── prompt.py
│   │   └── task.py
│   └── services/           # 业务逻辑层（保持现有）
├── core/                   # 核心模块（保持现有，逐步简化）
├── frontend/               # 前端（阶段 2 重构）
└── tests/
```

#### 步骤 1.2：引入 FastAPI 依赖注入
- 用 `Depends()` 替代模块级 `_svc = ProviderService()` 实例
- 用 `Annotated[]` 类型注解声明依赖
- 示例：
  ```python
  # dependencies.py
  def get_provider_service() -> ProviderService:
      return ProviderService()

  # routers/providers.py
  @router.get("/")
  def list_providers(svc: ProviderService = Depends(get_provider_service)):
      return svc.list_all()
  ```

#### 步骤 1.3：添加请求/响应 Schema
- 将现有 Pydantic 模型拆分为请求模型（`*Create`、`*Update`）和响应模型（`*Response`）
- 利用 FastAPI 自动校验和文档生成
- 示例：
  ```python
  # schemas/provider.py
  class ProviderCreate(BaseModel):
      name: str
      base_url: str
      api_key: str
      models: dict[str, str] = {}

  class ProviderResponse(BaseModel):
      name: str
      base_url: str
      models: dict[str, str]
  ```

#### 步骤 1.4：统一错误处理
- 用 FastAPI 的 `HTTPException` + exception handler 替代 Flask 的 `@app.errorhandler`
- 保持 `{"success": false, "error": "..."}` 响应格式兼容前端

#### 步骤 1.5：更新 requirements.txt
```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0
openai>=1.12.0
```

**验证**：所有现有 API 端点在 FastAPI 下行为一致，前端无需改动

---

### 阶段 2：数据层迁移（config.json → SQLite）

**目标**：用 SQLite + SQLAlchemy 替代 JSON 文件存储

#### 步骤 2.1：定义 ORM 模型
```python
# models/db.py
class Provider(Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    base_url: Mapped[str]
    api_key: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    models: Mapped[str] = mapped_column(Text)  # JSON 序列化

class Prompt(Base):
    __tablename__ = "prompts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    content: Mapped[str]
```

#### 步骤 2.2：重写 Repository 层
- 每个 Repository 注入 `Session` 而非 `ConfigManager`
- 通过 FastAPI 依赖注入管理数据库会话生命周期
- 示例：
  ```python
  # dependencies.py
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()

  # repositories/provider.py
  class ProviderRepository:
      def __init__(self, db: Session):
          self._db = db

      def get(self, name: str) -> Provider | None:
          return self._db.query(Provider).filter(Provider.name == name).first()
  ```

#### 步骤 2.3：数据迁移脚本
- 编写一次性脚本，将 config.json 数据导入 SQLite
- 保留 config.json 仅用于系统设置（host、port、debug_level 等）

#### 步骤 2.4：保留 ConfigManager 仅管理应用配置
- `ConfigManager` 职责缩减为只管 `system_settings`
- 业务数据（providers、prompts、trash）全部走数据库

**验证**：所有 CRUD 操作通过数据库完成，数据持久化可靠

---

### 阶段 2.5：数据库 Web 管理界面

**目标**：在网页上直接查看和管理 SQLite 数据库内容

#### 方案对比

| 方案 | 说明 | 优势 | 劣势 |
|------|------|------|------|
| **SQLAdmin** ✅ | FastAPI 生态的 Admin 面板（类似 Django Admin） | 与 FastAPI + SQLAlchemy 深度集成、零前端代码、支持 CRUD + 搜索 + 筛选 | 界面风格固定 |
| sqlite-web | 独立的 SQLite Web 浏览器 | 轻量、独立部署 | 与应用无关、需单独启动 |
| 自建管理页面 | 在 Vue 前端中开发管理模块 | 完全自定义 | 开发量大 |

#### 推荐方案：SQLAdmin

SQLAdmin 是 FastAPI 生态中最成熟的 Admin 面板，类似 Django Admin 的体验：

**集成步骤**：

1. 安装依赖：
   ```
   sqladmin>=0.20.0
   ```

2. 注册 Admin 模型：
   ```python
   # app/admin.py
   from sqladmin import ModelView

   class ProviderAdmin(ModelView, model=Provider):
       column_list = [Provider.id, Provider.name, Provider.base_url, Provider.is_active]
       column_searchable_list = [Provider.name]
       form_excluded_columns = [Provider.id]
       can_export = True

   class PromptAdmin(ModelView, model=Prompt):
       column_list = [Prompt.id, Prompt.name]
       column_searchable_list = [Prompt.name]
       can_export = True

   class TrashProviderAdmin(ModelView, model=TrashProvider):
       column_list = [TrashProvider.id, TrashProvider.name, TrashProvider.original_id]
       can_delete = True
       can_edit = False
       can_create = False
   ```

3. 挂载到 FastAPI：
   ```python
   # app/main.py
   from sqladmin import Admin
   from sqladmin.authentication import AuthenticationBackend
   from app.admin import ProviderAdmin, PromptAdmin, TrashProviderAdmin

   class AdminAuth(AuthenticationBackend):
       async def login(self, request):
           # 简单密码验证，或复用系统设置中的 secret_key
           form = await request.form()
           if form.get("username") == "admin" and form.get("password") == "admin":
               request.session.update({"authenticated": True})
               return True
           return False

       async def logout(self, request):
           request.session.clear()
           return True

       async def authenticate(self, request):
           return request.session.get("authenticated")

   admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key="your-secret"))
   admin.add_view(ProviderAdmin)
   admin.add_view(PromptAdmin)
   admin.add_view(TrashProviderAdmin)
   ```

4. 访问方式：
   - 浏览器打开 `http://localhost:5000/admin/`
   - 登录后即可查看、搜索、编辑、导出所有数据库表

**功能一览**：
- 📋 表格浏览：分页查看每张表的所有记录
- 🔍 搜索筛选：按字段搜索和筛选
- ✏️ 增删改查：直接在网页上编辑数据
- 📤 数据导出：支持 CSV/JSON 导出
- 🔐 登录保护：需要密码才能访问

---

### 阶段 3：前端重构（原生 JS → Vue 3）

**目标**：用 Vue 3 组件化替代现有原生 JS

#### 步骤 3.1：引入 Vue 3 + Vite
```bash
npm create vite@latest frontend-vue -- --template vue
```

#### 步骤 3.2：组件映射
| 现有 JS 文件 | Vue 组件 |
|-------------|---------|
| `provider-panel.js` | `ProviderPanel.vue` |
| `prompt-panel.js` | `PromptPanel.vue` |
| `task-progress.js` | `TaskProgress.vue` |
| `directory-browser.js` | `DirectoryBrowser.vue` |
| `trash-panel.js` | `TrashPanel.vue` |
| `result-table.js` | `ResultTable.vue` |
| `state.js` | Pinia store |
| `api.js` | `composables/useApi.ts` |

#### 步骤 3.3：状态管理（Pinia）
- 用 Pinia 替代全局 `AppState` 对象
- 按领域拆分 store：`useProviderStore`、`usePromptStore`、`useTaskStore`

#### 步骤 3.4：API 层
- 用 `fetch` 或 `axios` 封装 composable
- 利用 FastAPI 自动生成的 OpenAPI spec 可选引入 OpenAPI Generator

**验证**：前端功能与重构前完全一致，UI 无回退

---

### 阶段 4：任务处理优化

**目标**：用更健壮的任务处理替代 threading.Thread

#### 步骤 4.1：引入任务队列（可选方案）

**轻量方案（推荐）**：使用 `asyncio` + `BackgroundTasks`（FastAPI 内置）
- 适合当前规模（单用户、批量文件处理）
- 无需额外基础设施

**中量方案**：使用 `arq`（基于 Redis 的轻量任务队列）
- 支持重试、超时、进度追踪
- 需要引入 Redis

**重量方案**：使用 Celery
- 功能最全，但对当前项目过重

#### 步骤 4.2：任务状态持久化
- 将 `ProcessingState` 从内存单例改为数据库记录
- 支持服务重启后恢复任务状态

**验证**：任务启动/取消/状态查询功能正常

---

### 阶段 5：测试与部署更新

#### 步骤 5.1：更新测试
- 用 `pytest` + `httpx.AsyncClient` 替代 `unittest` + `requests`
- 利用 FastAPI 的 `TestClient` 进行同步测试
- 集成测试不再需要运行中的服务器

#### 步骤 5.2：更新部署配置
- Dockerfile：`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]`
- docker-compose.yml：移除 gunicorn，改用 uvicorn

**验证**：Docker 构建和部署正常

---

## 四、迁移优先级与风险

| 阶段 | 优先级 | 风险 | 回滚策略 |
|------|--------|------|---------|
| 阶段 1：Flask → FastAPI | 🔴 高 | 低（API 兼容） | 保留 Flask 代码，切回即可 |
| 阶段 2：JSON → SQLite | 🔴 高 | 中（数据迁移） | 保留 ConfigManager，双写过渡 |
| 阶段 2.5：SQLAdmin 管理面板 | 🟡 中 | 低（独立模块） | 移除 admin 挂载即可 |
| 阶段 3：JS → Vue 3 | 🟡 中 | 中（前端重写） | 保留旧前端，Nginx 路由切换 |
| 阶段 4：任务优化 | 🟢 低 | 低 | 保留 threading 方案 |
| 阶段 5：测试/部署 | 🟡 中 | 低 | 保留旧配置 |

## 五、总结

**推荐组合**：**FastAPI + Vue 3 + SQLite**

核心理由：
1. **FastAPI** 与现有 Pydantic 模型天然兼容，迁移成本最低
2. **SQLite** 是最简单的"真正的数据库"，无需额外部署
3. **Vue 3** 渐进式特性允许逐步替换，不必一次性重写前端
4. 三个技术都是各自领域的主流选择，社区活跃、文档完善

建议按阶段 1 → 2 → 3 → 4 → 5 的顺序执行，每个阶段完成后验证再进入下一阶段，确保随时可回滚。
