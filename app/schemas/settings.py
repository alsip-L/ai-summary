# -*- coding: utf-8 -*-
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
