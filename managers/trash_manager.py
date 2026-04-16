# -*- coding: utf-8 -*-
"""回收站管理模块"""

from typing import Dict, Optional, Any
from core.logger import get_logger
from core.config_manager import ConfigManager
from core.exceptions import TrashError

logger = get_logger()


class TrashManager:
    """回收站管理器
    
    管理已删除的提供商和提示词，支持恢复和永久删除。
    """
    
    def __init__(self):
        """初始化回收站管理器"""
        self.config = ConfigManager()
        logger.debug("回收站管理器初始化")
    
    def get_all(self) -> Dict[str, Any]:
        """获取回收站中的所有项目
        
        Returns:
            回收站数据字典
        """
        return self.config.get('trash', {})
    
    def get_providers(self) -> Dict[str, dict]:
        """获取回收站中的提供商
        
        Returns:
            提供商字典，键为提供商名称
        """
        trash = self.get_all()
        return trash.get('providers', {})
    
    def get_prompts(self) -> Dict[str, str]:
        """获取回收站中的提示词
        
        Returns:
            提示词字典，键为提示词名称
        """
        trash = self.get_all()
        return trash.get('custom_prompts', {})
    
    def move_provider_to_trash(self, name: str) -> bool:
        """将提供商移动到回收站

        Args:
            name: 提供商名称

        Returns:
            移动成功返回 True，否则返回 False
        """
        try:
            from managers.model_manager import ModelManager
            from dataclasses import asdict

            model_manager = ModelManager()
            provider = model_manager.get(name)

            if not provider:
                logger.warning(f"移动提供商到回收站失败，未找到: {name}")
                return False

            # 从提供商列表中删除
            if not model_manager.delete(name):
                return False

            # 添加到回收站 - 存储字典格式
            trash = self.get_all()
            if 'providers' not in trash:
                trash['providers'] = {}

            trash['providers'][name] = asdict(provider)
            self.config.set('trash', trash)

            logger.info(f"移动提供商到回收站: {name}")
            return self.config.save()

        except Exception as e:
            logger.error(f"移动提供商到回收站失败: {name}, {e}")
            return False
    
    def move_prompt_to_trash(self, name: str) -> bool:
        """将提示词移动到回收站
        
        Args:
            name: 提示词名称
            
        Returns:
            移动成功返回 True，否则返回 False
        """
        try:
            from managers.prompt_manager import PromptManager
            
            prompt_manager = PromptManager()
            prompt = prompt_manager.get(name)
            
            if not prompt:
                logger.warning(f"移动提示词到回收站失败，未找到: {name}")
                return False
            
            # 从提示词列表中删除
            if not prompt_manager.delete(name):
                return False
            
            # 添加到回收站
            trash = self.get_all()
            if 'custom_prompts' not in trash:
                trash['custom_prompts'] = {}
            
            trash['custom_prompts'][name] = prompt
            self.config.set('trash', trash)
            
            logger.info(f"移动提示词到回收站: {name}")
            return self.config.save()
            
        except Exception as e:
            logger.error(f"移动提示词到回收站失败: {name}, {e}")
            return False
    
    def restore_provider(self, name: str) -> bool:
        """从回收站恢复提供商

        Args:
            name: 提供商名称

        Returns:
            恢复成功返回 True，否则返回 False
        """
        try:
            trash = self.get_all()
            trash_providers = trash.get('providers', {})

            if name not in trash_providers:
                logger.warning(f"恢复提供商失败，回收站中未找到: {name}")
                return False

            # 恢复提供商 - 存储时是字典格式
            from managers.model_manager import ModelManager, ModelConfig

            provider = trash_providers[name]
            model_manager = ModelManager()

            # dict format (as stored by move_provider_to_trash)
            result = model_manager.save(ModelConfig(
                name=name,
                base_url=provider.get('base_url', ''),
                api_key=provider.get('api_key', ''),
                models=provider.get('models', {})
            ))

            if not result:
                return False

            # 从回收站删除
            del trash_providers[name]
            if not trash_providers:
                trash.pop('providers', None)

            self.config.set('trash', trash)

            logger.info(f"恢复提供商: {name}")
            return self.config.save()

        except Exception as e:
            logger.error(f"恢复提供商失败: {name}, {e}")
            return False
    
    def restore_prompt(self, name: str) -> bool:
        """从回收站恢复提示词
        
        Args:
            name: 提示词名称
            
        Returns:
            恢复成功返回 True，否则返回 False
        """
        try:
            trash = self.get_all()
            trash_prompts = trash.get('custom_prompts', {})
            
            if name not in trash_prompts:
                logger.warning(f"恢复提示词失败，回收站中未找到: {name}")
                return False
            
            # 恢复提示词
            content = trash_prompts[name]
            from managers.prompt_manager import PromptManager
            
            prompt_manager = PromptManager()
            result = prompt_manager.save(name, content)
            
            if not result:
                return False
            
            # 从回收站删除
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop('custom_prompts', None)
            
            self.config.set('trash', trash)
            
            logger.info(f"恢复提示词: {name}")
            return self.config.save()
            
        except Exception as e:
            logger.error(f"恢复提示词失败: {name}, {e}")
            return False
    
    def permanent_delete_provider(self, name: str) -> bool:
        """永久删除提供商
        
        Args:
            name: 提供商名称
            
        Returns:
            删除成功返回 True，否则返回 False
        """
        try:
            trash = self.get_all()
            trash_providers = trash.get('providers', {})
            
            if name not in trash_providers:
                logger.warning(f"永久删除提供商失败，回收站中未找到: {name}")
                return False
            
            # 永久删除
            del trash_providers[name]
            if not trash_providers:
                trash.pop('providers', None)
            
            self.config.set('trash', trash)
            
            logger.info(f"永久删除提供商: {name}")
            return self.config.save()
            
        except Exception as e:
            logger.error(f"永久删除提供商失败: {name}, {e}")
            return False
    
    def permanent_delete_prompt(self, name: str) -> bool:
        """永久删除提示词
        
        Args:
            name: 提示词名称
            
        Returns:
            删除成功返回 True，否则返回 False
        """
        try:
            trash = self.get_all()
            trash_prompts = trash.get('custom_prompts', {})
            
            if name not in trash_prompts:
                logger.warning(f"永久删除提示词失败，回收站中未找到: {name}")
                return False
            
            # 永久删除
            del trash_prompts[name]
            if not trash_prompts:
                trash.pop('custom_prompts', None)
            
            self.config.set('trash', trash)
            
            logger.info(f"永久删除提示词: {name}")
            return self.config.save()
            
        except Exception as e:
            logger.error(f"永久删除提示词失败: {name}, {e}")
            return False
    
    def clear(self) -> bool:
        """清空回收站
        
        Returns:
            清空成功返回 True，否则返回 False
        """
        try:
            self.config.delete('trash')
            logger.info("清空回收站")
            return self.config.save()
            
        except Exception as e:
            logger.error(f"清空回收站失败: {e}")
            return False
    
    def is_empty(self) -> bool:
        """检查回收站是否为空
        
        Returns:
            为空返回 True，否则返回 False
        """
        trash = self.get_all()
        return not trash


# 向后兼容的函数
def get_trash_items():
    """获取回收站项目（向后兼容）"""
    return TrashManager().get_all()


def move_provider_to_trash(name: str) -> bool:
    """移动提供商到回收站（向后兼容）"""
    return TrashManager().move_provider_to_trash(name)


def move_prompt_to_trash(name: str) -> bool:
    """移动提示词到回收站（向后兼容）"""
    return TrashManager().move_prompt_to_trash(name)


def restore_provider_from_trash(name: str) -> bool:
    """从回收站恢复提供商（向后兼容）"""
    return TrashManager().restore_provider(name)


def restore_prompt_from_trash(name: str) -> bool:
    """从回收站恢复提示词（向后兼容）"""
    return TrashManager().restore_prompt(name)


def permanent_delete_provider_from_trash(name: str) -> bool:
    """永久删除提供商（向后兼容）"""
    return TrashManager().permanent_delete_provider(name)


def permanent_delete_prompt_from_trash(name: str) -> bool:
    """永久删除提示词（向后兼容）"""
    return TrashManager().permanent_delete_prompt(name)
