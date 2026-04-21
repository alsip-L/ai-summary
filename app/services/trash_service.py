# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.repositories.trash_repo import TrashRepository


class TrashService:
    def __init__(self, db: Session):
        self._repo = TrashRepository(db)

    def get_all(self) -> dict:
        return self._repo.get_all()

    def restore_provider(self, name: str) -> dict:
        if self._repo.restore_provider(name):
            return {"success": True}
        return {"success": False, "error": "恢复失败"}

    def restore_prompt(self, name: str) -> dict:
        if self._repo.restore_prompt(name):
            return {"success": True}
        return {"success": False, "error": "恢复失败"}

    def permanent_delete_provider(self, name: str) -> dict:
        if self._repo.permanent_delete_provider(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}

    def permanent_delete_prompt(self, name: str) -> dict:
        if self._repo.permanent_delete_prompt(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
