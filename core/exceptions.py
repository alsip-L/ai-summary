# -*- coding: utf-8 -*-
"""自定义异常模块

定义项目中使用的所有自定义异常类，便于错误分类和处理。
"""


class AISummaryException(Exception):
    """AI Summary 基础异常类
    
    所有自定义异常的基类。
    """
    
    def __init__(self, message: str = "", code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigError(AISummaryException):
    """配置错误
    
    当配置文件加载、保存或解析出错时抛出。
    """
    pass


class ProviderError(AISummaryException):
    """AI 提供商错误
    
    当 AI 提供商配置错误或调用失败时抛出。
    """
    pass


class FileProcessingError(AISummaryException):
    """文件处理错误
    
    当文件读取、写入或处理失败时抛出。
    """
    pass


class ValidationError(AISummaryException):
    """验证错误
    
    当用户输入验证失败时抛出。
    """
    pass


class ProcessingError(AISummaryException):
    """处理错误
    
    当异步处理任务执行失败时抛出。
    """
    pass


class TrashError(AISummaryException):
    """回收站错误
    
    当回收站操作失败时抛出。
    """
    pass
