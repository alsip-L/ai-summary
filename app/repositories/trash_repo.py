# -*- coding: utf-8 -*-
from app.repositories.base_repo import BaseRepository
from app.repositories.provider_repo import ProviderRepository
from app.repositories.prompt_repo import PromptRepository


class TrashRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self._provider_repo = ProviderRepository(db)
        self._prompt_repo = PromptRepository(db)

    def get_all(self) -> dict:
        providers = self._provider_repo.get_all_deleted()
        prompts = self._prompt_repo.get_all_deleted()
        return {"providers": providers, "custom_prompts": prompts}

    def move_provider_to_trash(self, name: str) -> bool:
        return self._provider_repo.soft_delete(name)

    def move_prompt_to_trash(self, name: str) -> bool:
        return self._prompt_repo.soft_delete(name)

    def restore_provider(self, name: str) -> bool:
        return self._provider_repo.restore(name)

    def restore_prompt(self, name: str) -> bool:
        return self._prompt_repo.restore(name)

    def permanent_delete_provider(self, name: str) -> bool:
        return self._provider_repo.permanent_delete(name)

    def permanent_delete_prompt(self, name: str) -> bool:
        return self._prompt_repo.permanent_delete(name)
