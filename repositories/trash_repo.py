# -*- coding: utf-8 -*-
"""回收站数据访问层"""

from models.provider import ProviderConfig
from models.prompt import PromptConfig
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()


class TrashRepository:
    def __init__(self, config: ConfigManager):
        self._config = config
        self._provider_repo = ProviderRepository(config)
        self._prompt_repo = PromptRepository(config)

    def get_all(self) -> dict:
        return self._config.get("trash", {})

    def move_provider_to_trash(self, name: str) -> bool:
        try:
            provider = self._provider_repo.get(name)
            if not provider:
                return False
            # 从活跃列表删除（通过 ProviderRepository 封装）
            if not self._provider_repo.delete(name):
                return False
            # 移入回收站
            trash = self.get_all()
            trash.setdefault("providers", {})[name] = provider.model_dump()
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"移动提供商到回收站失败: {name}, {e}")
            return False

    def move_prompt_to_trash(self, name: str) -> bool:
        try:
            prompt = self._prompt_repo.get(name)
            if not prompt:
                return False
            if not self._prompt_repo.delete(name):
                return False
            trash = self.get_all()
            trash.setdefault("custom_prompts", {})[name] = prompt.content
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"移动提示词到回收站失败: {name}, {e}")
            return False

    def restore_provider(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False
            provider_data = trash_providers[name]
            provider = ProviderConfig(**provider_data)
            if not self._provider_repo.save(provider):
                return False
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"恢复提供商失败: {name}, {e}")
            return False

    def restore_prompt(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False
            content = trash_prompts[name]
            if not self._prompt_repo.save(PromptConfig(name=name, content=content)):
                return False
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"恢复提示词失败: {name}, {e}")
            return False

    def permanent_delete_provider(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_providers = trash.get("providers", {})
            if name not in trash_providers:
                return False
            del trash_providers[name]
            if not trash_providers:
                trash.pop("providers", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"永久删除提供商失败: {name}, {e}")
            return False

    def permanent_delete_prompt(self, name: str) -> bool:
        try:
            trash = self.get_all()
            trash_prompts = trash.get("custom_prompts", {})
            if name not in trash_prompts:
                return False
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop("custom_prompts", None)
            self._config.set("trash", trash)
            return self._config.save()
        except Exception as e:
            logger.error(f"永久删除提示词失败: {name}, {e}")
            return False
