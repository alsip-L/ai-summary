# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.repositories.trash_repo import TrashRepository
from core.result import ok, fail


class TrashService:
    def __init__(self, db: Session):
        self._repo = TrashRepository(db)

    def get_all(self) -> dict:
        return self._repo.get_all()

    def restore_provider(self, name: str) -> dict:
        if self._repo.restore_provider(name):
            return ok()
        return fail("恢复失败")

    def restore_prompt(self, name: str) -> dict:
        if self._repo.restore_prompt(name):
            return ok()
        return fail("恢复失败")

    def permanent_delete_provider(self, name: str) -> dict:
        if self._repo.permanent_delete_provider(name):
            return ok()
        return fail("删除失败")

    def permanent_delete_prompt(self, name: str) -> dict:
        if self._repo.permanent_delete_prompt(name):
            return ok()
        return fail("删除失败")
