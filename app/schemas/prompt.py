# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="提示词名称")
    content: str = Field(min_length=1, max_length=100000, description="提示词内容，作为 system prompt 发送")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "摘要生成",
                "content": "请对以下文本生成摘要，保留关键信息。",
            }]
        }
    }
