# -*- coding: utf-8 -*-
"""Tests for repository layer using new SQLAlchemy architecture."""

import unittest
import os
import json

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models import Provider, Prompt, TrashProvider, TrashPrompt
from app.services.provider_repo import ProviderRepository
from app.services.prompt_repo import PromptRepository
from app.services.trash_repo import TrashRepository


class _BaseDBTest(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()


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

    def test_remove(self):
        repo = ProviderRepository(self.db)
        repo.save({"name": "ToRemove", "base_url": "https://t.com", "api_key": "k", "models": {}})
        data = repo.remove("ToRemove")
        self.assertIsNotNone(data)
        self.assertIsNone(repo.get("ToRemove"))


class TestPromptRepository(_BaseDBTest):

    def test_save_and_get(self):
        repo = PromptRepository(self.db)
        self.assertTrue(repo.save("TestPrompt", "Test content"))
        result = repo.get("TestPrompt")
        self.assertEqual(result, "Test content")

    def test_get_all(self):
        repo = PromptRepository(self.db)
        repo.save("P1", "Content 1")
        repo.save("P2", "Content 2")
        all_prompts = repo.get_all()
        self.assertEqual(len(all_prompts), 2)

    def test_remove(self):
        repo = PromptRepository(self.db)
        repo.save("ToDelete", "Content")
        content = repo.remove("ToDelete")
        self.assertEqual(content, "Content")
        self.assertIsNone(repo.get("ToDelete"))


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
