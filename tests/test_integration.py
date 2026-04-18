# -*- coding: utf-8 -*-
"""集成测试 — 需要服务器运行在 http://127.0.0.1:5000

运行方式: python -m tests.test_integration
"""

import requests
import json
import unittest

BASE_URL = "http://127.0.0.1:5000"


class TestAPIEndpoints(unittest.TestCase):
    """测试 RESTful API 端点"""

    def test_homepage(self):
        """测试主页加载"""
        r = requests.get(f"{BASE_URL}/")
        self.assertEqual(r.status_code, 200)

    def test_providers_crud(self):
        """测试提供商 CRUD"""
        # 列出
        r = requests.get(f"{BASE_URL}/api/providers/")
        self.assertEqual(r.status_code, 200)

        # 创建
        data = {"name": "TestProvider", "base_url": "https://test.com", "api_key": "test_key", "models": {}}
        r = requests.post(f"{BASE_URL}/api/providers/", json=data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

        # 更新
        data["base_url"] = "https://updated.com"
        r = requests.put(f"{BASE_URL}/api/providers/TestProvider", json=data)
        self.assertEqual(r.status_code, 200)

        # 删除（移入回收站）
        r = requests.delete(f"{BASE_URL}/api/providers/TestProvider")
        self.assertEqual(r.status_code, 200)

    def test_prompts_crud(self):
        """测试提示词 CRUD"""
        r = requests.get(f"{BASE_URL}/api/prompts/")
        self.assertEqual(r.status_code, 200)

        data = {"name": "TestPrompt", "content": "Test content"}
        r = requests.post(f"{BASE_URL}/api/prompts/", json=data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

        r = requests.delete(f"{BASE_URL}/api/prompts/TestPrompt")
        self.assertEqual(r.status_code, 200)

    def test_tasks_status(self):
        """测试任务状态 API"""
        r = requests.get(f"{BASE_URL}/api/tasks/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("status", data)

    def test_files_drives(self):
        """测试文件驱动器 API"""
        r = requests.get(f"{BASE_URL}/api/files/drives")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

    def test_settings_preferences(self):
        """测试用户偏好 API"""
        r = requests.get(f"{BASE_URL}/api/settings/preferences")
        self.assertEqual(r.status_code, 200)

    def test_settings_system(self):
        """测试系统设置 API"""
        r = requests.get(f"{BASE_URL}/api/settings/system")
        self.assertEqual(r.status_code, 200)

    def test_trash(self):
        """测试回收站 API"""
        r = requests.get(f"{BASE_URL}/api/settings/trash/")
        self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main()
