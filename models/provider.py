# -*- coding: utf-8 -*-
"""AI 提供商配置模型"""

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """AI 提供商配置"""
    name: str
    base_url: str
    api_key: str = Field(repr=False)
    models: dict[str, str] = Field(default_factory=dict)   # {display_name: model_id}
    is_active: bool = True
