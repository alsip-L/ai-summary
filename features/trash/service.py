# -*- coding: utf-8 -*-
"""回收站业务逻辑层"""

from .repository import TrashRepository
from core.log import get_logger

logger = get_logger()


class TrashService:
    """回收站服务：查看、恢复、永久删除"""

    def __init__(self):
        self._repo = TrashRepository()

    def get_all(self) -> dict:
        """获取回收站全部内容"""
        return self._repo.get_all()

    def restore_provider(self, name: str) -> dict:
        """恢复提供商"""
        if self._repo.restore_provider(name):
            return {"success": True}
        return {"success": False, "error": "恢复失败"}

    def restore_prompt(self, name: str) -> dict:
        """恢复提示词"""
        if self._repo.restore_prompt(name):
            return {"success": True}
        return {"success": False, "error": "恢复失败"}

    def permanent_delete_provider(self, name: str) -> dict:
        """永久删除提供商"""
        if self._repo.permanent_delete_provider(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}

    def permanent_delete_prompt(self, name: str) -> dict:
        """永久删除提示词"""
        if self._repo.permanent_delete_prompt(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
