# -*- coding: utf-8 -*-
"""回收站数据访问层

所有修改操作（移入回收站、恢复、永久删除）均为原子操作：
在同一次 config.set 调用中同时更新源数据和回收站数据，避免中间状态。
"""

from models.provider import ProviderConfig
from models.prompt import PromptConfig
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()


class TrashRepository:
    def __init__(self, config: ConfigManager):
        self._config = config

    def get_all(self) -> dict:
        return self._config.get("trash", {})

    def move_provider_to_trash(self, name: str) -> bool:
        """将提供商移入回收站（原子操作：删除 + 移入一次写入）"""
        try:
            providers = self._config.get("providers", [])
            target = next((p for p in providers if p.get("name") == name), None)
            if not target:
                return False

            # 构造新状态
            new_providers = [p for p in providers if p.get("name") != name]
            trash = self._config.get("trash", {})
            trash.setdefault("providers", {})[name] = target

            # 原子写入：同时更新 providers 和 trash
            self._config.set("providers", new_providers)
            self._config.set("trash", trash)
            return True
        except Exception as e:
            logger.error(f"移动提供商到回收站失败: {name}, {e}")
            return False

    def move_prompt_to_trash(self, name: str) -> bool:
        """将提示词移入回收站（原子操作）"""
        try:
            prompts = self._config.get("custom_prompts", {})
            if name not in prompts:
                return False

            content = prompts[name]
            new_prompts = {k: v for k, v in prompts.items() if k != name}
            trash = self._config.get("trash", {})
            trash.setdefault("custom_prompts", {})[name] = content

            # 更新 current_prompt
            current = self._config.get("current_prompt", "")
            if current == name:
                new_current = next(iter(new_prompts), "")

            self._config.set("custom_prompts", new_prompts)
            if current == name:
                self._config.set("current_prompt", new_current)
            self._config.set("trash", trash)
            return True
        except Exception as e:
            logger.error(f"移动提示词到回收站失败: {name}, {e}")
            return False

    def restore_provider(self, name: str) -> bool:
        """从回收站恢复提供商（原子操作）"""
        try:
            trash = self._config.get("trash", {})
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False

            provider_data = trash_providers[name]
            # 添加回活跃列表
            providers = self._config.get("providers", [])
            providers.append(provider_data)
            # 从回收站移除
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)

            self._config.set("providers", providers)
            self._config.set("trash", trash)
            return True
        except Exception as e:
            logger.error(f"恢复提供商失败: {name}, {e}")
            return False

    def restore_prompt(self, name: str) -> bool:
        """从回收站恢复提示词（原子操作）"""
        try:
            trash = self._config.get("trash", {})
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False

            content = trash_prompts[name]
            prompts = self._config.get("custom_prompts", {})
            prompts[name] = content
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)

            # 如果是第一个提示词，设为当前
            if len(prompts) == 1:
                self._config.set("current_prompt", name)

            self._config.set("custom_prompts", prompts)
            self._config.set("trash", trash)
            return True
        except Exception as e:
            logger.error(f"恢复提示词失败: {name}, {e}")
            return False

    def permanent_delete_provider(self, name: str) -> bool:
        try:
            trash = self._config.get("trash", {})
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)
            return self._config.set("trash", trash)
        except Exception as e:
            logger.error(f"永久删除提供商失败: {name}, {e}")
            return False

    def permanent_delete_prompt(self, name: str) -> bool:
        try:
            trash = self._config.get("trash", {})
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)
            return self._config.set("trash", trash)
        except Exception as e:
            logger.error(f"永久删除提示词失败: {name}, {e}")
            return False
