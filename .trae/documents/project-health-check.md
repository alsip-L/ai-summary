# 全面转为新架构计划

## 目标

将项目完全切换到新架构（FastAPI + Vue 3 + SQLite），删除所有遗留 Flask 代码和旧前端，修复新前端中的已知问题，确保项目可正常运行。

## 当前状态

- **新后端** (`app/`): FastAPI + SQLAlchemy + SQLite — 已完成，可正常工作
- **新前端** (`frontend-vue/`): Vue 3 + Pinia + Vite — 已完成，有若干 bug
- **遗留 Flask 代码** (`app.py` + `features/`): 仍在项目中，但不再被使用
- **旧前端** (`frontend/`): 原生 JS，FastAPI 通过 StaticFiles 提供服务
- **测试** (`tests/`): 仍引用旧 Flask 架构的 `features.*` 模块
- **启动脚本** (`start.bat`, `start.sh`): 仍检查 Flask 依赖

## 实施步骤

### 步骤 1：删除遗留 Flask 代码

删除以下文件/目录：
- `app.py` — Flask 应用入口
- `features/` — 整个旧 Flask 功能模块目录

### 步骤 2：删除旧前端

删除 `frontend/` 目录（原生 JS 前端），因为 `frontend-vue/` 已完全替代它。

### 步骤 3：修改 FastAPI 应用以服务 Vue 前端

当前 `app/main.py` 挂载 `frontend/` 目录为静态文件并提供 `frontend/index.html`。需要：
- 修改静态文件挂载，指向 `frontend-vue/dist/`（构建产物）
- 或者在开发模式下通过 Vite dev server 代理

### 步骤 4：修复 Vue 前端已知问题

#### 4.1 App.vue 双 script 块问题
`App.vue` 有两个 `<script>` 块：
- `<script setup>` 中使用了 `reactive`, `provide`, `onMounted` 但未导入
- 第二个 `<script>` 块导入了这些但用 `export default`

修复：合并为单个 `<script setup>` 块，在顶部导入所有依赖。

#### 4.2 TrashPanel.vue totalCount getter 问题
`trash.js` store 中 `totalCount` 使用了 `get` 语法，但在 Pinia setup store 中应使用 `computed`。

修复：将 `get totalCount()` 改为 `computed(() => ...)`。

#### 4.3 DirectoryBrowser.vue 未被 App.vue 引用
`DirectoryBrowser.vue` 通过 `defineExpose({ open })` 暴露 `open` 方法，但 `App.vue` 中没有 ref 引用来调用它。"浏览"按钮的 `@click="$emit('open-directory')"` 事件也没有被处理。

修复：在 App.vue 中添加 ref 引用 DirectoryBrowser，处理 open-directory 事件。

#### 4.4 ResultTable.vue 与 App.vue 的 v-if 重复
`App.vue` 中 `<ResultTable v-if="taskStore.results.length > 0" />`，而 `ResultTable.vue` 内部也有 `v-if="taskStore.results.length > 0"`。双重判断不影响功能但冗余。

修复：移除 ResultTable.vue 内部的 v-if（由 App.vue 控制）。

### 步骤 5：更新启动脚本和部署配置

- `start.bat` — 更新依赖检查（不再检查 Flask），添加 Vue 前端构建步骤
- `start.sh` — 同上
- `dockerfile` — 添加 Node.js 构建步骤，构建 Vue 前端
- `docker-compose.yml` — 无需大改

### 步骤 6：更新测试

当前测试引用旧 `features.*` 模块，需要重写为使用新 `app.*` 模块：
- `test_core.py` — 仍有效（测试 core 模块）
- `test_services.py` — 需重写，改用 `app.services.*`
- `test_repositories.py` — 需重写，改用 `app.services.*_repo`
- `test_integration.py` — 需重写，改用 FastAPI TestClient

### 步骤 7：清理 config.json

`config.json` 中仍包含旧的 providers/prompts/trash 数据（已迁移到数据库）。清理为仅保留 `system_settings`。

### 步骤 8：验证

- 后端可正常启动
- Vue 前端可正常构建和运行
- 所有 API 端点正常响应
- 前端所有功能正常工作
