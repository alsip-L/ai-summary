# -*- coding: utf-8 -*-
"""提示词管理模块"""

from typing import Dict, Optional
from core.logger import get_logger
from core.config_manager import ConfigManager
from core.exceptions import ValidationError

logger = get_logger()


class PromptManager:
    """提示词管理器
    
    管理系统提示词的配置，包括添加、删除、修改、查询和当前选择。
    """
    
    def __init__(self):
        """初始化提示词管理器"""
        self.config = ConfigManager()
        logger.debug("提示词管理器初始化")
    
    def get_all(self) -> Dict[str, str]:
        """获取所有提示词
        
        Returns:
            提示词字典，键为提示词名称，值为提示词内容
        """
        prompts = self.config.get('custom_prompts', {})
        
        # 处理列表格式兼容性（旧版本可能使用列表存储长文本）
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
            提示词内容，如果未找到则返回 None
        """
        return self.get_all().get(name)
    
    def get_current(self) -> Optional[str]:
        """获取当前选中的提示词内容
        
        Returns:
            当前提示词内容，如果未设置则返回第一个提示词的内容
        """
        current_name = self.config.get('current_prompt', '')
        
        if current_name:
            content = self.get(current_name)
            if content:
                return content
        
        # 如果没有设置或设置的提示词不存在，返回第一个
        prompts = self.get_all()
        if prompts:
            return list(prompts.values())[0]
        
        return None
    
    def get_current_name(self) -> Optional[str]:
        """获取当前选中的提示词名称
        
        Returns:
            当前提示词名称，如果未设置则返回第一个提示词的名称
        """
        current_name = self.config.get('current_prompt', '')
        
        if current_name and current_name in self.get_all():
            return current_name
        
        # 如果没有设置或设置的提示词不存在，返回第一个
        prompts = self.get_all()
        if prompts:
            return list(prompts.keys())[0]
        
        return None
    
    def set_current(self, name: str) -> bool:
        """设置当前使用的提示词
        
        Args:
            name: 提示词名称
            
        Returns:
            设置成功返回 True，否则返回 False
        """
        if name not in self.get_all():
            logger.warning(f"设置当前提示词失败，未找到: {name}")
            return False
        
        return self.config.set('current_prompt', name)
    
    def exists(self, name: str) -> bool:
        """检查提示词是否存在
        
        Args:
            name: 提示词名称
            
        Returns:
            存在返回 True，否则返回 False
        """
        return name in self.get_all()
    
    def save(self, name: str, content: str) -> bool:
        """保存提示词
        
        如果提示词已存在则更新，否则创建新提示词。
        
        Args:
            name: 提示词名称
            content: 提示词内容
            
        Returns:
            保存成功返回 True，否则返回 False
            
        Raises:
            ValidationError: 当名称或内容为空时抛出
        """
        if not name or not name.strip():
            raise ValidationError("提示词名称不能为空")
        
        if not content:
            raise ValidationError("提示词内容不能为空")
        
        try:
            prompts = self.config.get('custom_prompts', {})
            
            # 检查是新建还是更新
            is_new = name not in prompts
            prompts[name] = content
            
            self.config.set('custom_prompts', prompts)
            
            if is_new:
                logger.info(f"创建提示词: {name}")
                # 如果是第一个提示词，自动设为当前
                if len(prompts) == 1:
                    self.set_current(name)
            else:
                logger.info(f"更新提示词: {name}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存提示词失败: {name}, {e}")
            return False
    
    def delete(self, name: str) -> bool:
        """删除提示词
        
        Args:
            name: 提示词名称
            
        Returns:
            删除成功返回 True，否则返回 False
        """
        try:
            prompts = self.config.get('custom_prompts', {})
            
            if name not in prompts:
                logger.warning(f"删除提示词失败，未找到: {name}")
                return False
            
            del prompts[name]
            self.config.set('custom_prompts', prompts)
            
            # 如果删除的是当前提示词，重置当前提示词
            current = self.config.get('current_prompt', '')
            if current == name:
                if prompts:
                    self.set_current(list(prompts.keys())[0])
                else:
                    self.config.set('current_prompt', '')
            
            logger.info(f"删除提示词: {name}")
            return True
            
        except Exception as e:
            logger.error(f"删除提示词失败: {name}, {e}")
            return False
    
    def get_default(self) -> Optional[str]:
        """获取默认提示词名称
        
        Returns:
            第一个提示词的名称，如果没有则返回 None
        """
        prompts = self.get_all()
        if prompts:
            return list(prompts.keys())[0]
        return None
    
    def validate(self, name: str, content: str) -> bool:
        """验证提示词
        
        Args:
            name: 提示词名称
            content: 提示词内容
            
        Returns:
            验证通过返回 True，否则抛出异常
            
        Raises:
            ValidationError: 当验证失败时抛出
        """
        if not name or not name.strip():
            raise ValidationError("提示词名称不能为空")
        
        if len(name) > 100:
            raise ValidationError("提示词名称不能超过 100 个字符")
        
        if not content:
            raise ValidationError("提示词内容不能为空")
        
        if len(content) > 100000:
            raise ValidationError("提示词内容不能超过 100000 个字符")
        
        return True


# 向后兼容的函数
def load_custom_prompts():
    """加载所有提示词（向后兼容）"""
    return PromptManager().get_all()


def save_custom_prompts(prompts):
    """保存所有提示词（向后兼容）"""
    config = ConfigManager()
    config.set('custom_prompts', prompts)
    return True


def delete_custom_prompt(prompt_name):
    """删除提示词（向后兼容）"""
    return PromptManager().delete(prompt_name)
