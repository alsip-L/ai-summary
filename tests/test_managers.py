# -*- coding: utf-8 -*-
"""Tests for repository layer (replaces old managers tests)."""

import unittest
import os
import json
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from repositories.trash_repo import TrashRepository
from models.provider import ProviderConfig
from models.prompt import PromptConfig


class TestProviderRepository(unittest.TestCase):
    """Test ProviderRepository class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({"providers": [], "custom_prompts": {}, "trash": {}}, f)

        ConfigManager.reset()
        ConfigManager._config_path = self.config_path

    def tearDown(self):
        ConfigManager.reset()
        if self.config_path.exists():
            self.config_path.unlink()

    def test_save_and_get(self):
        repo = ProviderRepository(ConfigManager())
        provider = ProviderConfig(name="TestProvider", base_url="https://test.com", api_key="test_key", models={"m1": "id1"})
        self.assertTrue(repo.save(provider))

        result = repo.get("TestProvider")
        self.assertIsNotNone(result)
        self.assertEqual(result.base_url, "https://test.com")

    def test_get_all(self):
        repo = ProviderRepository(ConfigManager())
        repo.save(ProviderConfig(name="P1", base_url="https://p1.com", api_key="k1", models={}))
        repo.save(ProviderConfig(name="P2", base_url="https://p2.com", api_key="k2", models={}))

        all_providers = repo.get_all()
        self.assertEqual(len(all_providers), 2)
        self.assertIn("P1", all_providers)
        self.assertIn("P2", all_providers)

    def test_delete(self):
        repo = ProviderRepository(ConfigManager())
        repo.save(ProviderConfig(name="ToDelete", base_url="https://test.com", api_key="k", models={}))
        self.assertTrue(repo.delete("ToDelete"))
        self.assertIsNone(repo.get("ToDelete"))


class TestPromptRepository(unittest.TestCase):
    """Test PromptRepository class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({"providers": [], "custom_prompts": {}, "trash": {}}, f)

        ConfigManager.reset()
        ConfigManager._config_path = self.config_path

    def tearDown(self):
        ConfigManager.reset()
        if self.config_path.exists():
            self.config_path.unlink()

    def test_save_and_get(self):
        repo = PromptRepository(ConfigManager())
        self.assertTrue(repo.save(PromptConfig(name="TestPrompt", content="Test content")))

        result = repo.get("TestPrompt")
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "Test content")

    def test_get_all(self):
        repo = PromptRepository(ConfigManager())
        repo.save(PromptConfig(name="P1", content="Content 1"))
        repo.save(PromptConfig(name="P2", content="Content 2"))

        all_prompts = repo.get_all()
        self.assertEqual(len(all_prompts), 2)

    def test_delete(self):
        repo = PromptRepository(ConfigManager())
        repo.save(PromptConfig(name="ToDelete", content="Content"))
        self.assertTrue(repo.delete("ToDelete"))
        self.assertIsNone(repo.get("ToDelete"))


class TestTrashRepository(unittest.TestCase):
    """Test TrashRepository class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({
                "providers": [{"name": "TestProvider", "base_url": "https://test.com", "api_key": "key", "models": {}, "is_active": True}],
                "custom_prompts": {"TestPrompt": "Test content"},
                "trash": {"providers": {}, "custom_prompts": {}}
            }, f)

        ConfigManager.reset()
        ConfigManager._config_path = self.config_path

    def tearDown(self):
        ConfigManager.reset()
        if self.config_path.exists():
            self.config_path.unlink()

    def test_move_provider_to_trash(self):
        repo = TrashRepository(ConfigManager())
        self.assertTrue(repo.move_provider_to_trash("TestProvider"))

        trash = repo.get_all()
        self.assertIn("providers", trash)
        self.assertIn("TestProvider", trash["providers"])

    def test_restore_provider(self):
        repo = TrashRepository(ConfigManager())
        repo.move_provider_to_trash("TestProvider")
        self.assertTrue(repo.restore_provider("TestProvider"))

        provider_repo = ProviderRepository(ConfigManager())
        self.assertIsNotNone(provider_repo.get("TestProvider"))

    def test_permanent_delete(self):
        repo = TrashRepository(ConfigManager())
        repo.move_provider_to_trash("TestProvider")
        self.assertTrue(repo.permanent_delete_provider("TestProvider"))

        trash = repo.get_all()
        self.assertNotIn("TestProvider", trash.get("providers", {}))


if __name__ == '__main__':
    unittest.main()
