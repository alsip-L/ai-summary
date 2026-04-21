# -*- coding: utf-8 -*-
"""指数退避重试策略"""
import asyncio
import time
from functools import wraps
from .exceptions import APIError, ConnectionError


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (APIError, ConnectionError),
):
    """装饰器：对可重试异常进行指数退避重试

    Args:
        max_retries: 最大重试次数（不含首次请求）
        base_delay: 基础退避延迟（秒），实际延迟 = base_delay * 2^attempt
        max_delay: 最大退避延迟（秒）
        retryable_exceptions: 触发重试的异常类型
    """

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retryable_exceptions as e:
                        # 仅对 retryable=True 的 APIError 重试
                        if isinstance(e, APIError) and not e.retryable:
                            raise
                        last_exception = e
                        if attempt < max_retries:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            await asyncio.sleep(delay)
                raise last_exception
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except retryable_exceptions as e:
                        if isinstance(e, APIError) and not e.retryable:
                            raise
                        last_exception = e
                        if attempt < max_retries:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            time.sleep(delay)
                raise last_exception
            return sync_wrapper

    return decorator
