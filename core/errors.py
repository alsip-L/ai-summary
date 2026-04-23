# -*- coding: utf-8 -*-
"""自定义异常模块"""


class AISummaryException(Exception):
    """AI Summary 基础异常类"""
    def __init__(self, message: str = "", cause: Exception = None):
        super().__init__(message)
        self.message = message
        self.cause = cause
        # 使用 Python 标准异常链机制，使 traceback 和调试工具能显示完整异常链
        if cause is not None:
            self.__cause__ = cause

    def __str__(self):
        if self.cause:
            return f"{self.message} (原因: {type(self.cause).__name__}: {str(self.cause)})"
        return self.message


class RetryableError(AISummaryException):
    """可重试错误基类 — 网络抖动、限流等临时性故障"""
    pass


class NetworkError(RetryableError):
    """网络错误 — 连接超时、连接拒绝等"""
    pass


class RateLimitError(RetryableError):
    """API 限流错误 — 429 Too Many Requests"""
    pass


class ProviderError(AISummaryException):
    """AI 提供商错误（不可重试）"""
    pass


class FileProcessingError(AISummaryException):
    """文件处理错误（不可重试）"""
    pass


class ValidationError(AISummaryException):
    """验证错误"""
    pass
