# -*- coding: utf-8 -*-
"""重试流程单元测试 — 覆盖异常分类、文件级重试、AI调用级重试、文件读取异常处理"""

import unittest
import os
import sys
import time
import tempfile
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.errors import (
    RetryableError, NetworkError, RateLimitError,
    ProviderError, FileProcessingError,
)
from core.utils import read_file_with_encoding
from app.services.task_service import (
    TaskService, ProcessingState, _classify_openai_error,
    MAX_RETRIES, FILE_MAX_RETRIES, RETRY_BASE_DELAY,
)


# ============================================================
# 1. _classify_openai_error 异常分类测试
# ============================================================

class TestClassifyOpenAIError(unittest.TestCase):
    """测试 _classify_openai_error 将各类异常正确分类"""

    def test_rate_limit_error_by_name(self):
        """RateLimitError 名称 → RateLimitError"""
        e = type("RateLimitError", (Exception,), {})("rate limited")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RateLimitError)

    def test_rate_limit_error_by_keyword(self):
        """error_str 含 rate_limit → RateLimitError"""
        e = Exception("rate_limit exceeded")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RateLimitError)

    def test_rate_limit_error_by_429(self):
        """error_str 含 429 → RateLimitError"""
        e = Exception("Error 429: Too Many Requests")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RateLimitError)

    def test_api_connection_error(self):
        """APIConnectionError 名称 → NetworkError"""
        e = type("APIConnectionError", (Exception,), {})("connection failed")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_connection_error(self):
        """ConnectionError 名称 → NetworkError"""
        e = type("ConnectionError", (Exception,), {})("refused")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_api_timeout_error(self):
        """APITimeoutError 名称 → NetworkError"""
        e = type("APITimeoutError", (Exception,), {})("timeout")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_timeout_error(self):
        """Timeout 名称 → NetworkError"""
        e = type("Timeout", (Exception,), {})("timed out")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_5xx_with_status_code(self):
        """APIStatusError + status_code=500 → RetryableError"""
        e = type("APIStatusError", (Exception,), {"status_code": 500})("server error")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RetryableError)

    def test_5xx_with_status_code_503(self):
        """APIStatusError + status_code=503 → RetryableError"""
        e = type("APIStatusError", (Exception,), {"status_code": 503})("service unavailable")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RetryableError)

    def test_5xx_without_status_code_in_message(self):
        """APIStatusError + 无 status_code + 消息含 500 → RetryableError"""
        e = type("APIStatusError", (Exception,), {})("Error 500 Internal")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RetryableError)

    def test_4xx_with_status_code(self):
        """APIStatusError + status_code=400 → RetryableError（其他OpenAI异常默认可重试）"""
        e = type("APIStatusError", (Exception,), {"status_code": 400})("bad request")
        result = _classify_openai_error(e)
        # 400 不是 5xx，不匹配5xx分支，但 APIStatusError 名称匹配"其他OpenAI异常默认可重试"
        self.assertIsInstance(result, RetryableError)

    def test_invalid_api_key(self):
        """error_str 含 invalid_api_key → ProviderError（不可重试）"""
        e = Exception("invalid_api_key provided")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)

    def test_model_not_found(self):
        """error_str 含 model_not_found → ProviderError（不可重试）"""
        e = Exception("model_not_found: gpt-5")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)

    def test_authentication_error(self):
        """error_str 含 authentication → ProviderError（不可重试）"""
        e = Exception("authentication failed")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)

    def test_openai_module_error_default_retryable(self):
        """openai 模块异常 → 默认 RetryableError"""
        ExcClass = type("SomeOpenAIError", (Exception,), {})
        ExcClass.__module__ = "openai._some_module"
        e = ExcClass("something went wrong")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, RetryableError)

    def test_python_connection_reset(self):
        """ConnectionResetError → NetworkError"""
        e = ConnectionResetError("reset")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_python_timeout_error(self):
        """Python TimeoutError → NetworkError"""
        e = TimeoutError("timed out")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_unknown_error_non_retryable(self):
        """未知非OpenAI异常 → ProviderError（不可重试）"""
        e = ValueError("some random error")
        result = _classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)


# ============================================================
# 2. _process_file_with_retry 文件级重试测试
# ============================================================

class TestProcessFileWithRetry(unittest.TestCase):
    """测试文件级重试逻辑"""

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    @patch.object(TaskService, '_process_file')
    def test_success_on_first_try(self, mock_process):
        """首次处理成功，不进入重试"""
        mock_process.return_value = {"source": "test.txt", "output": "test.md"}
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertEqual(result["output"], "test.md")
        self.assertNotIn("error", result)
        self.assertEqual(mock_process.call_count, 1)

    @patch.object(TaskService, '_process_file')
    def test_non_retryable_error_no_retry(self, mock_process):
        """不可重试错误，不进入重试循环"""
        mock_process.return_value = {"source": "test.txt", "error": "API Key无效", "retryable": False}
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertEqual(result["error"], "API Key无效")
        self.assertFalse(result["retryable"])
        self.assertEqual(mock_process.call_count, 1)

    @patch.object(TaskService, '_process_file')
    @patch('app.services.task_service.time.sleep')
    def test_retryable_error_then_success(self, mock_sleep, mock_process):
        """可重试错误 → 重试后成功"""
        mock_process.side_effect = [
            {"source": "test.txt", "error": "网络超时", "retryable": True},
            {"source": "test.txt", "output": "test.md"},
        ]
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertEqual(result["output"], "test.md")
        self.assertEqual(mock_process.call_count, 2)
        mock_sleep.assert_called_once()

    @patch.object(TaskService, '_process_file')
    @patch('app.services.task_service.time.sleep')
    def test_retryable_error_all_retries_fail(self, mock_sleep, mock_process):
        """可重试错误 → 重试全部失败"""
        mock_process.return_value = {"source": "test.txt", "error": "服务端错误", "retryable": True}
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertIn("error", result)
        self.assertIn(f"重试{FILE_MAX_RETRIES}次仍失败", result["error"])
        self.assertTrue(result["retryable"])
        # 首次1次 + 重试循环 range(2, FILE_MAX_RETRIES+1) 次
        # FILE_MAX_RETRIES=2 → range(2,3) → 1次重试，总共2次调用
        retry_count = len(list(range(2, FILE_MAX_RETRIES + 1)))
        self.assertEqual(mock_process.call_count, 1 + retry_count)

    @patch.object(TaskService, '_process_file')
    @patch('app.services.task_service.time.sleep')
    def test_retryable_then_non_retryable_stops(self, mock_sleep, mock_process):
        """可重试 → 变为不可重试 → 立即停止"""
        mock_process.side_effect = [
            {"source": "test.txt", "error": "网络超时", "retryable": True},
            {"source": "test.txt", "error": "API Key无效", "retryable": False},
        ]
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertEqual(result["error"], "API Key无效")
        self.assertFalse(result["retryable"])
        self.assertEqual(mock_process.call_count, 2)

    @patch.object(TaskService, '_process_file')
    @patch('app.services.task_service.time.sleep')
    def test_retry_delay_exponential_backoff(self, mock_sleep, mock_process):
        """验证指数退避延迟：第2次重试 delay = RETRY_BASE_DELAY * 2^0 = 2s"""
        mock_process.side_effect = [
            {"source": "test.txt", "error": "网络超时", "retryable": True},
            {"source": "test.txt", "output": "test.md"},
        ]
        TaskService._process_file_with_retry("test.txt", None, None, None)
        # attempt=2, delay = RETRY_BASE_DELAY * 2^(2-2) = 2 * 1 = 2
        mock_sleep.assert_called_once_with(RETRY_BASE_DELAY)

    @patch.object(TaskService, '_process_file')
    @patch('app.services.task_service.time.sleep')
    def test_cancel_during_retry(self, mock_sleep, mock_process):
        """重试期间被取消 → 返回取消错误"""
        state = ProcessingState()
        mock_process.return_value = {"source": "test.txt", "error": "网络超时", "retryable": True}

        # 在 sleep 之前取消
        def cancel_before_sleep(delay):
            state.set_cancelled()

        mock_sleep.side_effect = cancel_before_sleep
        result = TaskService._process_file_with_retry("test.txt", None, None, None)
        self.assertIn("error", result)
        # 取消后应返回取消信息
        self.assertIn("取消", result["error"])


# ============================================================
# 3. _call_ai AI调用级重试测试
# ============================================================

class TestCallAIRetry(unittest.TestCase):
    """测试 AI 调用级重试逻辑"""

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    @patch('app.services.task_service.get_ws_handler')
    def test_success_on_first_call(self, mock_ws):
        """首次调用成功"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "AI response"
        mock_stream.__iter__ = MagicMock(return_value=iter([mock_chunk]))
        mock_client.chat.completions.create.return_value = mock_stream

        result = TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(result, "AI response")

    @patch('app.services.task_service.time.sleep')
    @patch('app.services.task_service.get_ws_handler')
    def test_retryable_error_then_success(self, mock_ws, mock_sleep):
        """RetryableError → 重试后成功"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "success"
        mock_stream.__iter__ = MagicMock(return_value=iter([mock_chunk]))

        # 第一次抛出 RetryableError，第二次成功
        mock_client.chat.completions.create.side_effect = [
            RetryableError("临时错误"),
            mock_stream,
        ]
        result = TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(result, "success")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    @patch('app.services.task_service.time.sleep')
    @patch('app.services.task_service.get_ws_handler')
    def test_retryable_error_all_retries_exhausted(self, mock_ws, mock_sleep):
        """RetryableError → 重试 MAX_RETRIES 次后抛出"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RetryableError("持续失败")

        with self.assertRaises(RetryableError):
            TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(mock_client.chat.completions.create.call_count, MAX_RETRIES)

    @patch('app.services.task_service.get_ws_handler')
    def test_provider_error_no_retry(self, mock_ws):
        """ProviderError → 不重试，直接抛出"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ProviderError("API Key无效")

        with self.assertRaises(ProviderError):
            TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    @patch('app.services.task_service.get_ws_handler')
    def test_file_processing_error_no_retry(self, mock_ws):
        """FileProcessingError → 不重试，直接抛出"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = FileProcessingError("文件错误")

        with self.assertRaises(FileProcessingError):
            TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    @patch('app.services.task_service.time.sleep')
    @patch('app.services.task_service.get_ws_handler')
    def test_unclassified_error_classified_as_retryable(self, mock_ws, mock_sleep):
        """未分类异常 → _classify_openai_error 判定为可重试 → 重试"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "ok"
        mock_stream.__iter__ = MagicMock(return_value=iter([mock_chunk]))

        # 构造一个会被分类为 RetryableError 的异常（openai 模块）
        class FakeOpenAIError(Exception):
            pass
        FakeOpenAIError.__module__ = "openai.api"

        error = FakeOpenAIError("temp error")
        mock_client.chat.completions.create.side_effect = [error, mock_stream]

        result = TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(result, "ok")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    @patch('app.services.task_service.get_ws_handler')
    def test_unclassified_error_classified_as_non_retryable(self, mock_ws):
        """未分类异常 → _classify_openai_error 判定为不可重试 → 直接抛出"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValueError("invalid_api_key bad")

        with self.assertRaises(ProviderError):
            TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    @patch('app.services.task_service.time.sleep')
    @patch('app.services.task_service.get_ws_handler')
    def test_exponential_backoff_delay(self, mock_ws, mock_sleep):
        """验证 AI 调用重试的指数退避：attempt=1 → 2s, attempt=2 → 4s"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = NetworkError("网络错误")

        with self.assertRaises(RetryableError):
            TaskService._call_ai(mock_client, "content", "system", "model-1")

        # MAX_RETRIES=3, 第1次失败 sleep(2), 第2次失败 sleep(4), 第3次失败抛出
        expected_calls = []
        for attempt in range(1, MAX_RETRIES):
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            expected_calls.append(unittest.mock.call(delay))

        mock_sleep.assert_has_calls(expected_calls)

    @patch('app.services.task_service.get_ws_handler')
    def test_empty_response_raises_provider_error(self, mock_ws):
        """API 返回空响应 → ProviderError"""
        mock_ws.return_value = None
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = None  # 空内容
        mock_stream.__iter__ = MagicMock(return_value=iter([mock_chunk]))
        mock_client.chat.completions.create.return_value = mock_stream

        with self.assertRaises(ProviderError) as ctx:
            TaskService._call_ai(mock_client, "content", "system", "model-1")
        self.assertIn("空响应", str(ctx.exception))


# ============================================================
# 4. read_file_with_encoding 文件读取异常处理测试
# ============================================================

class TestReadFileWithEncoding(unittest.TestCase):
    """测试文件读取的多编码尝试和异常处理"""

    def test_read_utf8_file(self):
        """成功读取 UTF-8 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as f:
            f.write("你好世界")
            path = f.name
        try:
            content = read_file_with_encoding(path)
            self.assertEqual(content, "你好世界")
        finally:
            os.unlink(path)

    def test_read_gbk_file(self):
        """成功读取 GBK 文件（UTF-8 失败后回退到 GBK）"""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write("你好世界".encode("gbk"))
            path = f.name
        try:
            content = read_file_with_encoding(path)
            self.assertEqual(content, "你好世界")
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """文件不存在 → FileProcessingError"""
        with self.assertRaises(FileProcessingError) as ctx:
            read_file_with_encoding("/nonexistent_file_xyz_12345.txt")
        self.assertIn("文件不存在", str(ctx.exception))

    def test_custom_encodings(self):
        """自定义编码列表"""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write("测试".encode("gb18030"))
            path = f.name
        try:
            content = read_file_with_encoding(path, encodings=["utf-8", "gb18030"])
            self.assertEqual(content, "测试")
        finally:
            os.unlink(path)

    def test_unreadable_file(self):
        """无法解码的文件 → FileProcessingError"""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(b'\xff\xfe\x00\x00\x01\x02')  # 无效编码字节
            path = f.name
        try:
            with self.assertRaises(FileProcessingError) as ctx:
                read_file_with_encoding(path, encodings=["utf-8", "gbk"])
            self.assertIn("无法解码", str(ctx.exception))
        finally:
            os.unlink(path)


# ============================================================
# 5. ProcessingState 重试状态管理测试
# ============================================================

class TestProcessingStateRetry(unittest.TestCase):
    """测试 ProcessingState 的重试状态管理"""

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    def test_set_and_clear_retrying(self):
        """设置和清除重试状态"""
        state = ProcessingState()
        state.start()
        self.assertFalse(state.get_dict()["retrying"])

        state.set_retrying(1)
        d = state.get_dict()
        self.assertTrue(d["retrying"])
        self.assertEqual(d["retry_attempt"], 1)

        state.clear_retrying()
        d = state.get_dict()
        self.assertFalse(d["retrying"])
        self.assertEqual(d["retry_attempt"], 0)

    def test_retry_max_default(self):
        """retry_max 默认为 FILE_MAX_RETRIES"""
        state = ProcessingState()
        self.assertEqual(state.get_dict()["retry_max"], FILE_MAX_RETRIES)

    def test_cancel_during_retry(self):
        """重试期间取消"""
        state = ProcessingState()
        state.start()
        state.set_retrying(1)
        state.cancel()
        self.assertTrue(state.is_cancelled())
        d = state.get_dict()
        self.assertEqual(d["status"], "cancelled")


# ============================================================
# 6. _process_file 异常分类集成测试
# ============================================================

class TestProcessFileErrorClassification(unittest.TestCase):
    """测试 _process_file 对不同异常的分类返回"""

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    @patch('app.services.task_service.read_file_with_encoding')
    def test_retryable_error_returns_retryable(self, mock_read):
        """_process_file 捕获 RetryableError → retryable=True"""
        mock_read.return_value = "content"
        with patch.object(TaskService, '_call_ai', side_effect=NetworkError("网络断开")):
            result = TaskService._process_file("test.txt", None, None, None)
            self.assertTrue(result["retryable"])
            self.assertIn("error", result)

    @patch('app.services.task_service.read_file_with_encoding')
    def test_provider_error_returns_non_retryable(self, mock_read):
        """_process_file 捕获 ProviderError → retryable=False"""
        mock_read.return_value = "content"
        with patch.object(TaskService, '_call_ai', side_effect=ProviderError("API Key无效")):
            result = TaskService._process_file("test.txt", None, None, None)
            self.assertFalse(result["retryable"])
            self.assertIn("error", result)

    @patch('app.services.task_service.read_file_with_encoding')
    def test_file_processing_error_returns_non_retryable(self, mock_read):
        """_process_file 捕获 FileProcessingError → retryable=False"""
        mock_read.side_effect = FileProcessingError("文件不存在: test.txt")
        result = TaskService._process_file("test.txt", None, None, None)
        self.assertFalse(result["retryable"])
        self.assertIn("error", result)

    @patch('app.services.task_service.read_file_with_encoding')
    def test_success_returns_output(self, mock_read):
        """_process_file 成功 → 返回 output"""
        mock_read.return_value = "content"
        with patch.object(TaskService, '_call_ai', return_value="AI summary"):
            with patch.object(TaskService, '_save_response', return_value="test.md"):
                result = TaskService._process_file("test.txt", None, None, None)
                self.assertEqual(result["output"], "test.md")
                self.assertNotIn("error", result)


if __name__ == '__main__':
    unittest.main()
