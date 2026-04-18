# -*- coding: utf-8 -*-
"""自定义异常模块"""


class AISummaryException(Exception):
    """AI Summary 基础异常类"""
    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class ProviderError(AISummaryException):
    """AI 提供商错误"""
    pass


class FileProcessingError(AISummaryException):
    """文件处理错误"""
    pass


class ValidationError(AISummaryException):
    """验证错误"""
    pass
