# -*- coding: utf-8 -*-
"""Tests for managers module."""

import unittest
import os
import json
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.model_manager import ModelManager, ModelConfig
from managers.prompt_manager import PromptManager
from managers.trash_manager import TrashManager
from core.config_manager import Config, ConfigManager


class TestModelManager(unittest.TestCase):
    """Test ModelManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create empty config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({"providers": []}, f)

        # Reset singleton completely
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        # Override config path
        ConfigManager._config_path = self.config_path

        self.manager = ModelManager()

    def tearDown(self):
        """Clean up test environment."""
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        if self.config_path.exists():
            self.config_path.unlink()

    def test_save_model(self):
        """Test saving model."""
        success = self.manager.save(ModelConfig(
            name="TestProvider",
            base_url="https://test.com",
            api_key="test_key",
            models={"model1": "id1"}
        ))
        self.assertTrue(success)

        # Verify
        provider = self.manager.get("TestProvider")
        self.assertIsNotNone(provider)
        self.assertEqual(provider.base_url, "https://test.com")

    def test_get_all_providers(self):
        """Test getting all providers."""
        self.manager.save(ModelConfig(name="Provider1", base_url="https://p1.com", api_key="key1", models={}))
        self.manager.save(ModelConfig(name="Provider2", base_url="https://p2.com", api_key="key2", models={}))

        providers = self.manager.get_all()
        self.assertEqual(len(providers), 2)
        self.assertIn("Provider1", providers)
        self.assertIn("Provider2", providers)

    def test_delete_model(self):
        """Test deleting model."""
        self.manager.save(ModelConfig(name="ToDelete", base_url="https://test.com", api_key="key", models={}))

        success = self.manager.delete("ToDelete")
        self.assertTrue(success)

        # Verify
        self.assertIsNone(self.manager.get("ToDelete"))


class TestPromptManager(unittest.TestCase):
    """Test PromptManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create empty config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({"custom_prompts": {}}, f)

        # Reset singleton completely
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        # Override config path
        ConfigManager._config_path = self.config_path

        self.manager = PromptManager()

    def tearDown(self):
        """Clean up test environment."""
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        if self.config_path.exists():
            self.config_path.unlink()

    def test_save_prompt(self):
        """Test saving prompt."""
        success = self.manager.save("TestPrompt", "This is a test prompt")
        self.assertTrue(success)

        # Verify
        prompt = self.manager.get("TestPrompt")
        self.assertEqual(prompt, "This is a test prompt")

    def test_get_all_prompts(self):
        """Test getting all prompts."""
        self.manager.save("Prompt1", "Content 1")
        self.manager.save("Prompt2", "Content 2")

        prompts = self.manager.get_all()
        self.assertEqual(len(prompts), 2)

    def test_delete_prompt(self):
        """Test deleting prompt."""
        self.manager.save("ToDelete", "Content")

        success = self.manager.delete("ToDelete")
        self.assertTrue(success)

        # Verify
        self.assertIsNone(self.manager.get("ToDelete"))

    def test_list_format_compatibility(self):
        """Test handling list format prompts."""
        # Reset singleton
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False
        ConfigManager._config_path = self.config_path

        # Simulate old format (list)
        config = Config()
        config.set('custom_prompts', {'OldPrompt': ['Line 1', 'Line 2']})
        config.save()

        # Reload
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False
        ConfigManager._config_path = self.config_path

        manager = PromptManager()
        prompt = manager.get("OldPrompt")
        self.assertEqual(prompt, "Line 1\nLine 2")


class TestTrashManager(unittest.TestCase):
    """Test TrashManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create config with providers and prompts
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({
                "providers": [{"name": "TestProvider", "base_url": "https://test.com", "api_key": "key", "models": {}}],
                "custom_prompts": {"TestPrompt": "Test content"},
                "trash": {}
            }, f)

        # Reset singleton completely
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        # Override config path
        ConfigManager._config_path = self.config_path

        self.manager = TrashManager()

    def tearDown(self):
        """Clean up test environment."""
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        if self.config_path.exists():
            self.config_path.unlink()

    def test_move_provider_to_trash(self):
        """Test moving provider to trash."""
        success = self.manager.move_provider_to_trash("TestProvider")
        self.assertTrue(success)

        # Verify in trash
        providers = self.manager.get_providers()
        self.assertIn("TestProvider", providers)

    def test_restore_provider(self):
        """Test restoring provider from trash."""
        # First move to trash
        self.manager.move_provider_to_trash("TestProvider")

        # Then restore
        success = self.manager.restore_provider("TestProvider")
        self.assertTrue(success)

        # Verify restored
        model_manager = ModelManager()
        self.assertIsNotNone(model_manager.get("TestProvider"))

    def test_permanent_delete(self):
        """Test permanent deletion."""
        # First move to trash
        self.manager.move_provider_to_trash("TestProvider")

        # Then permanently delete
        success = self.manager.permanent_delete_provider("TestProvider")
        self.assertTrue(success)

        # Verify not in trash
        providers = self.manager.get_providers()
        self.assertNotIn("TestProvider", providers)


if __name__ == '__main__':
    unittest.main()
