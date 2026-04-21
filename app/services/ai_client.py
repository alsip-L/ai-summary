# -*- coding: utf-8 -*-
import time
from openai import OpenAI
from core.errors import (
    FileProcessingError, ProviderError, RetryableError,
    NetworkError, RateLimitError,
)
from core.log import get_logger, get_ws_handler
from app.services.processing_state import ProcessingState

logger = get_logger()

# AI调用级重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 秒，指数退避基数


def classify_openai_error(e: Exception) -> Exception:
    """将 OpenAI SDK 异常分类为项目自定义异常

    策略：AI 调用相关的异常默认可重试（网络抖动、限流、服务端临时错误等），
    仅明确的客户端逻辑错误（如 API Key 无效、模型不存在）不可重试。
    """
    error_name = type(e).__name__
    module = type(e).__module__ or ""
    error_str = str(e)

    # OpenAI SDK 的限流错误
    if "RateLimitError" in error_name or "rate_limit" in error_str.lower() or "429" in error_str:
        return RateLimitError(f"API 限流", cause=e)

    # OpenAI SDK 的网络/连接错误
    if "APIConnectionError" in error_name or "ConnectionError" in error_name:
        return NetworkError(f"网络连接失败", cause=e)

    # OpenAI SDK 的超时错误
    if "APITimeoutError" in error_name or "Timeout" in error_name:
        return NetworkError(f"请求超时", cause=e)

    # OpenAI SDK 的服务端错误 (5xx)
    if "APIStatusError" in error_name or "InternalServerError" in error_name:
        status_code = getattr(e, "status_code", None)
        if (status_code is not None and 500 <= status_code < 600) or \
           (status_code is None and any(f" {code} " in f" {error_str} " for code in range(500, 600))):
            return RetryableError(f"服务端临时错误", cause=e)

    # 明确不可重试的客户端错误：认证失败、模型不存在
    non_retryable_keywords = ["invalid_api_key", "authentication", "model_not_found", "invalid x-api-key"]
    if any(kw in error_str.lower() for kw in non_retryable_keywords):
        return ProviderError(f"AI 调用失败: {error_str}", cause=e)

    # 其他 OpenAI/API 相关异常默认可重试（包括 400 invalid_parameter 等）
    if "openai" in module.lower() or "APIStatusError" in error_name or "APIError" in error_name:
        return RetryableError(f"API 临时错误", cause=e)

    # 非 OpenAI 异常：Python 内置的网络/IO 临时异常视为可重试
    if isinstance(e, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, TimeoutError)):
        return NetworkError(f"网络连接失败", cause=e)

    # 其他非OpenAI异常，视为不可重试
    return ProviderError(f"AI 调用失败: {error_str}", cause=e)


class AIClient:
    """封装 OpenAI 兼容 API 的调用逻辑，包含重试策略和流式输出"""

    def __init__(self, state: ProcessingState = None):
        self._state = state or ProcessingState()

    def call(self, client: OpenAI, content: str, system_prompt: str, model_id: str) -> str:
        """调用 AI API，带指数退避重试（仅对可重试异常）"""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            ws_handler = get_ws_handler()
            try:
                if attempt > 1:
                    self._state.set_retrying(attempt)
                    logger.info(f"第 {attempt} 次重试调用 AI 模型: {model_id}...")
                else:
                    logger.info(f"调用 AI 模型: {model_id}...")
                stream = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    stream=True,
                )
                full_response = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_response.append(token)
                        if ws_handler:
                            ws_handler.put_stream(token)
                response = "".join(full_response)
                if ws_handler:
                    ws_handler.put_stream_end()
                if not response:
                    raise ProviderError("API 返回空响应")
                logger.info(f"AI 响应完成, 字符数: {len(response)}")
                if attempt > 1:
                    logger.info(f"第 {attempt} 次重试成功")
                self._state.clear_retrying()
                return response
            except (ProviderError, FileProcessingError):
                if ws_handler:
                    ws_handler.put_stream_end()
                self._state.clear_retrying()
                raise
            except RetryableError as e:
                if ws_handler:
                    ws_handler.put_stream_end()
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"AI 调用失败（第{attempt}次，{delay}秒后重试）: {e}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"AI 调用失败（已重试{MAX_RETRIES}次）: {e}")
                    self._state.clear_retrying()
                    raise
            except Exception as e:
                if ws_handler:
                    ws_handler.put_stream_end()
                classified = classify_openai_error(e)
                if isinstance(classified, RetryableError):
                    last_error = classified
                    if attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        logger.warning(
                            f"AI 调用失败（第{attempt}次，{delay}秒后重试）: {classified}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"AI 调用失败（已重试{MAX_RETRIES}次）: {classified}")
                        self._state.clear_retrying()
                        raise classified
                else:
                    logger.error(f"AI 调用失败（不可重试）: {classified}")
                    self._state.clear_retrying()
                    raise classified
        self._state.clear_retrying()
        if last_error:
            raise last_error
