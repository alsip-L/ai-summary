from typing import Dict, Optional
from dataclasses import dataclass, asdict
from core.config_manager import ConfigManager


@dataclass
class ModelConfig:
    """大模型配置数据类
    
    Attributes:
        name: 提供商显示名称，如"阿里通义"
        base_url: API基础地址
        api_key: API密钥
        models: 模型列表，键为显示名，值为模型ID
        is_active: 是否启用
    """
    name: str
    base_url: str
    api_key: str
    models: Dict[str, str]
    is_active: bool = True


class ModelManager:
    """大模型管理器
    
    职责：统一管理所有大模型的配置（URL、Key、模型列表）
    
    使用示例：
        manager = ModelManager()
        
        # 添加新的大模型
        manager.save(ModelConfig(
            name="DeepSeek",
            base_url="https://api.deepseek.com",
            api_key="sk-xxx",
            models={"DeepSeek Chat": "deepseek-chat"}
        ))
        
        # 获取所有模型
        models = manager.get_all()
        
        # 获取当前选中的模型
        current = manager.get_current()
        
        # 切换当前模型
        manager.set_current("DeepSeek", "DeepSeek Chat")
        
        # 更新API Key
        manager.update_api_key("DeepSeek", "sk-new-key")
    """
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_all(self) -> Dict[str, ModelConfig]:
        """获取所有大模型配置
        
        Returns:
            以模型名称为键，ModelConfig为值的字典
        """
        providers = self.config.get("providers", [])
        return {
            p["name"]: ModelConfig(**p)
            for p in providers
            if p.get("is_active", True)
        }
    
    def get(self, name: str) -> Optional[ModelConfig]:
        """获取指定大模型配置
        
        Args:
            name: 大模型名称
            
        Returns:
            ModelConfig对象，如果不存在返回None
        """
        return self.get_all().get(name)
    
    def save(self, model: ModelConfig) -> bool:
        """保存大模型配置（新增或更新）
        
        Args:
            model: 大模型配置
            
        Returns:
            是否保存成功
        """
        providers = self.config.get("providers", [])
        
        # 查找并更新或添加
        for i, p in enumerate(providers):
            if p["name"] == model.name:
                providers[i] = asdict(model)
                break
        else:
            providers.append(asdict(model))
        
        return self.config.set("providers", providers)
    
    def delete(self, name: str) -> bool:
        """删除大模型（软删除，移到回收站）

        Args:
            name: 大模型名称

        Returns:
            是否删除成功
        """
        model = self.get(name)
        if not model:
            return False

        # 移到回收站 - 存储字典格式而非 ModelConfig
        trash = self.config.get("trash", {})
        if 'providers' not in trash:
            trash['providers'] = {}
        trash['providers'][name] = asdict(model)
        self.config.set("trash", trash)

        # 从活跃列表移除
        providers = self.config.get("providers", [])
        providers = [p for p in providers if p.get("name") != name]
        return self.config.set("providers", providers)
    
    def update_api_key(self, name: str, api_key: str) -> bool:
        """更新指定大模型的API Key
        
        Args:
            name: 大模型名称
            api_key: 新的API Key
            
        Returns:
            是否更新成功
        """
        model = self.get(name)
        if not model:
            return False
        
        model.api_key = api_key
        return self.save(model)
    
    def update_base_url(self, name: str, base_url: str) -> bool:
        """更新指定大模型的Base URL
        
        Args:
            name: 大模型名称
            base_url: 新的Base URL
            
        Returns:
            是否更新成功
        """
        model = self.get(name)
        if not model:
            return False
        
        model.base_url = base_url
        return self.save(model)
    
    def add_model_variant(self, provider_name: str, model_key: str, model_id: str) -> bool:
        """为大模型添加新的模型变体
        
        Args:
            provider_name: 大模型名称
            model_key: 模型显示名称
            model_id: 模型ID
            
        Returns:
            是否添加成功
        """
        model = self.get(provider_name)
        if not model:
            return False
        
        model.models[model_key] = model_id
        return self.save(model)
    
    def get_current(self) -> Optional[Dict]:
        """获取当前选中的大模型和模型
        
        Returns:
            包含provider和model_key的字典，如果没有设置返回None
        """
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
        """设置当前使用的大模型和模型
        
        Args:
            provider_name: 大模型名称
            model_key: 模型显示名称
            
        Returns:
            是否设置成功
        """
        return self.config.set("current_provider", {
            "provider": provider_name,
            "model": model_key
        })
