# -*- coding: utf-8 -*-
"""AIClient 单元测试"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.errors import RateLimitError, NetworkError, RetryableError, ProviderError
from app.services.ai_client import classify_openai_error


class TestClassifyOpenAIError(unittest.TestCase):

    def test_classify_rate_limit_error(self):
        e = Exception("Error 429: Too Many Requests")
        result = classify_openai_error(e)
        self.assertIsInstance(result, RateLimitError)

    def test_classify_connection_error(self):
        e = type("APIConnectionError", (Exception,), {})("connection failed")
        result = classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_classify_timeout_error(self):
        e = type("APITimeoutError", (Exception,), {})("timeout")
        result = classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)

    def test_classify_auth_error(self):
        e = Exception("invalid_api_key provided")
        result = classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)

    def test_classify_server_error(self):
        e = type("APIStatusError", (Exception,), {"status_code": 500})("server error")
        result = classify_openai_error(e)
        self.assertIsInstance(result, RetryableError)

    def test_classify_unknown_error(self):
        e = ValueError("some random error")
        result = classify_openai_error(e)
        self.assertIsInstance(result, ProviderError)

    def test_classify_builtin_network_error(self):
        e = ConnectionResetError("reset")
        result = classify_openai_error(e)
        self.assertIsInstance(result, NetworkError)


if __name__ == '__main__':
    unittest.main()
