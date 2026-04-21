# -*- coding: utf-8 -*-
"""SDK 模型校验测试"""
import unittest
from ai_summary_sdk.models import (
    ProviderCreate, ApiKeyUpdate, ModelCreate,
    PromptCreate, TaskStartRequest, RetryFailedRequest,
    PreferencesUpdate, SuccessResponse, ErrorResponse,
    ProviderInfo, PromptInfo, TaskStatus,
)


class TestProviderCreate(unittest.TestCase):
    def test_valid(self):
        p = ProviderCreate(
            name="openai", base_url="https://api.openai.com/v1",
            api_key="sk-xxx", models={"GPT-4": "gpt-4"}, is_active=True,
        )
        data = p.model_dump()
        self.assertEqual(data["name"], "openai")
        self.assertEqual(data["models"], {"GPT-4": "gpt-4"})

    def test_default_values(self):
        p = ProviderCreate(name="test", base_url="https://api.test.com", api_key="key")
        data = p.model_dump()
        self.assertEqual(data["models"], {})
        self.assertTrue(data["is_active"])


class TestApiKeyUpdate(unittest.TestCase):
    def test_valid(self):
        u = ApiKeyUpdate(api_key="sk-new")
        self.assertEqual(u.model_dump()["api_key"], "sk-new")


class TestModelCreate(unittest.TestCase):
    def test_valid(self):
        m = ModelCreate(display_name="GPT-4", model_id="gpt-4")
        data = m.model_dump()
        self.assertEqual(data["display_name"], "GPT-4")
        self.assertEqual(data["model_id"], "gpt-4")


class TestPromptCreate(unittest.TestCase):
    def test_valid(self):
        p = PromptCreate(name="摘要生成", content="请生成摘要。")
        data = p.model_dump()
        self.assertEqual(data["name"], "摘要生成")


class TestTaskStartRequest(unittest.TestCase):
    def test_valid(self):
        r = TaskStartRequest(
            provider="openai", model="gpt-4", api_key="sk-xxx",
            prompt="摘要生成", directory="C:/data",
        )
        data = r.model_dump()
        self.assertEqual(data["provider"], "openai")
        self.assertFalse(data["skip_existing"])


class TestRetryFailedRequest(unittest.TestCase):
    def test_valid(self):
        r = RetryFailedRequest(
            provider="openai", model="gpt-4", api_key="sk-xxx", prompt="摘要生成",
        )
        data = r.model_dump()
        self.assertEqual(data["provider"], "openai")


class TestPreferencesUpdate(unittest.TestCase):
    def test_all_none(self):
        p = PreferencesUpdate()
        data = p.model_dump()
        self.assertIsNone(data["selected_provider"])
        self.assertIsNone(data["selected_model"])

    def test_with_values(self):
        p = PreferencesUpdate(selected_provider="openai", selected_model="gpt-4")
        data = p.model_dump(exclude_none=True)
        self.assertEqual(data["selected_provider"], "openai")
        self.assertNotIn("directory_path", data)


class TestSuccessResponse(unittest.TestCase):
    def test_model(self):
        r = SuccessResponse()
        data = r.model_dump()
        self.assertTrue(data["success"])
        self.assertIsNone(data["message"])

    def test_with_message(self):
        r = SuccessResponse(message="操作成功")
        self.assertEqual(r.message, "操作成功")


class TestErrorResponse(unittest.TestCase):
    def test_model(self):
        r = ErrorResponse(error="提供商不存在")
        data = r.model_dump()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "提供商不存在")
        self.assertIsNone(data["retryable"])


class TestProviderInfo(unittest.TestCase):
    def test_model(self):
        p = ProviderInfo(name="openai", base_url="https://api.openai.com/v1")
        data = p.model_dump()
        self.assertEqual(data["name"], "openai")
        self.assertEqual(data["models"], {})


class TestPromptInfo(unittest.TestCase):
    def test_model(self):
        p = PromptInfo(name="摘要生成", content="请生成摘要。")
        data = p.model_dump()
        self.assertEqual(data["name"], "摘要生成")


class TestTaskStatus(unittest.TestCase):
    def test_model(self):
        s = TaskStatus(status="idle")
        data = s.model_dump()
        self.assertEqual(data["status"], "idle")
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["results"], [])


if __name__ == "__main__":
    unittest.main()
