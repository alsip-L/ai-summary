# -*- coding: utf-8 -*-
"""集成测试 — 使用 FastAPI TestClient，无需运行服务器"""

import unittest
import os
import json
import shutil
import tempfile

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, DB_PATH
from app.models import Provider, Prompt, UserPreference
from app.main import app
from app.dependencies import get_db


from .conftest import _backup_production_db, _ensure_soft_delete_columns


class _BaseIntegrationTest(unittest.TestCase):

    def setUp(self):
        self._db_path = _backup_production_db()
        self._engine = create_engine(f"sqlite:///{self._db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self._engine)
        _ensure_soft_delete_columns(self._engine)
        self._TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        self.db = self._TestSessionLocal()

        def _override_get_db():
            db = self._TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = _override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.rollback()
        self.db.close()
        self._engine.dispose()
        os.unlink(self._db_path)


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
