# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.repositories.provider_repo import ProviderRepository
from core.result import ok, fail


class ProviderService:
    def __init__(self, db: Session):
        self._repo = ProviderRepository(db)

    def list_all(self) -> dict:
        providers = self._repo.get_all()
        return ok(providers=providers)

    def create(self, data: dict) -> dict:
        if not data.get("name") or not data.get("base_url"):
            return fail("名称和 URL 为必填项")
        if self._repo.save(data):
            return ok()
        return fail("保存失败")

    def delete(self, name: str) -> dict:
        if self._repo.soft_delete(name):
            return ok()
        return fail("删除失败")

    def get_api_key(self, name: str) -> dict:
        provider = self._repo.get_raw(name)
        if not provider:
            return fail("提供商不存在")
        api_key = provider.get("api_key", "")
        return ok(api_key=api_key)

    def update_api_key(self, name: str, api_key: str) -> dict:
        if self._repo.update_api_key(name, api_key):
            return ok()
        return fail("更新失败")

    def add_model(self, name: str, display_name: str, model_id: str, temperature: float = 0.7, frequency_penalty: float = 0.4, presence_penalty: float = 0.2) -> dict:
        if self._repo.add_model_variant(name, display_name, model_id, temperature, frequency_penalty, presence_penalty):
            return ok()
        return fail("添加失败")

    def delete_model(self, name: str, model_name: str) -> dict:
        if self._repo.delete_model(name, model_name):
            return ok()
        return fail("删除失败")
