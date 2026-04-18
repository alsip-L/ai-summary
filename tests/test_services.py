# -*- coding: utf-8 -*-
"""Tests for service layer (ProviderService, PromptService, TrashService, SettingsService, TaskService)."""

import unittest
import os
import json
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager
from features.provider.service import ProviderService
from features.prompt.service import PromptService
from features.trash.service import TrashService
from features.settings.service import SettingsService
from features.task.service import TaskService, ProcessingState


def _setup_config(test_case, extra_config=None):
    """Helper: create temp config and reset ConfigManager singleton."""
    test_case.temp_dir = tempfile.mkdtemp()
    test_case.config_path = Path(test_case.temp_dir) / "test_config.json"
    base = {
        "providers": [],
        "custom_prompts": {},
        "trash": {"providers": {}, "custom_prompts": {}},
        "user_preferences": {},
        "system_settings": {
            "debug_level": "ERROR",
            "flask_secret_key": "test-secret",
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
        },
    }
    if extra_config:
        base.update(extra_config)
    with open(test_case.config_path, "w", encoding="utf-8") as f:
        json.dump(base, f)
    ConfigManager.reset()
    ConfigManager._config_path = test_case.config_path


def _teardown_config(test_case):
    """Helper: reset ConfigManager and clean temp file."""
    ConfigManager.reset()
    if test_case.config_path.exists():
        test_case.config_path.unlink()


class TestProviderService(unittest.TestCase):
    def setUp(self):
        _setup_config(self)

    def tearDown(self):
        _teardown_config(self)

    def test_create_provider(self):
        svc = ProviderService()
        result = svc.create({
            "name": "TestProvider",
            "base_url": "https://test.com",
            "api_key": "key123",
            "models": {"m1": "model-1"},
        })
        self.assertTrue(result["success"])
        # Verify it's listed
        all_providers = svc.list_all()
        self.assertIn("TestProvider", all_providers)

    def test_create_provider_invalid_data(self):
        svc = ProviderService()
        result = svc.create({"name": "P"})  # missing required fields
        self.assertFalse(result["success"])

    def test_delete_provider_moves_to_trash(self):
        _setup_config(self, {
            "providers": [{"name": "ToDelete", "base_url": "https://t.com", "api_key": "k", "models": {}}],
        })
        svc = ProviderService()
        result = svc.delete("ToDelete")
        self.assertTrue(result["success"])
        # Provider should no longer be listed
        self.assertNotIn("ToDelete", svc.list_all())

    def test_update_api_key(self):
        _setup_config(self, {
            "providers": [{"name": "P1", "base_url": "https://p.com", "api_key": "old", "models": {}}],
        })
        svc = ProviderService()
        result = svc.update_api_key("P1", "new-key")
        self.assertTrue(result["success"])

    def test_add_and_delete_model(self):
        _setup_config(self, {
            "providers": [{"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}}],
        })
        svc = ProviderService()
        result = svc.add_model("P1", "GPT-4", "gpt-4")
        self.assertTrue(result["success"])
        result = svc.delete_model("P1", "GPT-4")
        self.assertTrue(result["success"])


class TestPromptService(unittest.TestCase):
    def setUp(self):
        _setup_config(self)

    def tearDown(self):
        _teardown_config(self)

    def test_create_prompt(self):
        svc = PromptService()
        result = svc.create({"name": "Summary", "content": "Summarize this"})
        self.assertTrue(result["success"])
        all_prompts = svc.list_all()
        self.assertIn("Summary", all_prompts)

    def test_delete_prompt_moves_to_trash(self):
        _setup_config(self, {
            "custom_prompts": {"ToDelete": "content"},
        })
        svc = PromptService()
        result = svc.delete("ToDelete")
        self.assertTrue(result["success"])
        self.assertNotIn("ToDelete", svc.list_all())


class TestTrashService(unittest.TestCase):
    def setUp(self):
        _setup_config(self, {
            "providers": [{"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}}],
            "custom_prompts": {"Prompt1": "content"},
            "trash": {"providers": {}, "custom_prompts": {}},
        })

    def tearDown(self):
        _teardown_config(self)

    def test_restore_provider(self):
        # First move to trash
        from features.trash.repository import TrashRepository
        TrashRepository(ConfigManager()).move_provider_to_trash("P1")

        svc = TrashService()
        result = svc.restore_provider("P1")
        self.assertTrue(result["success"])

    def test_permanent_delete_provider(self):
        from features.trash.repository import TrashRepository
        TrashRepository(ConfigManager()).move_provider_to_trash("P1")

        svc = TrashService()
        result = svc.permanent_delete_provider("P1")
        self.assertTrue(result["success"])
        # Should no longer be in trash
        trash = svc.get_all()
        self.assertNotIn("P1", trash.get("providers", {}))

    def test_restore_prompt(self):
        from features.trash.repository import TrashRepository
        TrashRepository(ConfigManager()).move_prompt_to_trash("Prompt1")

        svc = TrashService()
        result = svc.restore_prompt("Prompt1")
        self.assertTrue(result["success"])

    def test_permanent_delete_prompt(self):
        from features.trash.repository import TrashRepository
        TrashRepository(ConfigManager()).move_prompt_to_trash("Prompt1")

        svc = TrashService()
        result = svc.permanent_delete_prompt("Prompt1")
        self.assertTrue(result["success"])


class TestSettingsService(unittest.TestCase):
    def setUp(self):
        _setup_config(self)

    def tearDown(self):
        _teardown_config(self)

    def test_get_preferences(self):
        svc = SettingsService()
        prefs = svc.get_preferences()
        self.assertIsInstance(prefs, dict)

    def test_save_preferences(self):
        svc = SettingsService()
        result = svc.save_preferences({"selected_provider": "test"})
        self.assertTrue(result["success"])
        prefs = svc.get_preferences()
        self.assertEqual(prefs.get("selected_provider"), "test")

    def test_get_system_settings(self):
        svc = SettingsService()
        settings = svc.get_system_settings()
        self.assertIn("debug_level", settings)

    def test_save_system_settings_port_validation(self):
        svc = SettingsService()
        result = svc.save_system_settings({"port": "not_a_number"})
        self.assertFalse(result["success"])
        self.assertIn("端口", result["error"])


class TestTaskService(unittest.TestCase):
    def setUp(self):
        _setup_config(self, {
            "providers": [{"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {"m1": "model-1"}}],
            "custom_prompts": {"Prompt1": "Summarize"},
        })
        ProcessingState.reset()

    def tearDown(self):
        _teardown_config(self)
        ProcessingState.reset()

    def test_start_missing_api_key(self):
        svc = TaskService()
        result = svc.start(
            provider_name="P1", model_key="m1", api_key="",
            prompt_name="Prompt1", directory="/tmp",
        )
        self.assertFalse(result["success"])
        self.assertIn("API Key", result["error"])

    def test_start_invalid_directory(self):
        svc = TaskService()
        result = svc.start(
            provider_name="P1", model_key="m1", api_key="key",
            prompt_name="Prompt1", directory="/nonexistent_dir_xyz",
        )
        self.assertFalse(result["success"])
        self.assertIn("目录", result["error"])

    def test_start_provider_not_found(self):
        svc = TaskService()
        result = svc.start(
            provider_name="NonExistent", model_key="m1", api_key="key",
            prompt_name="Prompt1", directory=self.temp_dir,
        )
        self.assertFalse(result["success"])
        self.assertIn("提供商", result["error"])

    def test_start_prompt_not_found(self):
        svc = TaskService()
        result = svc.start(
            provider_name="P1", model_key="m1", api_key="key",
            prompt_name="NonExistent", directory=self.temp_dir,
        )
        self.assertFalse(result["success"])
        self.assertIn("Prompt", result["error"])

    def test_get_status(self):
        svc = TaskService()
        status = svc.get_status()
        self.assertIn("status", status)

    def test_cancel_when_idle(self):
        svc = TaskService()
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
        # After reset, new instance should be idle
        self.assertEqual(state2.get_dict()["status"], "idle")


if __name__ == '__main__':
    unittest.main()
