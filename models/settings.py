# -*- coding: utf-8 -*-
"""用户偏好和系统设置模型"""

from pydantic import BaseModel


class UserPreferences(BaseModel):
    """用户偏好"""
    selected_provider: str = ""
    selected_model: str = ""
    selected_prompt: str = ""
    directory_path: str = ""


class SystemSettings(BaseModel):
    """系统设置"""
    debug_level: str = "ERROR"
    flask_secret_key: str = "default-dev-secret-key-please-change-in-prod"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
