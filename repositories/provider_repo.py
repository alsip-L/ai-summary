# -*- coding: utf-8 -*-
"""提供商数据访问层"""

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
