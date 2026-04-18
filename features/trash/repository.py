# -*- coding: utf-8 -*-
"""回收站数据访问层

所有修改操作（移入回收站、恢复、永久删除）均为原子操作：
通过 config.set_batch 在一次锁 + 一次磁盘写入中同时更新源数据和回收站数据，
避免中间状态。
"""

from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()


class TrashRepository:
    def __init__(self, config: ConfigManager = None):
        self._config = config or ConfigManager()

    def get_all(self) -> dict:
        return self._config.get("trash", {})

    def move_provider_to_trash(self, name: str) -> bool:
        """将提供商移入回收站（原子操作：一次 set_batch 同时更新 providers 和 trash）"""
        try:
            providers = self._config.get("providers", [])
            target = next((p for p in providers if p.get("name") == name), None)
            if not target:
                return False

            new_providers = [p for p in providers if p.get("name") != name]
            trash = self._config.get("trash", {})
            trash.setdefault("providers", {})[name] = target

            return self._config.set_batch({"providers": new_providers, "trash": trash})
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

            updates = {"custom_prompts": new_prompts, "trash": trash}

            current = self._config.get("current_prompt", "")
            if current == name:
                updates["current_prompt"] = next(iter(new_prompts), "")

            return self._config.set_batch(updates)
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
            providers = self._config.get("providers", [])
            providers.append(provider_data)
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)

            return self._config.set_batch({"providers": providers, "trash": trash})
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

            updates = {"custom_prompts": prompts, "trash": trash}
            if len(prompts) == 1:
                updates["current_prompt"] = name

            return self._config.set_batch(updates)
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
