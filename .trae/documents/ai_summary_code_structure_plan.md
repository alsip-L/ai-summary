# AI Summary 代码结构优化计划

## 概述
针对当前项目的代码结构问题，制定专项优化计划，重点解决代码组织、模块划分和可维护性问题。

---

## 当前代码结构问题诊断

### 1. 文件组织混乱
- `app.py` 超过 600 行，职责过重
- `utils.py` 超过 500 行，功能混杂
- 缺乏清晰的目录结构划分

### 2. 重复代码严重
- `debug_print` 函数在 `app.py` 和 `utils.py` 中重复定义
- 配置加载逻辑分散在多个地方
- 错误处理模式不统一

### 3. 函数过长
- `run_processing_task` 函数超过 200 行
- `index` 路由函数超过 150 行
- 单个函数承担过多职责

### 4. 模块耦合度高
- 配置管理与业务逻辑紧密耦合
- 文件处理与 AI 调用逻辑混杂
- 缺乏清晰的分层架构

### 5. 缺乏抽象
- 没有统一的接口定义
- 类设计不够合理
- 扩展性受限

---

## 优化目标

1. **单一职责**：每个模块、类、函数只负责一件事
2. **高内聚低耦合**：模块内部紧密相关，模块之间松散耦合
3. **可测试性**：便于编写单元测试
4. **可扩展性**：易于添加新功能
5. **可维护性**：代码清晰易读，便于维护

---

## 优化方案

### 第一阶段：目录结构重构

#### 1.1 创建标准项目结构

```
ai_summary/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── routes.py          # 路由定义
│   ├── models.py          # 数据模型
│   └── services.py        # 业务服务
├── core/                   # 核心功能
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志管理
│   └── exceptions.py      # 自定义异常
├── processors/             # 处理器
│   ├── __init__.py
│   ├── file_processor.py  # 文件处理
│   └── ai_processor.py    # AI 处理
├── managers/               # 管理器
│   ├── __init__.py
│   ├── provider_manager.py # AI 提供商管理
│   ├── prompt_manager.py  # 提示词管理
│   └── trash_manager.py   # 回收站管理
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── validators.py      # 验证工具
│   └── helpers.py         # 辅助函数
├── static/                 # 静态文件
│   ├── css/
│   └── js/
├── templates/              # 模板文件
├── tests/                  # 测试文件
│   ├── __init__.py
│   ├── test_processors.py
│   └── test_managers.py
├── config.json            # 配置文件
├── requirements.txt       # 依赖
└── run.py                 # 启动脚本
```

#### 1.2 迁移现有代码

**步骤**：
1. 创建新的目录结构
2. 将 `utils.py` 中的功能拆分到各个模块
3. 将 `app.py` 中的路由和业务逻辑分离
4. 更新导入语句

**预期收益**：
- 代码组织清晰
- 便于定位和维护
- 支持模块化开发

---

### 第二阶段：核心模块提取

#### 2.1 日志模块 (core/logger.py)

**目标**：统一日志管理，消除重复代码

**实现**：
```python
import logging
import sys
from functools import lru_cache

@lru_cache()
def get_logger(name: str = "ai_summary") -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 从环境变量读取日志级别
        level = os.environ.get('DEBUG_LEVEL', 'ERROR').upper()
        logger.setLevel(getattr(logging, level, logging.ERROR))
    
    return logger
```

**预期收益**：
- 消除重复代码
- 统一日志格式
- 支持日志级别配置

#### 2.2 配置模块 (core/config.py)

**目标**：集中管理配置，提供统一接口

**实现**：
```python
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path

class Config:
    """配置管理类"""
    
    _instance = None
    _config = None
    _config_path = Path("config.json")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load()
    
    def _load(self) -> None:
        """加载配置文件"""
        if self._config_path.exists():
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            self._config = {}
    
    def save(self) -> bool:
        """保存配置"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
```

**预期收益**：
- 统一配置访问接口
- 支持点号访问嵌套配置
- 实现单例模式避免重复加载

#### 2.3 异常模块 (core/exceptions.py)

**目标**：定义统一的异常体系

**实现**：
```python
class AISummaryException(Exception):
    """基础异常类"""
    pass

class ConfigError(AISummaryException):
    """配置错误"""
    pass

class ProviderError(AISummaryException):
    """AI 提供商错误"""
    pass

class FileProcessingError(AISummaryException):
    """文件处理错误"""
    pass

class ValidationError(AISummaryException):
    """验证错误"""
    pass
```

**预期收益**：
- 统一异常处理
- 便于错误分类和处理
- 提高代码可读性

---

### 第三阶段：业务逻辑分离

#### 3.1 文件处理器 (processors/file_processor.py)

**目标**：封装文件处理逻辑

**实现**：
```python
from pathlib import Path
from typing import List, Iterator
from core.exceptions import FileProcessingError

class FileProcessor:
    """文件处理器"""
    
    def __init__(self, directory: str):
        self.directory = Path(directory)
        if not self.directory.exists():
            raise FileProcessingError(f"目录不存在: {directory}")
    
    def scan_txt_files(self) -> List[Path]:
        """扫描目录中的 txt 文件"""
        return list(self.directory.rglob("*.txt"))
    
    def read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise FileProcessingError(f"读取文件失败: {file_path}, {e}")
    
    def save_response(self, source_file: Path, content: str) -> Path:
        """保存响应内容"""
        md_file = source_file.with_suffix('.md')
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return md_file
        except Exception as e:
            raise FileProcessingError(f"保存响应失败: {md_file}, {e}")
```

**预期收益**：
- 封装文件操作
- 统一错误处理
- 便于单元测试

#### 3.2 AI 处理器 (processors/ai_processor.py)

**目标**：封装 AI 调用逻辑

**实现**：
```python
from openai import OpenAI
from typing import Optional
from core.config import Config
from core.exceptions import ProviderError

class AIProcessor:
    """AI 处理器"""
    
    def __init__(self, provider_name: str, api_key: str):
        self.provider_name = provider_name
        self.api_key = api_key
        self.config = Config()
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """创建 AI 客户端"""
        providers = self.config.get('providers', [])
        provider = next(
            (p for p in providers if p.get('name') == self.provider_name),
            None
        )
        
        if not provider:
            raise ProviderError(f"提供商未找到: {self.provider_name}")
        
        return OpenAI(
            api_key=self.api_key,
            base_url=provider.get('base_url')
        )
    
    def process(self, content: str, model_id: str, system_prompt: str) -> str:
        """处理内容"""
        try:
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': content}
                ],
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise ProviderError(f"AI 处理失败: {e}")
```

**预期收益**：
- 封装 AI 调用细节
- 统一错误处理
- 便于切换 AI 提供商

---

### 第四阶段：管理器重构

#### 4.1 提供商管理器 (managers/provider_manager.py)

**目标**：重构提供商管理逻辑

**实现**：
```python
from typing import Dict, List, Optional
from core.config import Config
from core.exceptions import ProviderError

class ProviderManager:
    """AI 提供商管理器"""
    
    def __init__(self):
        self.config = Config()
    
    def get_all(self) -> Dict[str, dict]:
        """获取所有提供商"""
        providers = self.config.get('providers', [])
        return {p['name']: p for p in providers if 'name' in p}
    
    def get(self, name: str) -> Optional[dict]:
        """获取指定提供商"""
        return self.get_all().get(name)
    
    def save(self, name: str, base_url: str, api_key: str, models: dict) -> bool:
        """保存提供商"""
        providers = self.config.get('providers', [])
        
        # 查找或创建提供商
        provider = next(
            (p for p in providers if p.get('name') == name),
            None
        )
        
        if provider:
            provider.update({
                'base_url': base_url,
                'api_key': api_key,
                'models': models
            })
        else:
            providers.append({
                'name': name,
                'base_url': base_url,
                'api_key': api_key,
                'models': models
            })
        
        self.config.set('providers', providers)
        return self.config.save()
    
    def delete(self, name: str) -> bool:
        """删除提供商"""
        providers = self.config.get('providers', [])
        providers = [p for p in providers if p.get('name') != name]
        self.config.set('providers', providers)
        return self.config.save()
    
    def get_models(self, name: str) -> Dict[str, str]:
        """获取提供商的模型列表"""
        provider = self.get(name)
        if not provider:
            raise ProviderError(f"提供商未找到: {name}")
        return provider.get('models', {})
```

**预期收益**：
- 简化提供商管理
- 统一接口设计
- 便于扩展和维护

#### 4.2 提示词管理器 (managers/prompt_manager.py)

**目标**：重构提示词管理逻辑

**实现**：
```python
from typing import Dict, Optional
from core.config import Config

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.config = Config()
    
    def get_all(self) -> Dict[str, str]:
        """获取所有提示词"""
        prompts = self.config.get('custom_prompts', {})
        # 处理列表格式兼容性
        return {
            name: '\n'.join(content) if isinstance(content, list) else content
            for name, content in prompts.items()
        }
    
    def get(self, name: str) -> Optional[str]:
        """获取指定提示词"""
        return self.get_all().get(name)
    
    def save(self, name: str, content: str) -> bool:
        """保存提示词"""
        prompts = self.config.get('custom_prompts', {})
        prompts[name] = content
        self.config.set('custom_prompts', prompts)
        return self.config.save()
    
    def delete(self, name: str) -> bool:
        """删除提示词"""
        prompts = self.config.get('custom_prompts', {})
        if name in prompts:
            del prompts[name]
            self.config.set('custom_prompts', prompts)
            return self.config.save()
        return False
```

**预期收益**：
- 简化提示词管理
- 统一接口设计
- 提高代码复用性

---

### 第五阶段：路由和视图重构

#### 5.1 路由分离 (app/routes.py)

**目标**：将路由逻辑从 app.py 分离

**实现**：
```python
from flask import Blueprint, render_template, request, jsonify, session
from managers.provider_manager import ProviderManager
from managers.prompt_manager import PromptManager
from processors.file_processor import FileProcessor
from processors.ai_processor import AIProcessor

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """主页"""
    provider_manager = ProviderManager()
    prompt_manager = PromptManager()
    
    providers = provider_manager.get_all()
    prompts = prompt_manager.get_all()
    
    if request.method == 'POST':
        # 处理表单提交
        pass
    
    return render_template('index.html',
                         providers=providers,
                         prompts=prompts)

@main_bp.route('/api/start_processing', methods=['POST'])
def start_processing():
    """启动处理"""
    # 处理逻辑
    pass

@main_bp.route('/api/status', methods=['GET'])
def get_status():
    """获取状态"""
    # 处理逻辑
    pass
```

**预期收益**：
- 分离路由和业务逻辑
- 便于维护和测试
- 支持蓝图扩展

#### 5.2 应用初始化 (app/__init__.py)

**目标**：重构应用初始化逻辑

**实现**：
```python
from flask import Flask
import os

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key')
    
    # 注册蓝图
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # 注册错误处理
    from core.exceptions import AISummaryException
    
    @app.errorhandler(AISummaryException)
    def handle_exception(e):
        return jsonify({'error': str(e)}), 400
    
    return app
```

**预期收益**：
- 使用应用工厂模式
- 便于测试和配置
- 支持多环境部署

---

## 实施步骤

### 步骤 1：创建新目录结构
1. 创建 `app/`, `core/`, `processors/`, `managers/`, `utils/`, `tests/` 目录
2. 创建 `__init__.py` 文件

### 步骤 2：提取核心模块
1. 创建 `core/logger.py`，实现统一日志
2. 创建 `core/config.py`，实现配置管理
3. 创建 `core/exceptions.py`，定义异常体系

### 步骤 3：重构处理器
1. 创建 `processors/file_processor.py`
2. 创建 `processors/ai_processor.py`
3. 迁移并优化处理逻辑

### 步骤 4：重构管理器
1. 创建 `managers/provider_manager.py`
2. 创建 `managers/prompt_manager.py`
3. 创建 `managers/trash_manager.py`
4. 简化管理逻辑

### 步骤 5：重构路由
1. 创建 `app/routes.py`，分离路由逻辑
2. 创建 `app/__init__.py`，使用应用工厂模式
3. 更新 `run.py` 启动脚本

### 步骤 6：清理旧代码
1. 删除 `utils.py`
2. 删除旧的 `app.py`
3. 更新导入语句

### 步骤 7：测试验证
1. 运行单元测试
2. 验证功能完整性
3. 检查性能指标

---

## 预期收益

### 代码质量提升
- **代码行数减少**：消除重复代码，预计减少 20-30%
- **函数长度合理**：单个函数不超过 50 行
- **模块职责清晰**：每个模块只负责一件事

### 可维护性提升
- **易于定位**：清晰的目录结构，快速找到代码
- **易于修改**：低耦合设计，修改不影响其他模块
- **易于测试**：每个模块可独立测试

### 开发效率提升
- **并行开发**：不同模块可由不同开发者并行开发
- **代码复用**：公共功能提取为独立模块
- **快速上手**：新开发者能快速理解项目结构

---

## 风险评估

### 风险 1：功能回归
- **风险**：重构可能引入 bug，导致功能异常
- **缓解**：
  - 每个步骤完成后进行充分测试
  - 保持原有功能测试用例
  - 使用版本控制，便于回滚

### 风险 2：时间超支
- **风险**：重构工作可能比预期耗时更长
- **缓解**：
  - 分阶段实施，每个阶段独立交付
  - 优先处理高优先级模块
  - 保留旧代码作为备份

### 风险 3：团队适应
- **风险**：团队成员需要时间适应新结构
- **缓解**：
  - 编写详细的开发文档
  - 进行代码结构培训
  - 提供迁移指南

---

## 时间规划

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 创建目录结构 | 0.5 天 |
| 2 | 提取核心模块 | 1 天 |
| 3 | 重构处理器 | 1 天 |
| 4 | 重构管理器 | 1 天 |
| 5 | 重构路由 | 1 天 |
| 6 | 清理旧代码 | 0.5 天 |
| 7 | 测试验证 | 1 天 |
| **总计** | | **6 天** |

---

## 验收标准

1. **功能完整性**：所有原有功能正常运行
2. **代码质量**：
   - 无重复代码
   - 函数长度合理
   - 模块职责清晰
3. **测试覆盖**：核心模块单元测试覆盖率达到 80%
4. **文档完整**：更新开发文档和 API 文档
5. **性能指标**：性能不劣于原有版本
