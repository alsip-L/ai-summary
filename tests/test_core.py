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

from core.config_manager import Config, ConfigManager
from core.logger import get_logger
from core.exceptions import (
    AISummaryException,
    ConfigError,
    ProviderError,
    FileProcessingError,
    ValidationError
)


class TestConfig(unittest.TestCase):
    """Test Config class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create test config
        test_config = {
            "providers": [
                {"name": "test_provider", "base_url": "https://test.com", "api_key": "test_key", "models": {}}
            ],
            "custom_prompts": {"test_prompt": "Test prompt content"},
            "nested": {"level1": {"level2": "value"}}
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)

        # Reset singleton completely for both Config and ConfigManager
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        # Override config path on ConfigManager (this is where it reads from)
        ConfigManager._config_path = self.config_path

        # Create fresh instances
        Config._instance = None
        Config._instance = Config()

    def tearDown(self):
        """Clean up test environment."""
        # Reset singleton completely
        Config._instance = None
        ConfigManager._instance = None
        ConfigManager._cache = None
        ConfigManager._loaded = False

        # Remove temp file
        if self.config_path.exists():
            self.config_path.unlink()
    
    def test_singleton(self):
        """Test singleton pattern."""
        config1 = Config()
        config2 = Config()
        self.assertIs(config1, config2)
    
    def test_get_simple(self):
        """Test getting simple values."""
        config = Config()
        providers = config.get('providers')
        self.assertIsInstance(providers, list)
        self.assertEqual(len(providers), 1)
    
    def test_get_nested(self):
        """Test getting nested values."""
        config = Config()
        value = config.get('nested.level1.level2')
        self.assertEqual(value, 'value')
    
    def test_get_default(self):
        """Test default value."""
        config = Config()
        value = config.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')
    
    def test_set(self):
        """Test setting values."""
        config = Config()
        config.set('new_key', 'new_value')
        self.assertEqual(config.get('new_key'), 'new_value')
    
    def test_set_nested(self):
        """Test setting nested values."""
        config = Config()
        config.set('a.b.c', 'deep_value')
        self.assertEqual(config.get('a.b.c'), 'deep_value')


class TestExceptions(unittest.TestCase):
    """Test exception classes."""
    
    def test_base_exception(self):
        """Test base exception."""
        exc = AISummaryException("Test message", "TEST_CODE")
        self.assertEqual(str(exc), "[TEST_CODE] Test message")
        self.assertEqual(exc.message, "Test message")
        self.assertEqual(exc.code, "TEST_CODE")
    
    def test_config_error(self):
        """Test config error."""
        exc = ConfigError("Config failed")
        self.assertIsInstance(exc, AISummaryException)
    
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
