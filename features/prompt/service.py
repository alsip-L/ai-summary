# -*- coding: utf-8 -*-
"""提示词业务逻辑层"""

from .models import PromptConfig
from .repository import PromptRepository
from features.trash.repository import TrashRepository
from core.log import get_logger

logger = get_logger()


class PromptService:
    """提示词服务：封装 CRUD 和删除移入回收站的业务逻辑"""

    def __init__(self):
        self._repo = PromptRepository()
        self._trash_repo = TrashRepository()

    def list_all(self) -> dict:
        """列出所有提示词"""
        prompts = self._repo.get_all()
        return {name: p.content for name, p in prompts.items()}

    def create(self, data: dict) -> dict:
        """创建提示词"""
        prompt = PromptConfig(name=data.get("name", ""), content=data.get("content", ""))
        if self._repo.save(prompt):
            return {"success": True}
        return {"success": False, "error": "保存失败"}

    def delete(self, name: str) -> dict:
        """删除提示词（移入回收站）"""
        if self._trash_repo.move_prompt_to_trash(name):
            return {"success": True}
        return {"success": False, "error": "删除失败"}
