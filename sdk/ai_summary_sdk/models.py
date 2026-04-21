# -*- coding: utf-8 -*-
"""SDK 请求/响应 Pydantic 模型定义"""
from pydantic import BaseModel, Field


# === 请求模型 ===

class ProviderCreate(BaseModel):
    name: str = Field(description="提供商名称")
    base_url: str = Field(description="API Base URL")
    api_key: str = Field(description="API Key")
    models: dict[str, str] = Field(default_factory=dict, description="模型映射")
    is_active: bool = Field(default=True, description="是否启用")


class ApiKeyUpdate(BaseModel):
    api_key: str = Field(description="新的 API Key")


class ModelCreate(BaseModel):
    display_name: str = Field(description="模型显示名称")
    model_id: str = Field(description="模型标识")


class PromptCreate(BaseModel):
    name: str = Field(description="提示词名称")
    content: str = Field(description="提示词内容")


class TaskStartRequest(BaseModel):
    provider: str = Field(description="提供商名称")
    model: str = Field(description="模型标识")
    api_key: str = Field(description="API Key")
    prompt: str = Field(description="提示词名称")
    directory: str = Field(description="待处理目录路径")
    skip_existing: bool = Field(default=False, description="是否跳过已处理文件")


class RetryFailedRequest(BaseModel):
    provider: str = Field(description="提供商名称")
    model: str = Field(description="模型标识")
    api_key: str = Field(description="API Key")
    prompt: str = Field(description="提示词名称")


class PreferencesUpdate(BaseModel):
    selected_provider: str | None = Field(default=None, description="选中的提供商")
    selected_model: str | None = Field(default=None, description="选中的模型")
    selected_prompt: str | None = Field(default=None, description="选中的提示词")
    directory_path: str | None = Field(default=None, description="目录路径")
    api_key: str | None = Field(default=None, description="API Key")


# === 响应模型 ===

class SuccessResponse(BaseModel):
    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    retryable: bool | None = None


class ProviderInfo(BaseModel):
    """提供商信息（从 API 响应中解析）"""
    name: str
    base_url: str
    models: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True


class PromptInfo(BaseModel):
    """提示词信息"""
    name: str
    content: str


class TaskStatus(BaseModel):
    """任务状态"""
    status: str = Field(description="任务状态: idle/processing/completed/error/cancelled")
    total: int = Field(default=0, description="总文件数")
    processed: int = Field(default=0, description="已处理数")
    progress: int = Field(default=0, description="进度百分比")
    current_file: str | None = Field(default=None, description="当前处理文件")
    results: list = Field(default_factory=list, description="处理结果列表")
