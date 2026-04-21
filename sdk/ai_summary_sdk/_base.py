# -*- coding: utf-8 -*-
"""基礎客户端 - 共享配置、错误处理和响应校验"""
import os
from typing import Any, TypeVar, Type

import httpx
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import (
    AISummarySDKError,
    ConnectionError,
    AuthenticationError,
    ValidationError,
    APIError,
    NotFoundError,
)
from ._retry import retry_with_backoff

T = TypeVar("T", bound=BaseModel)

ENV_BASE_URL = "AI_SUMMARY_BASE_URL"
ENV_API_KEY = "AI_SUMMARY_API_KEY"
DEFAULT_BASE_URL = "http://localhost:5000"


class BaseClientConfig:
    """客户端共享配置"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = (base_url or os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.environ.get(ENV_API_KEY, "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay


class BaseResourceGroup:
    """API 分组基类"""

    def __init__(self, client: httpx.Client | httpx.AsyncClient, config: BaseClientConfig):
        self._client = client
        self._config = config

    def _url(self, path: str) -> str:
        """构造完整 URL"""
        return f"{self._config.base_url}{path}"

    def _headers(self) -> dict:
        """构造请求头"""
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers


def _handle_response(response: httpx.Response) -> dict:
    """统一响应处理：将 HTTP 状态码转换为 SDK 异常

    Args:
        response: httpx 响应对象

    Returns:
        解析后的 JSON 字典

    Raises:
        NotFoundError: HTTP 404
        ValidationError: HTTP 400
        APIError: HTTP 4xx/5xx
    """
    if response.status_code == 200:
        return response.json()

    # 尝试解析错误响应体
    try:
        body = response.json()
        error_msg = body.get("error", body.get("detail", response.text))
        retryable = body.get("retryable", False)
    except Exception:
        error_msg = response.text
        retryable = False

    if response.status_code == 404:
        raise NotFoundError(message=error_msg)
    if response.status_code == 400:
        raise ValidationError(message=error_msg)
    if response.status_code == 401:
        raise AuthenticationError(message=error_msg)
    raise APIError(
        message=error_msg,
        status_code=response.status_code,
        retryable=retryable,
    )


def _validate_response(data: dict, model: Type[T]) -> T:
    """使用 Pydantic 模型校验响应数据

    Args:
        data: API 响应字典
        model: 目标 Pydantic 模型类

    Returns:
        校验后的模型实例

    Raises:
        ValidationError: 校验失败
    """
    try:
        return model.model_validate(data)
    except PydanticValidationError as e:
        raise ValidationError(
            message=f"响应校验失败: {e.error_count()} 个错误",
            errors=e.errors(),
        )
