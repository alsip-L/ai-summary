# AI Summary 项目 - 基于功能需求的架构设计

## 核心功能需求分析

基于您的描述，项目需要实现以下核心功能：

1. **文件处理流程**: txt文件 → AI总结 → md文件
2. **大模型管理**: 方便地管理 URL、API Key、模型选择
3. **提示词管理**: 方便地管理不同的 Prompt
4. **路径管理**: 方便地设置 txt 输入路径和 md 输出路径

---

## 推荐架构：以功能模块为核心的扁平化架构

考虑到这是一个工具型应用，功能相对集中，推荐采用**扁平化模块架构**，避免过度设计。

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     入口层 (Entry)                           │
│                    run.py / app.py                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    路由层 (Routes)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   main.py   │  │  config.py  │  │   processing.py     │  │
│  │  主页面路由 │  │ 配置管理路由│  │   文件处理路由      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   核心功能层 (Core Features)                  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  ModelManager   │  │  PromptManager  │                   │
│  │  大模型管理器   │  │  提示词管理器   │                   │
│  │  - URL管理      │  │  - Prompt增删改 │                   │
│  │  - Key管理      │  │  - Prompt切换   │                   │
│  │  - 模型切换     │  │                 │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                            │
│           └────────┬───────────┘                            │
│                    │                                        │
│                    ▼                                        │
│  ┌─────────────────────────────────────┐                   │
│  │         FileProcessor               │                   │
│  │         文件处理器                   │                   │
│  │  - 扫描txt文件                      │                   │
│  │  - 调用AI总结                       │                   │
│  │  - 生成md文件                       │                   │
│  │  - 路径管理                         │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   基础设施层 (Infrastructure)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  config.py  │  │  logger.py  │  │   exceptions.py     │  │
│  │  配置持久化 │  │  日志记录   │  │   异常定义          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 推荐的目录结构

```
ai_summary/
├── app.py                      # 主应用入口（简化版）
├── run.py                      # 启动脚本
├── config.json                 # 配置文件
├── requirements.txt
│
├── core/                       # 核心基础设施
│   ├── __init__.py
│   ├── config_manager.py       # 配置管理（替代现有的config.py）
│   ├── logger.py              # 日志（保留现有）
│   └── exceptions.py          # 异常（保留现有）
│
├── managers/                   # 功能管理器（您管理功能的入口）
│   ├── __init__.py
│   ├── model_manager.py        # 大模型管理（URL、Key、模型）
│   ├── prompt_manager.py       # 提示词管理（保留现有）
│   └── file_manager.py         # 文件路径管理（输入/输出路径）
│
├── processors/                 # 处理器（实际工作）
│   ├── __init__.py
│   ├── ai_processor.py         # AI调用（保留现有）
│   └── file_processor.py       # 文件处理（保留现有）
│
├── routes/                     # 路由（简洁明了）
│   ├── __init__.py
│   ├── main.py                 # 主页面
│   ├── config_routes.py        # 配置相关API
│   └── processing_routes.py    # 文件处理API
│
├── static/                     # 前端资源
│   ├── style.css
│   └── script.js
│
├── templates/                  # HTML模板
│   └── index.html
│
└── tests/                      # 测试
    ├── test_managers.py
    └── test_processors.py
```

---

## 核心功能模块设计

### 1. ModelManager - 大模型管理器

这是您管理大模型的核心入口。

```python
# managers/model_manager.py
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from core.config_manager import ConfigManager

@dataclass
class ModelConfig:
    """大模型配置数据类"""
    name: str           # 显示名称，如"阿里通义"
    base_url: str       # API地址
    api_key: str        # API密钥
    models: Dict[str, str]  # 模型列表，如{"通义千问Plus": "qwen-plus"}
    is_active: bool = True  # 是否启用

class ModelManager:
    """
    大模型管理器
    
    职责：统一管理所有大模型的配置
    
    使用示例：
        manager = ModelManager()
        
        # 添加新的大模型
        manager.add_model(ModelConfig(
            name="DeepSeek",
            base_url="https://api.deepseek.com",
            api_key="sk-xxx",
            models={"DeepSeek Chat": "deepseek-chat"}
        ))
        
        # 获取所有模型
        models = manager.get_all_models()
        
        # 切换当前使用的模型
        manager.set_current_model("DeepSeek", "DeepSeek Chat")
        
        # 更新API Key
        manager.update_api_key("DeepSeek", "sk-new-key")
    """
    
    CONFIG_KEY = "providers"
    CURRENT_KEY = "current_provider"
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_all_models(self) -> Dict[str, ModelConfig]:
        """获取所有大模型配置"""
        providers = self.config.get(self.CONFIG_KEY, [])
        return {
            p['name']: ModelConfig(**p) 
            for p in providers 
            if p.get('is_active', True)
        }
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """获取指定大模型配置"""
        models = self.get_all_models()
        return models.get(name)
    
    def add_model(self, model: ModelConfig) -> bool:
        """添加新的大模型"""
        providers = self.config.get(self.CONFIG_KEY, [])
        
        # 检查是否已存在
        for i, p in enumerate(providers):
            if p['name'] == model.name:
                providers[i] = asdict(model)
                break
        else:
            providers.append(asdict(model))
        
        return self.config.set(self.CONFIG_KEY, providers)
    
    def delete_model(self, name: str) -> bool:
        """删除大模型（软删除，移到回收站）"""
        # 实现删除逻辑...
        pass
    
    def update_api_key(self, model_name: str, api_key: str) -> bool:
        """更新指定大模型的API Key"""
        model = self.get_model(model_name)
        if not model:
            return False
        
        model.api_key = api_key
        return self.add_model(model)
    
    def update_base_url(self, model_name: str, base_url: str) -> bool:
        """更新指定大模型的Base URL"""
        model = self.get_model(model_name)
        if not model:
            return False
        
        model.base_url = base_url
        return self.add_model(model)
    
    def get_current_model(self) -> Optional[Dict]:
        """获取当前选中的大模型和模型"""
        current = self.config.get(self.CURRENT_KEY, {})
        provider_name = current.get('provider')
        model_key = current.get('model')
        
        if not provider_name:
            # 默认返回第一个
            models = self.get_all_models()
            if models:
                first = list(models.values())[0]
                return {
                    'provider': first,
                    'model_key': list(first.models.keys())[0] if first.models else None
                }
            return None
        
        provider = self.get_model(provider_name)
        if not provider:
            return None
            
        return {
            'provider': provider,
            'model_key': model_key or (list(provider.models.keys())[0] if provider.models else None)
        }
    
    def set_current_model(self, provider_name: str, model_key: str) -> bool:
        """设置当前使用的大模型和模型"""
        return self.config.set(self.CURRENT_KEY, {
            'provider': provider_name,
            'model': model_key
        })
    
    def add_model_variant(self, provider_name: str, model_key: str, model_id: str) -> bool:
        """为大模型添加新的模型变体"""
        model = self.get_model(provider_name)
        if not model:
            return False
        
        model.models[model_key] = model_id
        return self.add_model(model)
```

### 2. FileManager - 文件路径管理器

管理输入(txt)和输出(md)路径。

```python
# managers/file_manager.py
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass
from core.config_manager import ConfigManager

@dataclass
class PathConfig:
    """路径配置"""
    input_path: str      # txt文件输入路径
    output_path: str     # md文件输出路径（可选，默认与输入相同）
    
    def __post_init__(self):
        # 如果输出路径未设置，默认与输入路径相同
        if not self.output_path:
            self.output_path = self.input_path

class FileManager:
    """
    文件路径管理器
    
    职责：管理txt输入路径和md输出路径
    
    使用示例：
        manager = FileManager()
        
        # 设置路径
        manager.set_paths("/data/txt_files", "/output/md_files")
        
        # 获取当前路径配置
        paths = manager.get_paths()
        
        # 扫描txt文件
        txt_files = manager.scan_input_files()
        
        # 获取对应的输出路径
        md_path = manager.get_output_path("/data/txt_files/article.txt")
    """
    
    PATHS_KEY = "file_paths"
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_paths(self) -> PathConfig:
        """获取当前路径配置"""
        paths = self.config.get(self.PATHS_KEY, {})
        return PathConfig(
            input_path=paths.get('input', ''),
            output_path=paths.get('output', '')
        )
    
    def set_paths(self, input_path: str, output_path: str = None) -> bool:
        """设置输入和输出路径"""
        return self.config.set(self.PATHS_KEY, {
            'input': input_path,
            'output': output_path or input_path
        })
    
    def scan_input_files(self) -> List[Path]:
        """扫描输入路径中的所有txt文件"""
        paths = self.get_paths()
        input_dir = Path(paths.input_path)
        
        if not input_dir.exists():
            return []
        
        return list(input_dir.rglob("*.txt"))
    
    def get_output_path(self, input_file_path: str) -> Path:
        """
        根据输入文件路径生成输出文件路径
        
        例如：
            输入: /data/txt_files/folder/article.txt
            输出: /output/md_files/folder/article.md
        """
        paths = self.get_paths()
        input_path = Path(input_file_path)
        
        # 计算相对路径
        try:
            relative = input_path.relative_to(paths.input_path)
        except ValueError:
            # 如果不在输入路径下，直接使用文件名
            relative = input_path.name
        
        # 生成输出路径
        output_dir = Path(paths.output_path)
        output_file = output_dir / relative.with_suffix('.md')
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        return output_file
    
    def validate_paths(self) -> tuple[bool, str]:
        """验证路径配置是否有效"""
        paths = self.get_paths()
        
        if not paths.input_path:
            return False, "输入路径未设置"
        
        input_dir = Path(paths.input_path)
        if not input_dir.exists():
            return False, f"输入路径不存在: {paths.input_path}"
        
        if not input_dir.is_dir():
            return False, f"输入路径不是目录: {paths.input_path}"
        
        # 检查输出路径（如果不存在会尝试创建）
        if paths.output_path:
            output_dir = Path(paths.output_path)
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"无法创建输出目录: {e}"
        
        return True, "路径有效"
```

### 3. ConfigManager - 配置管理器

统一的配置读写接口。

```python
# core/config_manager.py
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path

class ConfigManager:
    """
    配置管理器
    
    职责：统一管理配置文件的读写
    
    使用示例：
        config = ConfigManager()
        
        # 读取配置
        providers = config.get('providers', [])
        
        # 写入配置
        config.set('providers', new_providers)
        
        # 批量更新
        config.update({
            'providers': providers,
            'current_provider': current,
            'file_paths': paths
        })
    """
    
    _instance = None
    _config_path: Path = Path("config.json")
    _cache: Dict = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._cache is None:
            self._load()
    
    def _load(self) -> None:
        """加载配置文件"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = self._default_config()
                self._save()
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            self._cache = self._default_config()
    
    def _save(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "providers": [],
            "current_provider": {},
            "custom_prompts": {},
            "current_prompt": "",
            "file_paths": {
                "input": "",
                "output": ""
            },
            "trash": {
                "providers": [],
                "custom_prompts": {}
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号路径）"""
        keys = key.split('.')
        value = self._cache
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项（支持点号路径）"""
        keys = key.split('.')
        config = self._cache
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return self._save()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value)
        return True
    
    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._cache.copy()
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load()
```

### 4. 简化的主应用

```python
# app.py
from flask import Flask, render_template, request, jsonify
from managers.model_manager import ModelManager
from managers.prompt_manager import PromptManager
from managers.file_manager import FileManager
from processors.ai_processor import AIProcessor
from processors.file_processor import FileProcessor
import threading

app = Flask(__name__)
app.secret_key = "your-secret-key"

# 初始化管理器
model_manager = ModelManager()
prompt_manager = PromptManager()
file_manager = FileManager()

# 处理状态（简化版）
processing_status = {
    'is_running': False,
    'progress': 0,
    'current_file': '',
    'total_files': 0,
    'processed_files': 0,
    'results': []
}

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html',
        models=model_manager.get_all_models(),
        current_model=model_manager.get_current_model(),
        prompts=prompt_manager.get_all(),
        current_prompt=prompt_manager.get_current(),
        paths=file_manager.get_paths()
    )

# ========== 大模型管理API ==========

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有大模型"""
    models = model_manager.get_all_models()
    return jsonify({
        'success': True,
        'data': {name: {
            'name': m.name,
            'base_url': m.base_url,
            'models': m.models
        } for name, m in models.items()}
    })

@app.route('/api/models', methods=['POST'])
def add_model():
    """添加/更新大模型"""
    data = request.json
    from managers.model_manager import ModelConfig
    
    model = ModelConfig(
        name=data['name'],
        base_url=data['base_url'],
        api_key=data.get('api_key', ''),
        models=data.get('models', {})
    )
    
    success = model_manager.add_model(model)
    return jsonify({'success': success})

@app.route('/api/models/<name>/apikey', methods=['PUT'])
def update_api_key(name):
    """更新API Key"""
    data = request.json
    success = model_manager.update_api_key(name, data['api_key'])
    return jsonify({'success': success})

@app.route('/api/models/current', methods=['POST'])
def set_current_model():
    """设置当前使用的大模型"""
    data = request.json
    success = model_manager.set_current_model(
        data['provider'], 
        data['model']
    )
    return jsonify({'success': success})

# ========== 提示词管理API ==========

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """获取所有提示词"""
    prompts = prompt_manager.get_all()
    return jsonify({'success': True, 'data': prompts})

@app.route('/api/prompts', methods=['POST'])
def save_prompt():
    """保存提示词"""
    data = request.json
    success = prompt_manager.save(data['name'], data['content'])
    return jsonify({'success': success})

@app.route('/api/prompts/current', methods=['POST'])
def set_current_prompt():
    """设置当前提示词"""
    data = request.json
    success = prompt_manager.set_current(data['name'])
    return jsonify({'success': success})

# ========== 路径管理API ==========

@app.route('/api/paths', methods=['GET'])
def get_paths():
    """获取当前路径配置"""
    paths = file_manager.get_paths()
    is_valid, message = file_manager.validate_paths()
    return jsonify({
        'success': True,
        'data': {
            'input': paths.input_path,
            'output': paths.output_path,
            'is_valid': is_valid,
            'message': message
        }
    })

@app.route('/api/paths', methods=['POST'])
def set_paths():
    """设置路径"""
    data = request.json
    success = file_manager.set_paths(
        data['input'],
        data.get('output')
    )
    return jsonify({'success': success})

# ========== 文件处理API ==========

@app.route('/api/process', methods=['POST'])
def start_processing():
    """开始处理文件"""
    global processing_status
    
    # 检查是否已在运行
    if processing_status['is_running']:
        return jsonify({
            'success': False,
            'error': '已有任务正在运行'
        }), 409
    
    # 验证路径
    is_valid, message = file_manager.validate_paths()
    if not is_valid:
        return jsonify({
            'success': False,
            'error': message
        }), 400
    
    # 获取配置
    current_model = model_manager.get_current_model()
    if not current_model:
        return jsonify({
            'success': False,
            'error': '未选择大模型'
        }), 400
    
    current_prompt = prompt_manager.get_current()
    if not current_prompt:
        return jsonify({
            'success': False,
            'error': '未选择提示词'
        }), 400
    
    # 扫描文件
    txt_files = file_manager.scan_input_files()
    if not txt_files:
        return jsonify({
            'success': False,
            'error': '未找到txt文件'
        }), 400
    
    # 重置状态
    processing_status = {
        'is_running': True,
        'progress': 0,
        'current_file': '',
        'total_files': len(txt_files),
        'processed_files': 0,
        'results': []
    }
    
    # 启动后台线程
    def process_task():
        provider = current_model['provider']
        model_id = provider.models.get(current_model['model_key'])
        
        ai_processor = AIProcessor(provider.name, provider.api_key)
        file_processor = FileProcessor(file_manager.get_paths().input_path)
        
        for i, txt_file in enumerate(txt_files):
            processing_status['current_file'] = txt_file.name
            
            try:
                # 读取文件
                content = file_processor.read_file(txt_file)
                
                # AI处理
                response = ai_processor.process(
                    content, 
                    model_id, 
                    current_prompt
                )
                
                # 保存结果
                output_path = file_manager.get_output_path(str(txt_file))
                file_processor.save_response(txt_file, response)
                
                processing_status['results'].append({
                    'source': str(txt_file),
                    'output': str(output_path),
                    'success': True
                })
                
            except Exception as e:
                processing_status['results'].append({
                    'source': str(txt_file),
                    'output': None,
                    'success': False,
                    'error': str(e)
                })
            
            processing_status['processed_files'] = i + 1
            processing_status['progress'] = int((i + 1) / len(txt_files) * 100)
        
        processing_status['is_running'] = False
        processing_status['current_file'] = ''
    
    thread = threading.Thread(target=process_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '处理任务已启动',
        'total_files': len(txt_files)
    })

@app.route('/api/process/status', methods=['GET'])
def get_process_status():
    """获取处理状态"""
    return jsonify({
        'success': True,
        'data': processing_status
    })

@app.route('/api/process/cancel', methods=['POST'])
def cancel_processing():
    """取消处理"""
    global processing_status
    processing_status['is_running'] = False
    return jsonify({'success': True, 'message': '已取消'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 配置文件的最终结构

```json
{
  "providers": [
    {
      "name": "阿里通义",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "sk-your-key",
      "models": {
        "通义千问Plus": "qwen-plus",
        "通义千问Turbo": "qwen-turbo"
      },
      "is_active": true
    }
  ],
  "current_provider": {
    "provider": "阿里通义",
    "model": "通义千问Plus"
  },
  "custom_prompts": {
    "文章总结": "你是一个专业的文本总结专家...",
    "代码分析": "你是一个代码审查专家..."
  },
  "current_prompt": "文章总结",
  "file_paths": {
    "input": "D:/data/txt_files",
    "output": "D:/output/md_files"
  },
  "trash": {
    "providers": [],
    "custom_prompts": {}
  }
}
```

---

## 总结

这个架构设计的核心思想是：

1. **扁平化** - 不过度分层，直接对应功能需求
2. **管理器模式** - 每个管理器对应一个您需要管理的功能领域
3. **清晰的职责**:
   - `ModelManager`: 管理大模型的URL、Key、模型选择
   - `PromptManager`: 管理提示词
   - `FileManager`: 管理输入/输出路径
   - `ConfigManager`: 统一配置读写
4. **简洁的API** - RESTful API设计，易于前端调用

这个架构既满足了您的功能需求，又保持了代码的简洁和可维护性。您觉得这个设计符合您的期望吗？
