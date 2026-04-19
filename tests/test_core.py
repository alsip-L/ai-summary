# -*- coding: utf-8 -*-
"""Tests for core module."""

import unittest
import os
import json
import tempfile
from pathlib import Path

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

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        test_config = {
            "system_settings": {
                "debug_level": "ERROR",
                "flask_secret_key": "test-secret",
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
            },
            "nested": {"level1": {"level2": "value"}}
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)

        ConfigManager.reset()
        ConfigManager._config_path = self.config_path

    def tearDown(self):
        ConfigManager.reset()
        if self.config_path.exists():
            self.config_path.unlink()

    def test_singleton(self):
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2)

    def test_get_nested(self):
        config = ConfigManager()
        value = config.get('nested.level1.level2')
        self.assertEqual(value, 'value')

    def test_get_default(self):
        config = ConfigManager()
        value = config.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')

    def test_set(self):
        config = ConfigManager()
        config.set('new_key', 'new_value')
        self.assertEqual(config.get('new_key'), 'new_value')

    def test_set_nested(self):
        config = ConfigManager()
        config.set('a.b.c', 'deep_value')
        self.assertEqual(config.get('a.b.c'), 'deep_value')

    def test_delete(self):
        config = ConfigManager()
        config.set('to_delete', 'value')
        self.assertTrue(config.delete('to_delete'))
        self.assertIsNone(config.get('to_delete'))

    def test_deep_copy_protection(self):
        config = ConfigManager()
        settings = config.get('system_settings')
        settings['port'] = 9999
        original = config.get('system_settings')
        self.assertEqual(original['port'], 5000)

    def test_set_batch(self):
        config = ConfigManager()
        self.assertTrue(config.set_batch({
            "key_a": "value_a",
            "key_b": "value_b"
        }))
        self.assertEqual(config.get('key_a'), 'value_a')
        self.assertEqual(config.get('key_b'), 'value_b')


class TestExceptions(unittest.TestCase):

    def test_base_exception(self):
        exc = AISummaryException("Test message")
        self.assertEqual(str(exc), "Test message")
        self.assertEqual(exc.message, "Test message")

    def test_provider_error(self):
        exc = ProviderError("Provider failed")
        self.assertIsInstance(exc, AISummaryException)

    def test_file_processing_error(self):
        exc = FileProcessingError("File failed")
        self.assertIsInstance(exc, AISummaryException)

    def test_validation_error(self):
        exc = ValidationError("Validation failed")
        self.assertIsInstance(exc, AISummaryException)


class TestLogger(unittest.TestCase):

    def test_get_logger(self):
        logger = get_logger("test")
        self.assertIsNotNone(logger)

    def test_logger_singleton(self):
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        self.assertIs(logger1, logger2)


if __name__ == '__main__':
    unittest.main()
