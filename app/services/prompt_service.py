# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.services.prompt_repo import PromptRepository


class PromptService:
    def __init__(self, db: Session):
        self._repo = PromptRepository(db)

    def list_all(self) -> dict:
        return self._repo.get_all()

    def create(self, data: dict) -> dict:
        name = data.get("name", "")
        content = data.get("content", "")
        if not name or not content:
            return {"success": False, "error": "名称和内容为必填项"}
        if self._repo.save(name, content):
            return {"success": True}
        return {"success": False, "error": "保存失败"}

    def delete(self, name: str) -> dict:
        from app.services.trash_repo import TrashRepository
        trash_repo = TrashRepository(self._repo._db)
        if trash_repo.move_prompt_to_trash(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
