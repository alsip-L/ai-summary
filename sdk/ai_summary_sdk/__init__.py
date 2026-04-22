# -*- coding: utf-8 -*-
"""AI Summary SDK - AI Summary 服务的 Python 客户端库"""

from .client import AISummaryClient
from .async_client import AsyncAISummaryClient
from .exceptions import (
    AISummarySDKError,
    SDKConnectionError,
    AuthenticationError,
    ValidationError,
    APIError,
    NotFoundError,
)
from . import models

# 向后兼容别名
ConnectionError = SDKConnectionError

__all__ = [
    "AISummaryClient",
    "AsyncAISummaryClient",
    "AISummarySDKError",
    "SDKConnectionError",
    "ConnectionError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "NotFoundError",
    "models",
]
__version__ = "0.1.0"
