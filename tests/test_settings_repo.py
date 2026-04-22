# -*- coding: utf-8 -*-
"""SettingsRepository 单元测试"""

import unittest
import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, DB_PATH
from app.models import UserPreference
from app.repositories.settings_repo import SettingsRepository
from core.utils import safe_json_loads


from .conftest import _backup_production_db


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


class TestSettingsRepository(_BaseDBTest):

    def test_get_all_returns_empty_when_no_preferences(self):
        repo = SettingsRepository(self.db)
        result = repo.get_all()
        self.assertIsInstance(result, dict)

    def test_save_and_get_all(self):
        repo = SettingsRepository(self.db)
        result = repo.save({"selected_provider": "test"})
        self.assertTrue(result["success"])
        prefs = repo.get_all()
        self.assertEqual(prefs.get("selected_provider"), "test")

    def test_save_updates_existing(self):
        repo = SettingsRepository(self.db)
        repo.save({"key1": "value1"})
        repo.save({"key1": "value2"})
        prefs = repo.get_all()
        self.assertEqual(prefs["key1"], "value2")

    def test_parse_value_json(self):
        result = safe_json_loads('"hello"', fallback="hello")
        self.assertEqual(result, "hello")

    def test_parse_value_plain_string(self):
        result = safe_json_loads("not_json", fallback="not_json")
        self.assertEqual(result, "not_json")


if __name__ == '__main__':
    unittest.main()
