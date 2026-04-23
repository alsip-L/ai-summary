# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.repositories.prompt_repo import PromptRepository
from core.result import ok, fail


class PromptService:
    def __init__(self, db: Session):
        self._repo = PromptRepository(db)

    def list_all(self) -> dict:
        return self._repo.get_all()

    def create(self, data: dict) -> dict:
        name = data.get("name", "")
        content = data.get("content", "")
        if not name or not content:
            return fail("名称和内容为必填项")
        if self._repo.save(name, content):
            return ok()
        return fail("保存失败")

    def delete(self, name: str) -> dict:
        if self._repo.soft_delete(name):
            return ok()
        return fail("删除失败")
