# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="提供商名称，如 openai、deepseek")
    base_url: str = Field(min_length=1, pattern=r"^https?://", description="API Base URL，须以 http:// 或 https:// 开头")
    api_key: str = Field(default="", description="API Key，可选")
    models: dict[str, str] = Field(default_factory=dict, description="模型映射 {显示名: 模型ID}")
    is_active: bool = Field(default=True, description="是否启用")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-xxx",
                "models": {"GPT-4": "gpt-4", "GPT-3.5": "gpt-3.5-turbo"},
                "is_active": True,
            }]
        }
    }


class ApiKeyUpdate(BaseModel):
    api_key: str = Field(min_length=1, description="新的 API Key")

    model_config = {
        "json_schema_extra": {
            "examples": [{"api_key": "sk-new-key"}]
        }
    }


class ModelCreate(BaseModel):
    display_name: str = Field(description="模型显示名称，如 GPT-4")
    model_id: str = Field(description="模型标识，如 gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度，0-2")
    frequency_penalty: float = Field(default=0.4, ge=-2.0, le=2.0, description="频率惩罚，-2到2")
    presence_penalty: float = Field(default=0.2, ge=-2.0, le=2.0, description="存在惩罚，-2到2")

    model_config = {
        "json_schema_extra": {
            "examples": [{"display_name": "GPT-4", "model_id": "gpt-4", "temperature": 0.7, "frequency_penalty": 0.4, "presence_penalty": 0.2}]
        }
    }
