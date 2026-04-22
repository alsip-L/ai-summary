# -*- coding: utf-8 -*-
"""Tests for repository layer using new SQLAlchemy architecture."""

import unittest
import os
import json
import shutil
import tempfile

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.database import Base, DB_PATH
from app.models import Provider, Prompt
from app.repositories.provider_repo import ProviderRepository
from app.repositories.prompt_repo import PromptRepository
from app.repositories.trash_repo import TrashRepository


from .conftest import _backup_production_db, _ensure_soft_delete_columns


class _BaseDBTest(unittest.TestCase):

    def setUp(self):
        self._db_path = _backup_production_db()
        self._engine = create_engine(f"sqlite:///{self._db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self._engine)
        _ensure_soft_delete_columns(self._engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        self.db = TestSessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        self._engine.dispose()
        os.unlink(self._db_path)


class TestProviderRepository(_BaseDBTest):

    def test_save_and_get(self):
        repo = ProviderRepository(self.db)
        data = {"name": "TestProvider", "base_url": "https://test.com", "api_key": "test_key", "models": {"m1": "id1"}}
        self.assertTrue(repo.save(data))
        result = repo.get("TestProvider")
        self.assertIsNotNone(result)
        self.assertEqual(result["base_url"], "https://test.com")

    def test_get_all(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "P1", "base_url": "https://p1.com", "api_key": "k1", "models": {}})
        repo.save({"name": "P2", "base_url": "https://p2.com", "api_key": "k2", "models": {}})
        all_providers = repo.get_all()
        self.assertIn("P1", all_providers)
        self.assertIn("P2", all_providers)

    def test_soft_delete(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "ToDelete", "base_url": "https://t.com", "api_key": "k", "models": {}})
        self.assertTrue(repo.soft_delete("ToDelete"))
        self.assertIsNone(repo.get("ToDelete"))
        self.assertNotIn("ToDelete", repo.get_all())

    def test_restore(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "ToRestore", "base_url": "https://t.com", "api_key": "k", "models": {}})
        repo.soft_delete("ToRestore")
        self.assertTrue(repo.restore("ToRestore"))
        self.assertIsNotNone(repo.get("ToRestore"))

    def test_permanent_delete(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "ToPermDelete", "base_url": "https://t.com", "api_key": "k", "models": {}})
        repo.soft_delete("ToPermDelete")
        self.assertTrue(repo.permanent_delete("ToPermDelete"))
        self.assertNotIn("ToPermDelete", repo.get_all_deleted())

    def test_get_all_deleted(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        repo.save({"name": "P2", "base_url": "https://p.com", "api_key": "k", "models": {}})
        repo.soft_delete("P1")
        deleted = repo.get_all_deleted()
        self.assertIn("P1", deleted)
        self.assertNotIn("P2", deleted)

    def test_save_restores_soft_deleted_record(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        repo.soft_delete("P1")
        self.assertTrue(repo.save({"name": "P1", "base_url": "https://new.com", "api_key": "k2", "models": {}}))
        result = repo.get("P1")
        self.assertIsNotNone(result)
        self.assertEqual(result["base_url"], "https://new.com")

    def test_is_deleted_default_false(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "P1", "base_url": "https://p.com", "api_key": "k", "models": {}})
        p = self.db.query(Provider).filter(Provider.name == "P1").first()
        self.assertFalse(p.is_deleted)


class TestPromptRepository(_BaseDBTest):

    def test_save_and_get(self):
        repo = PromptRepository(self.db)
        self.assertTrue(repo.save("TestPrompt", "Test content"))
        result = repo.get("TestPrompt")
        self.assertEqual(result, "Test content")

    def test_get_all(self):
        repo = PromptRepository(self.db)
        existing_count = len(repo.get_all())
        repo.save("P1", "Content 1")
        repo.save("P2", "Content 2")
        all_prompts = repo.get_all()
        self.assertEqual(len(all_prompts), existing_count + 2)

    def test_soft_delete(self):
        repo = PromptRepository(self.db)
        repo.save("ToDelete", "Content")
        self.assertTrue(repo.soft_delete("ToDelete"))
        self.assertIsNone(repo.get("ToDelete"))
        self.assertNotIn("ToDelete", repo.get_all())

    def test_restore(self):
        repo = PromptRepository(self.db)
        repo.save("ToRestore", "Content")
        repo.soft_delete("ToRestore")
        self.assertTrue(repo.restore("ToRestore"))
        self.assertEqual(repo.get("ToRestore"), "Content")

    def test_permanent_delete(self):
        repo = PromptRepository(self.db)
        repo.save("ToPermDelete", "Content")
        repo.soft_delete("ToPermDelete")
        self.assertTrue(repo.permanent_delete("ToPermDelete"))
        self.assertNotIn("ToPermDelete", repo.get_all_deleted())

    def test_get_all_deleted(self):
        repo = PromptRepository(self.db)
        repo.save("P1", "Content 1")
        repo.save("P2", "Content 2")
        repo.soft_delete("P1")
        deleted = repo.get_all_deleted()
        self.assertIn("P1", deleted)
        self.assertNotIn("P2", deleted)

    def test_save_restores_soft_deleted_record(self):
        repo = PromptRepository(self.db)
        repo.save("P1", "old content")
        repo.soft_delete("P1")
        self.assertTrue(repo.save("P1", "new content"))
        self.assertEqual(repo.get("P1"), "new content")


class TestTrashRepository(_BaseDBTest):

    def test_move_provider_to_trash(self):
        ProviderRepository(self.db).save({"name": "TestProvider", "base_url": "https://test.com", "api_key": "key", "models": {}})
        repo = TrashRepository(self.db)
        self.assertTrue(repo.move_provider_to_trash("TestProvider"))
        trash = repo.get_all()
        self.assertIn("TestProvider", trash["providers"])

    def test_restore_provider(self):
        ProviderRepository(self.db).save({"name": "TestProvider", "base_url": "https://test.com", "api_key": "key", "models": {}})
        repo = TrashRepository(self.db)
        repo.move_provider_to_trash("TestProvider")
        self.assertTrue(repo.restore_provider("TestProvider"))
        provider_repo = ProviderRepository(self.db)
        self.assertIsNotNone(provider_repo.get("TestProvider"))

    def test_permanent_delete(self):
        ProviderRepository(self.db).save({"name": "TestProvider", "base_url": "https://test.com", "api_key": "key", "models": {}})
        repo = TrashRepository(self.db)
        repo.move_provider_to_trash("TestProvider")
        self.assertTrue(repo.permanent_delete_provider("TestProvider"))
        trash = repo.get_all()
        self.assertNotIn("TestProvider", trash.get("providers", {}))


if __name__ == '__main__':
    unittest.main()
