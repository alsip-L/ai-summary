# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.repositories.provider_repo import ProviderRepository


class ProviderService:
    def __init__(self, db: Session):
        self._repo = ProviderRepository(db)

    def list_all(self) -> dict:
        return self._repo.get_all()

    def create(self, data: dict) -> dict:
        try:
            if not data.get("name") or not data.get("base_url"):
                return {"success": False, "error": "名称和 URL 为必填项"}
            if self._repo.save(data):
                return {"success": True}
            return {"success": False, "error": "保存失败"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, name: str) -> dict:
        from app.repositories.trash_repo import TrashRepository
        trash_repo = TrashRepository(self._repo.db)
        if trash_repo.move_provider_to_trash(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}

    def update_api_key(self, name: str, api_key: str) -> dict:
        if self._repo.update_api_key(name, api_key):
            return {"success": True}
        return {"success": False, "error": "更新失败"}

    def add_model(self, name: str, display_name: str, model_id: str) -> dict:
        if self._repo.add_model_variant(name, display_name, model_id):
            return {"success": True}
        return {"success": False, "error": "添加失败"}

    def delete_model(self, name: str, model_name: str) -> dict:
        if self._repo.delete_model(name, model_name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
