# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = Field(default=True, description="操作是否成功")
    message: str | None = Field(default=None, description="成功消息")

    model_config = {
        "json_schema_extra": {
            "examples": [{"success": True, "message": "操作成功"}]
        }
    }


class ErrorResponse(BaseModel):
    """通用错误响应"""
    success: bool = Field(default=False, description="操作是否成功")
    error: str = Field(description="错误信息")
    retryable: bool | None = Field(default=None, description="是否可重试")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"success": False, "error": "提供商不存在"},
                {"success": False, "error": "服务暂时不可用", "retryable": True},
            ]
        }
    }
