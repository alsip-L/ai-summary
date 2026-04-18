# -*- coding: utf-8 -*-
"""Tests for core module."""

import unittest
import os
import json
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager
from core.log import get_logger
from core.errors import (
    AISummaryException,
    ProviderError,
    FileProcessingError,
    ValidationError
)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        test_config = {
            "providers": [
                {"name": "test_provider", "base_url": "https://test.com", "api_key": "test_key", "models": {}}
            ],
            "custom_prompts": {"test_prompt": "Test prompt content"},
            "nested": {"level1": {"level2": "value"}}
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)

        # Reset singleton
        ConfigManager.reset()
        ConfigManager._config_path = self.config_path

    def tearDown(self):
        """Clean up test environment."""
        ConfigManager.reset()
        if self.config_path.exists():
            self.config_path.unlink()

    def test_singleton(self):
        """Test singleton pattern."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2)

    def test_get_simple(self):
        """Test getting simple values."""
        config = ConfigManager()
        providers = config.get('providers')
        self.assertIsInstance(providers, list)
        self.assertEqual(len(providers), 1)

    def test_get_nested(self):
        """Test getting nested values."""
        config = ConfigManager()
        value = config.get('nested.level1.level2')
        self.assertEqual(value, 'value')

    def test_get_default(self):
        """Test default value."""
        config = ConfigManager()
        value = config.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')

    def test_set(self):
        """Test setting values."""
        config = ConfigManager()
        config.set('new_key', 'new_value')
        self.assertEqual(config.get('new_key'), 'new_value')

    def test_set_nested(self):
        """Test setting nested values."""
        config = ConfigManager()
        config.set('a.b.c', 'deep_value')
        self.assertEqual(config.get('a.b.c'), 'deep_value')

    def test_delete(self):
        """Test deleting values."""
        config = ConfigManager()
        config.set('to_delete', 'value')
        self.assertTrue(config.delete('to_delete'))
        self.assertIsNone(config.get('to_delete'))

    def test_deep_copy_protection(self):
        """Test that get() returns deep copy."""
        config = ConfigManager()
        providers = config.get('providers')
        providers.append({"name": "new"})
        # Original should not be modified
        original = config.get('providers')
        self.assertEqual(len(original), 1)


class TestExceptions(unittest.TestCase):
    """Test exception classes."""

    def test_base_exception(self):
        """Test base exception."""
        exc = AISummaryException("Test message")
        self.assertEqual(str(exc), "Test message")
        self.assertEqual(exc.message, "Test message")

    def test_provider_error(self):
        """Test provider error."""
        exc = ProviderError("Provider failed")
        self.assertIsInstance(exc, AISummaryException)

    def test_file_processing_error(self):
        """Test file processing error."""
        exc = FileProcessingError("File failed")
        self.assertIsInstance(exc, AISummaryException)

    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError("Validation failed")
        self.assertIsInstance(exc, AISummaryException)


class TestLogger(unittest.TestCase):
    """Test logger functionality."""

    def test_get_logger(self):
        """Test getting logger."""
        logger = get_logger("test")
        self.assertIsNotNone(logger)

    def test_logger_singleton(self):
        """Test logger singleton."""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        self.assertIs(logger1, logger2)


if __name__ == '__main__':
    unittest.main()
