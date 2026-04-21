# -*- coding: utf-8 -*-
"""Tests for service layer using new FastAPI + SQLAlchemy architecture."""

import unittest
import os
import json
import shutil
import tempfile

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, DB_PATH
from app.models import Provider, Prompt, TrashProvider, TrashPrompt, UserPreference
from app.services.provider_service import ProviderService
from app.services.prompt_service import PromptService
from app.services.trash_service import TrashService
from app.services.settings_service import SettingsService
from app.services.task_service import TaskService, ProcessingState
from core.config import ConfigManager


def _backup_production_db():
    """从生产数据库备份一份到临时文件，返回临时文件路径。"""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd)
    if DB_PATH.exists():
        shutil.copy2(str(DB_PATH), tmp_path)
    return tmp_path


class _BaseDBTest(unittest.TestCase):

    def setUp(self):
        self._db_path = _backup_production_db()
        self._engine = create_engine(f"sqlite:///{self._db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self._engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        self.db = TestSessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        self._engine.dispose()
        os.unlink(self._db_path)
        ProcessingState.reset()


class TestProviderService(_BaseDBTest):

    def test_create_provider(self):
        svc = ProviderService(self.db)
        result = svc.create({
            "name": "TestProvider",
            "base_url": "https://test.com",
            "api_key": "key123",
            "models": {"m1": "model-1"},
        })
        self.assertTrue(result["success"])
        all_providers = svc.list_all()
        self.assertIn("TestProvider", all_providers)

    def test_create_provider_invalid_data(self):
        svc = ProviderService(self.db)
        result = svc.create({"name": "P"})
        self.assertFalse(result["success"])

    def test_delete_provider_moves_to_trash(self):
        svc = ProviderService(self.db)
        svc.create({"name": "ToDelete", "base_url": "https://t.com", "api_key": "k", "models": {}})
        result = svc.delete("ToDelete")
        self.assertTrue(result["success"])
        self.assertNotIn("ToDelete", svc.list_all())

    def test_update_api_key(self):
        svc = ProviderService(self.db)
        svc.create({"name": "P1", "base_url": "https://p.com", "api_key": "old", "models": {}})
        result = svc.update_api_key("P1", "new-key")
        self.assertTrue(result["success"])

    def test_add_and_delete_model(self):
        svc = ProviderService(self.db)
        svc.create({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        result = svc.add_model("P1", "GPT-4", "gpt-4")
        self.assertTrue(result["success"])
        result = svc.delete_model("P1", "GPT-4")
        self.assertTrue(result["success"])


class TestPromptService(_BaseDBTest):

    def test_create_prompt(self):
        svc = PromptService(self.db)
        result = svc.create({"name": "Summary", "content": "Summarize this"})
        self.assertTrue(result["success"])
        all_prompts = svc.list_all()
        self.assertIn("Summary", all_prompts)

    def test_delete_prompt_moves_to_trash(self):
        svc = PromptService(self.db)
        svc.create({"name": "ToDelete", "content": "content"})
        result = svc.delete("ToDelete")
        self.assertTrue(result["success"])
        self.assertNotIn("ToDelete", svc.list_all())


class TestTrashService(_BaseDBTest):

    def test_restore_provider(self):
        ProviderService(self.db).create({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        ProviderService(self.db).delete("P1")
        svc = TrashService(self.db)
        result = svc.restore_provider("P1")
        self.assertTrue(result["success"])

    def test_permanent_delete_provider(self):
        ProviderService(self.db).create({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        ProviderService(self.db).delete("P1")
        svc = TrashService(self.db)
        result = svc.permanent_delete_provider("P1")
        self.assertTrue(result["success"])

    def test_restore_prompt(self):
        PromptService(self.db).create({"name": "P1", "content": "content"})
        PromptService(self.db).delete("P1")
        svc = TrashService(self.db)
        result = svc.restore_prompt("P1")
        self.assertTrue(result["success"])

    def test_permanent_delete_prompt(self):
        PromptService(self.db).create({"name": "P1", "content": "content"})
        PromptService(self.db).delete("P1")
        svc = TrashService(self.db)
        result = svc.permanent_delete_prompt("P1")
        self.assertTrue(result["success"])


class TestSettingsService(_BaseDBTest):

    def test_get_preferences(self):
        svc = SettingsService(self.db)
        prefs = svc.get_preferences()
        self.assertIsInstance(prefs, dict)

    def test_save_preferences(self):
        svc = SettingsService(self.db)
        result = svc.save_preferences({"selected_provider": "test"})
        self.assertTrue(result["success"])
        prefs = svc.get_preferences()
        self.assertEqual(prefs.get("selected_provider"), "test")

    def test_get_system_settings(self):
        svc = SettingsService(self.db)
        settings = svc.get_system_settings()
        self.assertIn("debug_level", settings)

    def test_save_system_settings_port_validation(self):
        svc = SettingsService(self.db)
        result = svc.save_system_settings({"port": "not_a_number"})
        self.assertFalse(result["success"])
        self.assertIn("端口", result["error"])


class TestTaskService(_BaseDBTest):

    def test_start_missing_api_key(self):
        svc = TaskService(self.db)
        result = svc.start(
            provider_name="P1", model_key="m1", api_key="",
            prompt_name="Prompt1", directory="/tmp",
        )
        self.assertFalse(result["success"])
        self.assertIn("API Key", result["error"])

    def test_start_invalid_directory(self):
        svc = TaskService(self.db)
        result = svc.start(
            provider_name="P1", model_key="m1", api_key="key",
            prompt_name="Prompt1", directory="/nonexistent_dir_xyz",
        )
        self.assertFalse(result["success"])
        self.assertIn("目录", result["error"])

    def test_start_provider_not_found(self):
        svc = TaskService(self.db)
        result = svc.start(
            provider_name="NonExistent", model_key="m1", api_key="key",
            prompt_name="Prompt1", directory=tempfile.mkdtemp(),
        )
        self.assertFalse(result["success"])
        self.assertIn("提供商", result["error"])

    def test_get_status(self):
        svc = TaskService(self.db)
        status = svc.get_status()
        self.assertIn("status", status)

    def test_cancel_when_idle(self):
        svc = TaskService(self.db)
        result = svc.cancel()
        self.assertFalse(result["success"])


class TestProcessingStateReset(unittest.TestCase):

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    def test_reset_creates_fresh_instance(self):
        state1 = ProcessingState()
        state1.start(total_files=5)
        self.assertEqual(state1.get_dict()["status"], "scanning")

        ProcessingState.reset()
        state2 = ProcessingState()
        self.assertEqual(state2.get_dict()["status"], "idle")


if __name__ == '__main__':
    unittest.main()
