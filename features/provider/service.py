# -*- coding: utf-8 -*-
"""提供商业务逻辑层"""

from .models import ProviderConfig
from .repository import ProviderRepository
from features.trash.repository import TrashRepository


class ProviderService:
    """提供商服务：封装 CRUD 和删除移入回收站的业务逻辑"""

    def __init__(self):
        self._repo = ProviderRepository()
        self._trash_repo = TrashRepository()

    def list_all(self) -> dict:
        """列出所有活跃提供商"""
        return self._repo.get_all_as_dict()

    def create(self, data: dict) -> dict:
        """创建提供商"""
        try:
            provider = ProviderConfig(**data)
        except Exception as e:
            return {"success": False, "error": str(e)}
        if self._repo.save(provider):
            return {"success": True}
        return {"success": False, "error": "保存失败"}

    def delete(self, name: str) -> dict:
        """删除提供商（移入回收站）"""
        if self._trash_repo.move_provider_to_trash(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}

    def update_api_key(self, name: str, api_key: str) -> dict:
        """更新 API Key"""
        if self._repo.update_api_key(name, api_key):
            return {"success": True}
        return {"success": False, "error": "更新失败"}

    def add_model(self, name: str, display_name: str, model_id: str) -> dict:
        """添加模型变体"""
        if self._repo.add_model_variant(name, display_name, model_id):
            return {"success": True}
        return {"success": False, "error": "添加失败"}

    def delete_model(self, name: str, model_name: str) -> dict:
        """删除模型变体"""
        if self._repo.delete_model(name, model_name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
