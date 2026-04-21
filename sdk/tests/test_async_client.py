# -*- coding: utf-8 -*-
"""SDK 异步客户端测试"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from ai_summary_sdk.async_client import AsyncAISummaryClient
from ai_summary_sdk._base import _handle_response, BaseClientConfig
from ai_summary_sdk.exceptions import APIError, NotFoundError


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


class TestAsyncAISummaryClient(unittest.TestCase):
    def test_creation(self):
        client = AsyncAISummaryClient(base_url="http://localhost:5000")
        self.assertEqual(client._config.base_url, "http://localhost:5000")
        self.assertIsNotNone(client.providers)
        self.assertIsNotNone(client.prompts)
        self.assertIsNotNone(client.tasks)
        self.assertIsNotNone(client.files)
        self.assertIsNotNone(client.trash)
        self.assertIsNotNone(client.settings)

    def test_async_context_manager(self):
        async def run():
            async with AsyncAISummaryClient() as client:
                self.assertIsNotNone(client.providers)
        asyncio.run(run())

    def test_async_providers_list(self):
        async def run():
            client = AsyncAISummaryClient()
            mock_resp = _make_response(200, [{"name": "openai"}])
            with patch.object(httpx.AsyncClient, "get", return_value=AsyncMock(return_value=mock_resp)()):
                # 直接 mock _client.get
                original_get = client._client.get
                client._client.get = AsyncMock(return_value=mock_resp)
                try:
                    result = await client.providers.list()
                    self.assertEqual(result, [{"name": "openai"}])
                finally:
                    client._client.get = original_get
            await client.close()
        asyncio.run(run())

    def test_async_handle_response_error(self):
        async def run():
            client = AsyncAISummaryClient()
            mock_resp = _make_response(404, {"error": "不存在"})
            with patch.object(httpx.AsyncClient, "get", return_value=AsyncMock(return_value=mock_resp)()):
                client._client.get = AsyncMock(return_value=mock_resp)
                try:
                    with self.assertRaises(NotFoundError):
                        await client.providers.list()
                finally:
                    pass
            await client.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
