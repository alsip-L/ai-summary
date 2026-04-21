# -*- coding: utf-8 -*-
"""SDK 异常层次定义"""


class AISummarySDKError(Exception):
    """SDK 基础异常，所有 SDK 异常的基类"""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class ConnectionError(AISummarySDKError):
    """连接错误 - 服务不可达或网络异常"""

    def __init__(self, message: str = "", *, url: str = ""):
        self.url = url
        super().__init__(message or f"无法连接到服务: {url}")


class AuthenticationError(AISummarySDKError):
    """认证错误 - API Key 无效或缺失"""

    def __init__(self, message: str = "认证失败，请检查 API Key"):
        super().__init__(message)


class ValidationError(AISummarySDKError):
    """验证错误 - 请求参数不合法或响应校验失败"""

    def __init__(self, message: str = "", *, field: str = "", errors: list | None = None):
        self.field = field
        self.errors = errors or []
        super().__init__(message or f"参数验证失败: {field}")


class APIError(AISummarySDKError):
    """API 错误 - 服务端返回非 2xx 状态码"""

    def __init__(self, message: str = "", *, status_code: int = 0, retryable: bool = False):
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message or f"API 错误 (HTTP {status_code})")


class NotFoundError(APIError):
    """资源不存在错误 (HTTP 404)"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(message, status_code=404)
