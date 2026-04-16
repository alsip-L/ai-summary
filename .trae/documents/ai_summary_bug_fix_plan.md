# 问题修复计划

## 一、发现的问题

### 问题1: Config单例状态残留（test_core.py）
- **位置**: `tests/test_core.py`
- **现象**: 测试之间Config单例状态未正确隔离，导致`test_get_simple`和`test_get_nested`失败
- **原因**: `Config._config`类变量在测试间未被正确重置

### 问题2: test_managers导入错误
- **位置**: `tests/test_managers.py`
- **现象**: `from managers.provider_manager import ProviderManager` 导入失败
- **原因**: 实际模块名为`managers.model_manager`，不存在`managers.provider_manager`

---

## 二、修复步骤

### 步骤1: 修复 test_core.py
1. 在`setUp`中添加完整的单例重置
2. 在`tearDown`中确保所有类变量被重置
3. 需要重置的变量：
   - `Config._instance = None`
   - `Config._config = None`
   - `Config._loaded = False`
   - `ConfigManager._instance = None`
   - `ConfigManager._cache = None`
   - `ConfigManager._loaded = False`

### 步骤2: 修复 test_managers.py
1. 将`from managers.provider_manager import ProviderManager`改为`from managers.model_manager import ModelManager`
2. 更新测试类中使用ProviderManager的地方，改为使用ModelManager
3. 修复TrashManager测试中对ProviderManager的引用

### 步骤3: 验证修复
运行单元测试确认所有测试通过

---

## 三、修复代码

### 3.1 test_core.py 修复
```python
def setUp(self):
    # Reset singleton completely
    Config._instance = None
    Config._config = None
    Config._loaded = False
    ConfigManager._instance = None
    ConfigManager._cache = None
    ConfigManager._loaded = False

def tearDown(self):
    # Reset singleton completely
    Config._instance = None
    Config._config = None
    Config._loaded = False
    ConfigManager._instance = None
    ConfigManager._cache = None
    ConfigManager._loaded = False
```

### 3.2 test_managers.py 修复
- 导入改为: `from managers.model_manager import ModelManager`
- ProviderManager测试类改为使用ModelManager
