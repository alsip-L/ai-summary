# 项目修复实施计划

基于 `feature_modules_analysis_verification.md` 中发现的问题，对项目进行代码层面的修复。修复分为7个任务，按依赖顺序执行。

---

## 任务1：删除已废弃的 services 模块（排除 state_service.py）

**问题**：`services/provider_service.py`、`services/prompt_service.py`、`services/file_service.py` 标记为 deprecated 且零外部引用，但 `services/state_service.py` 是核心模块（被 app.py 引用），不能删除。

**操作**：
1. 删除 `services/provider_service.py`（206行）
2. 删除 `services/prompt_service.py`（129行）
3. 删除 `services/file_service.py`（174行）
4. 更新 `services/__init__.py`：移除对已删除模块的导入和导出，仅保留 `ProcessingState`
5. 运行测试验证 `ProcessingState` 仍可正常导入

**预期结果**：减少约 524 行代码，保留 `state_service.py` 不受影响

---

## 任务2：删除已废弃的 processors 模块

**问题**：`processors/ai_processor.py` 和 `processors/file_processor.py` 标记为 deprecated，零外部引用。

**操作**：
1. 删除 `processors/ai_processor.py`（220行）
2. 删除 `processors/file_processor.py`（147行）
3. 删除 `processors/__init__.py`（5行）
4. 删除整个 `processors/` 目录

**预期结果**：减少约 372 行代码

---

## 任务3：删除已废弃的 core/config.py

**问题**：`core/config.py` 仅做转发，零外部引用。

**操作**：
1. 删除 `core/config.py`（6行）
2. 确认无其他文件引用 `from core.config import` 或 `from core import config`（已验证：零引用）

**预期结果**：减少 6 行代码

---

## 任务4：消除重复的 debug_print 定义

**问题**：`debug_print` 在3处定义：`app.py`（L45-55）、`utils.py`（L15-25）、`core/logger.py`（L77-99）。app.py 和 utils.py 的版本完全相同，都委托给 logger.py。

**操作**：
1. 在 `app.py` 中：删除 `debug_print` 函数定义（L45-55），改为 `from core.logger import debug_print`
2. 在 `utils.py` 中：删除 `debug_print` 函数定义（L15-25），改为 `from core.logger import debug_print`
3. 确认 `core/logger.py` 的 `debug_print` 是唯一的实现

**预期结果**：减少约 22 行重复代码，统一到 logger.py

---

## 任务5：统一 ProviderManager — 移除 app.py 中的薄包装层

**问题**：`app.py` 中的 `ProviderManager`（L85-104）是薄包装层，仅3个静态方法，全部委托给 `utils.py` 的函数。`app.py` 中的 `PromptManager`（L106-119）同理。

**操作**：
1. 在 `app.py` 中：删除 `ProviderManager` 类定义（L85-104）
2. 在 `app.py` 中：删除 `PromptManager` 类定义（L106-119）
3. 在 `app.py` 的 import 区域添加：`from utils import ProviderManager, PromptManager`
4. 更新 `utils.py`：确保 `ProviderManager` 和 `PromptManager` 类包含 app.py 原来通过薄包装调用的所有方法（`get_all_providers`→`load`, `get_default_provider`→新增, `get_provider_models`→新增, `get_all_prompts`→`load`, `get_default_prompt`→新增）
5. 在 `utils.py` 的 `ProviderManager` 中添加 `get_default_provider` 和 `get_provider_models` 静态方法
6. 在 `utils.py` 的 `PromptManager` 中添加 `get_default_prompt` 静态方法
7. 验证 app.py 中所有对 `ProviderManager.get_all_providers()`、`ProviderManager.get_default_provider()`、`ProviderManager.get_provider_models()`、`PromptManager.get_all_prompts()`、`PromptManager.get_default_prompt()` 的调用仍然正常

**注意**：`managers/model_manager.py` 的 `ModelManager` 被 `managers/trash_manager.py` 依赖，不能删除。它与 `utils.py` 的 `ProviderManager` 功能重叠但职责不同（ModelManager 使用 dataclass，ProviderManager 使用 dict），暂不统一。

**预期结果**：减少约 34 行代码，消除 app.py 中的重复类定义

---

## 任务6：修复暗黑主题死代码

**问题**：`script.js` 中有 `setupThemeToggle()` 函数（L735-751）查找 `id="themeToggle"` 的按钮，但 `index.html` 中不存在此元素，导致暗黑主题功能完全无法触发。`style.css` 中有约 60 行 `body.dark-theme` 样式规则也是死代码。

**操作**（两种方案，选择方案A）：

**方案A：添加暗黑主题切换按钮（保留功能）**
1. 在 `index.html` 的侧边栏底部（系统设置下方）添加主题切换按钮：`<button id="themeToggle" class="btn btn-secondary" style="width:100%">🌓 切换主题</button>`
2. 保留 `script.js` 中的 `setupThemeToggle()` 函数
3. 保留 `style.css` 中的 `body.dark-theme` 样式

**方案B：移除暗黑主题代码（删除功能）**
1. 从 `script.js` 删除 `setupThemeToggle()` 函数（L735-751）和 `UIManager.setupThemeToggle()` 调用（L974）
2. 从 `style.css` 删除所有 `body.dark-theme` 相关规则（L1840-1901，约60行）
3. 从 `style.css` 删除 `[data-theme="dark"]` CSS 变量定义（L46-66，约20行）

**选择方案A的理由**：暗黑主题是有价值的功能，只需添加一个按钮即可激活，成本极低。

**预期结果**：暗黑主题功能从死代码变为可用功能

---

## 任务7：重命名 managers/file_manager.py 中的 FileManager 避免混淆

**问题**：`utils.py` 的 `FileManager`（文件处理：扫描+AI处理+保存）和 `managers/file_manager.py` 的 `FileManager`（路径管理：输入输出路径配置）同名但职责完全不同，容易混淆。

**操作**：
1. 将 `managers/file_manager.py` 中的 `FileManager` 类重命名为 `FilePathManager`
2. 将 `managers/file_manager.py` 中的 `PathConfig` 保持不变
3. 更新 `managers/__init__.py` 中的导出（如有）
4. 搜索并更新所有对 `managers.file_manager.FileManager` 的引用（当前零外部引用，仅测试文件可能间接使用）

**预期结果**：消除命名混淆，两个类的职责更加清晰

---

## 风险控制

1. **每个任务完成后运行测试**：`python -m pytest tests/ -v`
2. **任务1特别注意**：不能删除 `state_service.py`，修改 `__init__.py` 时只移除已删除模块的导入
3. **任务5特别注意**：需要在 utils.py 中补充 app.py 薄包装层的方法，确保 API 兼容
4. **任务6特别注意**：选择方案A时，按钮位置需在 HTML 中合理放置

---

## 预期总效果

| 任务 | 减少代码行数 | 说明 |
|------|------------|------|
| 任务1 | ~524行 | 删除 deprecated services |
| 任务2 | ~372行 | 删除 deprecated processors |
| 任务3 | ~6行 | 删除废弃 core/config.py |
| 任务4 | ~22行 | 消除重复 debug_print |
| 任务5 | ~34行 | 移除薄包装类 |
| 任务6 | +1行 | 添加暗黑主题按钮（净增） |
| 任务7 | ~0行 | 重命名，行数不变 |
| **合计** | **~957行** | 净减少代码量 |
