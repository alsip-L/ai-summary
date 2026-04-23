# -*- coding: utf-8 -*-
from typing import Literal
from pydantic import BaseModel, Field


class PreferencesUpdate(BaseModel):
    selected_provider: str | None = Field(default=None, description="选中的提供商名称")
    selected_model: str | None = Field(default=None, description="选中的模型标识")
    selected_prompt: str | None = Field(default=None, description="选中的提示词名称")
    directory_path: str | None = Field(default=None, description="目录路径")
    api_key: str | None = Field(default=None, description="API Key")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "selected_provider": "openai",
                "selected_model": "gpt-4",
                "selected_prompt": "摘要生成",
                "directory_path": "C:/data/texts",
            }]
        }
    }


class SystemSettingsUpdate(BaseModel):
    debug_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = Field(default=None, description="日志级别")
    secret_key: str | None = Field(default=None, min_length=8, description="密钥")
    host: str | None = Field(default=None, description="监听地址")
    port: int | None = Field(default=None, ge=1, le=65535, description="监听端口")
    debug: bool | None = Field(default=None, description="调试模式")
    admin_username: str | None = Field(default=None, max_length=50, description="管理员用户名")
    admin_password: str | None = Field(default=None, min_length=4, max_length=100, description="管理员密码")
    allowed_paths: list[str] | None = Field(default=None, description="允许的文件路径白名单")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "debug_level": "ERROR",
                "port": 5000,
            }]
        }
    }
