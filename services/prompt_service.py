# -*- coding: utf-8 -*-
"""提示词服务模块"""

from typing import Dict, Optional
from core.config_manager import ConfigManager
from core.logger import get_logger

logger = get_logger()


class PromptService:
    """提示词服务类

    统一管理所有提示词配置
    """

    def __init__(self):
        self.config = ConfigManager()

    def get_all(self) -> Dict[str, str]:
        """获取所有提示词

        Returns:
            提示词字典，键为名称，值为内容
        """
        prompts = self.config.get('custom_prompts', {})

        processed_prompts = {}
        for name, content in prompts.items():
            if isinstance(content, list):
                processed_prompts[name] = '\n'.join(content)
            else:
                processed_prompts[name] = content

        return processed_prompts

    def get(self, name: str) -> Optional[str]:
        """获取指定提示词

        Args:
            name: 提示词名称

        Returns:
            提示词内容，如果不存在返回None
        """
        prompts = self.get_all()
        return prompts.get(name)

    def save(self, name: str, content: str) -> bool:
        """保存提示词（新增或更新）

        Args:
            name: 提示词名称
            content: 提示词内容

        Returns:
            是否保存成功
        """
        try:
            prompts = self.config.get('custom_prompts', {})
            prompts[name] = content
            return self.config.set('custom_prompts', prompts)
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
            return False

    def delete(self, name: str) -> bool:
        """删除提示词（软删除，移到回收站）

        Args:
            name: 提示词名称

        Returns:
            是否删除成功
        """
        content = self.get(name)
        if content is None:
            return False

        try:
            trash = self.config.get('trash', {})
            if 'custom_prompts' not in trash:
                trash['custom_prompts'] = {}
            trash['custom_prompts'][name] = content
            self.config.set('trash', trash)

            prompts = self.config.get('custom_prompts', {})
            if name in prompts:
                del prompts[name]
            return self.config.set('custom_prompts', prompts)
        except Exception as e:
            logger.error(f"删除提示词失败: {e}")
            return False

    def restore(self, name: str) -> bool:
        """从回收站恢复提示词

        Args:
            name: 提示词名称

        Returns:
            是否恢复成功
        """
        try:
            trash = self.config.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})

            if name not in trash_prompts:
                return False

            prompts = self.config.get('custom_prompts', {})
            prompts[name] = trash_prompts[name]
            del trash_prompts[name]

            self.config.set('custom_prompts', prompts)
            self.config.set('trash', trash)
            return True
        except Exception as e:
            logger.error(f"恢复提示词失败: {e}")
            return False

    def permanent_delete(self, name: str) -> bool:
        """永久删除提示词

        Args:
            name: 提示词名称

        Returns:
            是否删除成功
        """
        try:
            trash = self.config.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})

            if name in trash_prompts:
                del trash_prompts[name]
                return self.config.set('trash', trash)
            return False
        except Exception as e:
            logger.error(f"永久删除提示词失败: {e}")
            return False

    def get_trash_items(self) -> Dict[str, str]:
        """获取回收站中的提示词

        Returns:
            回收站中的提示词字典
        """
        trash = self.config.get('trash', {})
        return trash.get('custom_prompts', {})

    def get_current(self) -> Optional[str]:
        """获取当前选中的提示词

        Returns:
            当前提示词名称，如果没有设置返回None
        """
        return self.config.get('current_prompt')

    def set_current(self, name: str) -> bool:
        """设置当前使用的提示词

        Args:
            name: 提示词名称

        Returns:
            是否设置成功
        """
        return self.config.set('current_prompt', name)
