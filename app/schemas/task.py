# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class TaskStartRequest(BaseModel):
    provider: str = Field(min_length=1, description="提供商名称")
    model: str = Field(min_length=1, description="模型标识")
    api_key: str = Field(min_length=1, description="API Key")
    prompt: str = Field(min_length=1, description="提示词名称")
    directory: str = Field(min_length=1, description="待处理目录路径")
    skip_existing: bool = Field(default=False, description="是否跳过已处理的文件")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "sk-xxx",
                "prompt": "摘要生成",
                "directory": "C:/data/texts",
                "skip_existing": True,
            }]
        }
    }


class RetryFailedRequest(BaseModel):
    provider: str = Field(min_length=1, description="提供商名称")
    model: str = Field(min_length=1, description="模型标识")
    api_key: str = Field(min_length=1, description="API Key")
    prompt: str = Field(min_length=1, description="提示词名称")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "sk-xxx",
                "prompt": "摘要生成",
            }]
        }
    }
