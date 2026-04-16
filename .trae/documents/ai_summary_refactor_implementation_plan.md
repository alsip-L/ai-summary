# AI Summary 项目 - 重构实施计划

## 目标
按照之前讨论的功能需求，重构现有代码，使其结构更清晰、更易于维护。

## 核心功能（保持不变）
1. txt文件 → AI总结 → md文件
2. 管理大模型的URL、API Key、模型选择
3. 管理不同的Prompt
4. 管理txt输入路径和md输出路径

---

## 重构步骤

### 阶段1：创建新的配置管理器
**文件**: `core/config_manager.py`

统一配置读写，替代现有的多个配置管理方式。

```python
import json
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    """统一配置管理器"""
    
    _instance = None
    _config_path = Path("config.json")
    _cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._cache is None:
            self._load()
    
    def _load(self):
        if self._config_path.exists():
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
        else:
            self._cache = self._default_config()
            self._save()
    
    def _save(self) -> bool:
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def _default_config(self) -> Dict:
        return {
            "providers": [],
            "current_provider": {},
            "custom_prompts": {},
            "current_prompt": "",
            "file_paths": {"input": "", "output": ""},
            "trash": {"providers": [], "custom_prompts": {}}
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置，支持点号路径如 'providers.0.name'"""
        keys = key.split('.')
        value = self._cache
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置，支持点号路径"""
        keys = key.split('.')
        config = self._cache
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        return self._save()
```

---

### 阶段2：创建大模型管理器
**文件**: `managers/model_manager.py`

管理所有大模型的配置（URL、Key、模型列表）。

```python
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from core.config_manager import ConfigManager

@dataclass
class ModelConfig:
    """大模型配置"""
    name: str
    base_url: str
    api_key: str
    models: Dict[str, str]
    is_active: bool = True

class ModelManager:
    """大模型管理器"""
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_all(self) -> Dict[str, ModelConfig]:
        """获取所有大模型"""
        providers = self.config.get("providers", [])
        return {
            p["name"]: ModelConfig(**p)
            for p in providers
            if p.get("is_active", True)
        }
    
    def get(self, name: str) -> Optional[ModelConfig]:
        """获取指定大模型"""
        return self.get_all().get(name)
    
    def save(self, model: ModelConfig) -> bool:
        """保存大模型配置"""
        providers = self.config.get("providers", [])
        
        # 查找并更新或添加
        for i, p in enumerate(providers):
            if p["name"] == model.name:
                providers[i] = asdict(model)
                break
        else:
            providers.append(asdict(model))
        
        return self.config.set("providers", providers)
    
    def update_api_key(self, name: str, api_key: str) -> bool:
        """更新API Key"""
        model = self.get(name)
        if not model:
            return False
        model.api_key = api_key
        return self.save(model)
    
    def get_current(self) -> Optional[Dict]:
        """获取当前选中的大模型"""
        current = self.config.get("current_provider", {})
        provider_name = current.get("provider")
        model_key = current.get("model")
        
        if not provider_name:
            # 默认返回第一个
            models = self.get_all()
            if models:
                first = list(models.values())[0]
                return {
                    "provider": first,
                    "model_key": list(first.models.keys())[0] if first.models else None
                }
            return None
        
        provider = self.get(provider_name)
        if not provider:
            return None
        
        return {
            "provider": provider,
            "model_key": model_key or (list(provider.models.keys())[0] if provider.models else None)
        }
    
    def set_current(self, provider_name: str, model_key: str) -> bool:
        """设置当前大模型"""
        return self.config.set("current_provider", {
            "provider": provider_name,
            "model": model_key
        })
```

---

### 阶段3：创建文件路径管理器
**文件**: `managers/file_manager.py`

管理输入路径（txt）和输出路径（md）。

```python
from typing import List
from pathlib import Path
from dataclasses import dataclass
from core.config_manager import ConfigManager

@dataclass
class PathConfig:
    """路径配置"""
    input_path: str
    output_path: str
    
    def __post_init__(self):
        if not self.output_path:
            self.output_path = self.input_path

class FileManager:
    """文件路径管理器"""
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_paths(self) -> PathConfig:
        """获取当前路径配置"""
        paths = self.config.get("file_paths", {})
        return PathConfig(
            input_path=paths.get("input", ""),
            output_path=paths.get("output", "")
        )
    
    def set_paths(self, input_path: str, output_path: str = None) -> bool:
        """设置路径"""
        return self.config.set("file_paths", {
            "input": input_path,
            "output": output_path or input_path
        })
    
    def scan_input_files(self) -> List[Path]:
        """扫描输入路径中的所有txt文件"""
        paths = self.get_paths()
        input_dir = Path(paths.input_path)
        
        if not input_dir.exists():
            return []
        
        return list(input_dir.rglob("*.txt"))
    
    def get_output_path(self, input_file_path: str) -> Path:
        """根据输入文件路径生成输出文件路径"""
        paths = self.get_paths()
        input_path = Path(input_file_path)
        
        # 计算相对路径
        try:
            relative = input_path.relative_to(paths.input_path)
        except ValueError:
            relative = input_path.name
        
        # 生成输出路径
        output_dir = Path(paths.output_path)
        output_file = output_dir / relative.with_suffix(".md")
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        return output_file
    
    def validate_paths(self) -> tuple[bool, str]:
        """验证路径配置"""
        paths = self.get_paths()
        
        if not paths.input_path:
            return False, "输入路径未设置"
        
        input_dir = Path(paths.input_path)
        if not input_dir.exists():
            return False, f"输入路径不存在: {paths.input_path}"
        
        if not input_dir.is_dir():
            return False, f"输入路径不是目录: {paths.input_path}"
        
        return True, "路径有效"
```

---

### 阶段4：简化主应用
**文件**: `app.py`

使用新的管理器重构主应用。

```python
from flask import Flask, render_template, request, jsonify
from managers.model_manager import ModelManager, ModelConfig
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

# 处理状态
processing_status = {
    "is_running": False,
    "progress": 0,
    "current_file": "",
    "total_files": 0,
    "processed_files": 0,
    "results": []
}

@app.route("/")
def index():
    """主页面"""
    current = model_manager.get_current()
    return render_template("index.html",
        models=model_manager.get_all(),
        current_provider=current["provider"] if current else None,
        current_model=current["model_key"] if current else None,
        prompts=prompt_manager.get_all(),
        current_prompt=prompt_manager.get_current(),
        paths=file_manager.get_paths()
    )

# ========== 大模型管理API ==========

@app.route("/api/models", methods=["GET"])
def get_models():
    """获取所有大模型"""
    models = model_manager.get_all()
    return jsonify({
        "success": True,
        "data": {
            name: {
                "name": m.name,
                "base_url": m.base_url,
                "models": m.models
            }
            for name, m in models.items()
        }
    })

@app.route("/api/models", methods=["POST"])
def add_model():
    """添加/更新大模型"""
    data = request.json
    
    model = ModelConfig(
        name=data["name"],
        base_url=data["base_url"],
        api_key=data.get("api_key", ""),
        models=data.get("models", {})
    )
    
    success = model_manager.save(model)
    return jsonify({"success": success})

@app.route("/api/models/<name>/apikey", methods=["PUT"])
def update_api_key(name):
    """更新API Key"""
    data = request.json
    success = model_manager.update_api_key(name, data["api_key"])
    return jsonify({"success": success})

@app.route("/api/models/current", methods=["POST"])
def set_current_model():
    """设置当前大模型"""
    data = request.json
    success = model_manager.set_current(data["provider"], data["model"])
    return jsonify({"success": success})

# ========== 提示词管理API ==========

@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    """获取所有提示词"""
    prompts = prompt_manager.get_all()
    return jsonify({"success": True, "data": prompts})

@app.route("/api/prompts", methods=["POST"])
def save_prompt():
    """保存提示词"""
    data = request.json
    success = prompt_manager.save(data["name"], data["content"])
    return jsonify({"success": success})

@app.route("/api/prompts/current", methods=["POST"])
def set_current_prompt():
    """设置当前提示词"""
    data = request.json
    success = prompt_manager.set_current(data["name"])
    return jsonify({"success": success})

# ========== 路径管理API ==========

@app.route("/api/paths", methods=["GET"])
def get_paths():
    """获取路径配置"""
    paths = file_manager.get_paths()
    is_valid, message = file_manager.validate_paths()
    return jsonify({
        "success": True,
        "data": {
            "input": paths.input_path,
            "output": paths.output_path,
            "is_valid": is_valid,
            "message": message
        }
    })

@app.route("/api/paths", methods=["POST"])
def set_paths():
    """设置路径"""
    data = request.json
    success = file_manager.set_paths(data["input"], data.get("output"))
    return jsonify({"success": success})

# ========== 文件处理API ==========

@app.route("/api/process", methods=["POST"])
def start_processing():
    """开始处理文件"""
    global processing_status
    
    # 检查是否已在运行
    if processing_status["is_running"]:
        return jsonify({"success": False, "error": "已有任务正在运行"}), 409
    
    # 验证路径
    is_valid, message = file_manager.validate_paths()
    if not is_valid:
        return jsonify({"success": False, "error": message}), 400
    
    # 获取当前配置
    current_model = model_manager.get_current()
    if not current_model:
        return jsonify({"success": False, "error": "未选择大模型"}), 400
    
    current_prompt = prompt_manager.get_current()
    if not current_prompt:
        return jsonify({"success": False, "error": "未选择提示词"}), 400
    
    # 扫描文件
    txt_files = file_manager.scan_input_files()
    if not txt_files:
        return jsonify({"success": False, "error": "未找到txt文件"}), 400
    
    # 重置状态
    processing_status = {
        "is_running": True,
        "progress": 0,
        "current_file": "",
        "total_files": len(txt_files),
        "processed_files": 0,
        "results": []
    }
    
    # 启动处理线程
    def process_task():
        provider = current_model["provider"]
        model_id = provider.models.get(current_model["model_key"])
        
        ai_processor = AIProcessor(provider.name, provider.api_key)
        file_processor = FileProcessor(file_manager.get_paths().input_path)
        
        for i, txt_file in enumerate(txt_files):
            processing_status["current_file"] = txt_file.name
            
            try:
                # 读取文件
                content = file_processor.read_file(txt_file)
                
                # AI处理
                response = ai_processor.process(content, model_id, current_prompt)
                
                # 保存结果
                output_path = file_manager.get_output_path(str(txt_file))
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(response)
                
                processing_status["results"].append({
                    "source": str(txt_file),
                    "output": str(output_path),
                    "success": True
                })
                
            except Exception as e:
                processing_status["results"].append({
                    "source": str(txt_file),
                    "output": None,
                    "success": False,
                    "error": str(e)
                })
            
            processing_status["processed_files"] = i + 1
            processing_status["progress"] = int((i + 1) / len(txt_files) * 100)
        
        processing_status["is_running"] = False
        processing_status["current_file"] = ""
    
    thread = threading.Thread(target=process_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "处理任务已启动",
        "total_files": len(txt_files)
    })

@app.route("/api/process/status", methods=["GET"])
def get_process_status():
    """获取处理状态"""
    return jsonify({"success": True, "data": processing_status})

@app.route("/api/process/cancel", methods=["POST"])
def cancel_processing():
    """取消处理"""
    global processing_status
    processing_status["is_running"] = False
    return jsonify({"success": True, "message": "已取消"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

---

## 实施步骤

### 第1步：备份现有代码
```bash
# 备份当前项目
copy ai_summary ai_summary_backup
```

### 第2步：创建新文件
按照上述代码创建以下文件：
1. `core/config_manager.py`
2. `managers/model_manager.py`
3. `managers/file_manager.py`
4. 更新 `app.py`

### 第3步：更新配置文件格式
将现有 `config.json` 转换为新格式：

旧格式：
```json
{
  "providers": [...],
  "custom_prompts": {...},
  "user_preferences": {...}
}
```

新格式：
```json
{
  "providers": [...],
  "current_provider": {},
  "custom_prompts": {...},
  "current_prompt": "",
  "file_paths": {"input": "", "output": ""},
  "trash": {...}
}
```

### 第4步：测试
1. 启动应用
2. 测试大模型管理（添加、修改、切换）
3. 测试提示词管理
4. 测试路径管理
5. 测试文件处理流程

---

## 文件变更清单

### 新增文件
- `core/config_manager.py` - 统一配置管理
- `managers/model_manager.py` - 大模型管理
- `managers/file_manager.py` - 文件路径管理

### 修改文件
- `app.py` - 简化重构
- `managers/prompt_manager.py` - 适配新的ConfigManager

### 删除文件（可选）
- `utils.py` - 功能被新的管理器替代
- `app/routes.py` - 功能合并到app.py

---

## 预期效果

重构后：
1. **代码结构清晰** - 每个管理器职责单一
2. **易于维护** - 修改某个功能只需改动对应的管理器
3. **配置统一** - 所有配置通过ConfigManager管理
4. **API简洁** - RESTful风格，前端调用方便

您确认这个重构计划后，我可以开始逐步实施。
