# -*- coding: utf-8 -*-
"""集成测试 — 使用 FastAPI TestClient，无需运行服务器"""

import unittest
import os
import json

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.database import SessionLocal, Base, engine
from app.models import Provider, Prompt, TrashProvider, TrashPrompt, UserPreference
from app.main import app


class _BaseIntegrationTest(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()


class TestAPIEndpoints(_BaseIntegrationTest):

    def test_providers_crud(self):
        r = self.client.get("/api/providers/")
        self.assertEqual(r.status_code, 200)

        data = {"name": "TestProvider", "base_url": "https://test.com", "api_key": "test_key", "models": {}}
        r = self.client.post("/api/providers/", json=data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

        r = self.client.delete("/api/providers/TestProvider")
        self.assertEqual(r.status_code, 200)

    def test_prompts_crud(self):
        r = self.client.get("/api/prompts/")
        self.assertEqual(r.status_code, 200)

        data = {"name": "TestPrompt", "content": "Test content"}
        r = self.client.post("/api/prompts/", json=data)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

        r = self.client.delete("/api/prompts/TestPrompt")
        self.assertEqual(r.status_code, 200)

    def test_tasks_status(self):
        r = self.client.get("/api/tasks/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("status", data)

    def test_files_drives(self):
        r = self.client.get("/api/files/drives")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))

    def test_settings_preferences(self):
        r = self.client.get("/api/settings/preferences")
        self.assertEqual(r.status_code, 200)

    def test_trash(self):
        r = self.client.get("/api/settings/trash")
        self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main()
