# -*- coding: utf-8 -*-
"""AI提供商服务模块

.. deprecated::
    此模块当前未被主流程使用，功能由 utils.py 中的 ProviderManager 提供。
    保留供未来架构迁移使用。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from core.config_manager import ConfigManager
from core.exceptions import ProviderError
from core.logger import get_logger

logger = get_logger()


@dataclass
class ProviderConfig:
    """AI提供商配置数据类"""
    name: str
    base_url: str
    api_key: str
    models: Dict[str, str]
    is_active: bool = True


class ProviderService:
    """AI提供商服务类

    统一管理所有AI提供商的配置（URL、Key、模型列表）
    """

    def __init__(self):
        self.config = ConfigManager()

    def get_all(self) -> Dict[str, ProviderConfig]:
        """获取所有AI提供商配置

        Returns:
            以提供商名称为键，ProviderConfig为值的字典
        """
        providers = self.config.get('providers', [])

        result = {}
        for p in providers:
            if p.get('is_active', True):
                try:
                    result[p['name']] = ProviderConfig(**p)
                except (TypeError, KeyError) as e:
                    logger.warning(f"跳过无效的提供商配置: {p}, 错误: {e}")
                    continue
        return result

    def get(self, name: str) -> Optional[ProviderConfig]:
        """获取指定AI提供商配置

        Args:
            name: 提供商名称

        Returns:
            ProviderConfig对象，如果不存在返回None
        """
        return self.get_all().get(name)

    def save(self, provider: ProviderConfig) -> bool:
        """保存AI提供商配置（新增或更新）

        Args:
            provider: 提供商配置

        Returns:
            是否保存成功
        """
        try:
            providers = self.config.get('providers', [])
            existing_index = -1

            for i, p in enumerate(providers):
                if p.get('name') == provider.name:
                    existing_index = i
                    break

            if existing_index >= 0:
                providers[existing_index] = asdict(provider)
            else:
                providers.append(asdict(provider))

            return self.config.set('providers', providers)
        except Exception as e:
            logger.error(f"保存提供商失败: {e}")
            return False

    def delete(self, name: str) -> bool:
        """从活跃列表中移除提供商（仅从 providers 列表删除，不操作回收站）

        注意：回收站写入由 TrashManager 统一负责，避免双重写入。

        Args:
            name: 提供商名称

        Returns:
            是否删除成功
        """
        try:
            providers = self.config.get('providers', [])
            new_providers = [p for p in providers if p.get('name') != name]

            if len(new_providers) == len(providers):
                return False

            return self.config.set('providers', new_providers)
        except Exception as e:
            logger.error(f"删除提供商失败: {e}")
            return False

    def restore(self, name: str) -> bool:
        """从回收站恢复提供商

        Args:
            name: 提供商名称

        Returns:
            是否恢复成功
        """
        try:
            trash = self.config.get('trash', {})
            trash_providers = trash.get('providers', {})

            if name not in trash_providers:
                return False

            provider = trash_providers[name]
            providers = self.config.get('providers', [])
            providers.append(provider)

            del trash_providers[name]
            self.config.set('providers', providers)
            self.config.set('trash', trash)
            return True
        except Exception as e:
            logger.error(f"恢复提供商失败: {e}")
            return False

    def permanent_delete(self, name: str) -> bool:
        """永久删除提供商

        Args:
            name: 提供商名称

        Returns:
            是否删除成功
        """
        try:
            trash = self.config.get('trash', {})
            trash_providers = trash.get('providers', {})

            if name in trash_providers:
                del trash_providers[name]
                return self.config.set('trash', trash)
            return False
        except Exception as e:
            logger.error(f"永久删除提供商失败: {e}")
            return False

    def update_api_key(self, name: str, api_key: str) -> bool:
        """更新指定提供商的API Key

        Args:
            name: 提供商名称
            api_key: 新的API Key

        Returns:
            是否更新成功
        """
        provider = self.get(name)
        if not provider:
            return False

        provider.api_key = api_key
        return self.save(provider)

    def add_model(self, provider_name: str, model_key: str, model_id: str) -> bool:
        """为提供商添加新的模型

        Args:
            provider_name: 提供商名称
            model_key: 模型显示名称
            model_id: 模型ID

        Returns:
            是否添加成功
        """
        provider = self.get(provider_name)
        if not provider:
            return False

        provider.models[model_key] = model_id
        return self.save(provider)

    def delete_model(self, provider_name: str, model_key: str) -> bool:
        """从提供商删除模型

        Args:
            provider_name: 提供商名称
            model_key: 模型显示名称

        Returns:
            是否删除成功
        """
        provider = self.get(provider_name)
        if not provider or model_key not in provider.models:
            return False

        del provider.models[model_key]
        return self.save(provider)

    def get_current(self) -> Optional[Dict[str, Any]]:
        """获取当前选中的提供商和模型

        Returns:
            包含provider和model_key的字典，如果没有设置返回None
        """
        current = self.config.get('current_provider', {})
        provider_name = current.get('provider')
        model_key = current.get('model')

        if not provider_name:
            providers = self.get_all()
            if providers:
                first_name = list(providers.keys())[0]
                first = providers[first_name]
                return {
                    'provider_name': first_name,
                    'provider': first,
                    'model_key': list(first.models.keys())[0] if first.models else None
                }
            return None

        provider = self.get(provider_name)
        if not provider:
            return None

        return {
            'provider_name': provider_name,
            'provider': provider,
            'model_key': model_key or (list(provider.models.keys())[0] if provider.models else None)
        }

    def set_current(self, provider_name: str, model_key: str = None) -> bool:
        """设置当前使用的提供商和模型

        Args:
            provider_name: 提供商名称
            model_key: 模型显示名称

        Returns:
            是否设置成功
        """
        return self.config.set('current_provider', {
            'provider': provider_name,
            'model': model_key
        })
