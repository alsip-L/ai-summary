# -*- coding: utf-8 -*-
"""SDK 同步客户端测试"""
import unittest
from unittest.mock import patch, MagicMock
import httpx
from ai_summary_sdk.client import AISummaryClient
from ai_summary_sdk._base import _handle_response, BaseClientConfig
from ai_summary_sdk.exceptions import (
    ValidationError, NotFoundError, APIError, AuthenticationError,
)


def _make_response(status_code: int, json_data: dict | None = None, text: str = ""):
    """构造模拟的 httpx.Response"""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = Exception("No JSON")
    return resp


class TestBaseClientConfig(unittest.TestCase):
    def test_defaults(self):
        config = BaseClientConfig()
        self.assertEqual(config.base_url, "http://localhost:5000")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.timeout, 30.0)
        self.assertEqual(config.max_retries, 3)

    @patch.dict("os.environ", {"AI_SUMMARY_BASE_URL": "http://custom:8080", "AI_SUMMARY_API_KEY": "test-key"})
    def test_env_vars(self):
        config = BaseClientConfig()
        self.assertEqual(config.base_url, "http://custom:8080")
        self.assertEqual(config.api_key, "test-key")

    def test_custom_values(self):
        config = BaseClientConfig(base_url="http://myserver:3000/", api_key="key123")
        self.assertEqual(config.base_url, "http://myserver:3000")  # rstrip "/"
        self.assertEqual(config.api_key, "key123")


class TestHandleResponse(unittest.TestCase):
    def test_200(self):
        resp = _make_response(200, {"success": True, "data": [1, 2]})
        result = _handle_response(resp)
        self.assertEqual(result, {"success": True, "data": [1, 2]})

    def test_400(self):
        resp = _make_response(400, {"success": False, "error": "参数错误"})
        with self.assertRaises(ValidationError) as ctx:
            _handle_response(resp)
        self.assertIn("参数错误", ctx.exception.message)

    def test_401(self):
        resp = _make_response(401, {"error": "认证失败"})
        with self.assertRaises(AuthenticationError):
            _handle_response(resp)

    def test_404(self):
        resp = _make_response(404, {"error": "资源不存在"})
        with self.assertRaises(NotFoundError) as ctx:
            _handle_response(resp)
        self.assertIn("资源不存在", ctx.exception.message)

    def test_500(self):
        resp = _make_response(500, {"error": "内部错误"})
        with self.assertRaises(APIError) as ctx:
            _handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 500)

    def test_503_retryable(self):
        resp = _make_response(503, {"error": "服务不可用", "retryable": True})
        with self.assertRaises(APIError) as ctx:
            _handle_response(resp)
        self.assertTrue(ctx.exception.retryable)

    def test_non_json_error(self):
        resp = _make_response(500, text="Internal Server Error")
        with self.assertRaises(APIError) as ctx:
            _handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 500)


class TestAISummaryClient(unittest.TestCase):
    def test_creation_with_defaults(self):
        client = AISummaryClient()
        self.assertEqual(client._config.base_url, "http://localhost:5000")
        self.assertIsNotNone(client.providers)
        self.assertIsNotNone(client.prompts)
        self.assertIsNotNone(client.tasks)
        self.assertIsNotNone(client.files)
        self.assertIsNotNone(client.trash)
        self.assertIsNotNone(client.settings)
        client.close()

    def test_creation_with_custom_url(self):
        client = AISummaryClient(base_url="http://myserver:8080", api_key="test-key")
        self.assertEqual(client._config.base_url, "http://myserver:8080")
        self.assertEqual(client._config.api_key, "test-key")
        client.close()

    def test_context_manager(self):
        with AISummaryClient() as client:
            self.assertIsNotNone(client.providers)
        # 退出后客户端已关闭

    @patch.object(httpx.Client, "get")
    def test_providers_list_success(self, mock_get):
        mock_get.return_value = _make_response(200, [{"name": "openai", "base_url": "https://api.openai.com/v1"}])
        with AISummaryClient() as client:
            result = client.providers.list()
        self.assertEqual(result, [{"name": "openai", "base_url": "https://api.openai.com/v1"}])

    @patch.object(httpx.Client, "post")
    def test_providers_create_success(self, mock_post):
        mock_post.return_value = _make_response(200, {"success": True, "name": "openai"})
        with AISummaryClient() as client:
            result = client.providers.create(
                name="openai", base_url="https://api.openai.com/v1", api_key="sk-xxx",
            )
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
