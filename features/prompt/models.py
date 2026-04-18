# -*- coding: utf-8 -*-
"""提示词配置模型"""

from pydantic import BaseModel


class PromptConfig(BaseModel):
    """提示词配置"""
    name: str
    content: str
