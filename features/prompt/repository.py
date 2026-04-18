# -*- coding: utf-8 -*-
"""提示词数据访问层"""

from .models import PromptConfig
from core.config import ConfigManager
from core.errors import ValidationError
from core.log import get_logger

logger = get_logger()


class PromptRepository:
    def __init__(self, config: ConfigManager = None):
        self._config = config or ConfigManager()

    def get_all(self) -> dict[str, PromptConfig]:
        prompts = self._config.get("custom_prompts", {})
        processed = {}
        for name, content in prompts.items():
            value = "\n".join(content) if isinstance(content, list) else content
            processed[name] = PromptConfig(name=name, content=value)
        return processed

    def get(self, name: str) -> PromptConfig | None:
        return self.get_all().get(name)

    def save(self, prompt: PromptConfig) -> bool:
        if not prompt.name or not prompt.name.strip():
            raise ValidationError("提示词名称不能为空")
        if not prompt.content:
            raise ValidationError("提示词内容不能为空")
        try:
            prompts = self._config.get("custom_prompts", {})
            is_new = prompt.name not in prompts
            prompts[prompt.name] = prompt.content
            self._config.set("custom_prompts", prompts)
            if is_new and len(prompts) == 1:
                self._config.set("current_prompt", prompt.name)
            return True
        except Exception as e:
            logger.error(f"保存提示词失败: {prompt.name}, {e}")
            return False

    def delete(self, name: str) -> bool:
        try:
            prompts = self._config.get("custom_prompts", {})
            if name not in prompts:
                return False
            del prompts[name]
            self._config.set("custom_prompts", prompts)
            current = self._config.get("current_prompt", "")
            if current == name:
                self._config.set("current_prompt", list(prompts.keys())[0] if prompts else "")
            return True
        except Exception as e:
            logger.error(f"删除提示词失败: {name}, {e}")
            return False
