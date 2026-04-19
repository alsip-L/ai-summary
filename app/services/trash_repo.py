# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import Session
from app.models import TrashProvider, TrashPrompt, Provider, Prompt
from app.services.provider_repo import ProviderRepository, _safe_json_loads
from app.services.prompt_repo import PromptRepository
from core.log import get_logger

logger = get_logger()


class TrashRepository:
    def __init__(self, db: Session):
        self._db = db
        self._provider_repo = ProviderRepository(db)
        self._prompt_repo = PromptRepository(db)

    def get_all(self) -> dict:
        trash_providers = self._db.query(TrashProvider).all()
        trash_prompts = self._db.query(TrashPrompt).all()

        providers = {}
        for tp in trash_providers:
            providers[tp.name] = {
                "name": tp.name,
                "base_url": tp.base_url,
                "api_key": tp.api_key,
                "models": _safe_json_loads(tp.models_json),
                "is_active": tp.is_active,
            }

        prompts = {}
        for tp in trash_prompts:
            prompts[tp.name] = tp.content

        return {"providers": providers, "custom_prompts": prompts}

    def move_provider_to_trash(self, name: str) -> bool:
        try:
            data = self._provider_repo.remove(name)
            if not data:
                return False
            tp = TrashProvider(
                name=data["name"],
                base_url=data["base_url"],
                api_key=data["api_key"],
                models_json=json.dumps(data.get("models", {}), ensure_ascii=False),
                is_active=data.get("is_active", True),
            )
            self._db.add(tp)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def move_prompt_to_trash(self, name: str) -> bool:
        try:
            content = self._prompt_repo.remove(name)
            if content is None:
                return False
            tp = TrashPrompt(name=name, content=content)
            self._db.add(tp)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def restore_provider(self, name: str) -> bool:
        try:
            tp = self._db.query(TrashProvider).filter(TrashProvider.name == name).first()
            if not tp:
                return False
            data = {
                "name": tp.name,
                "base_url": tp.base_url,
                "api_key": tp.api_key,
                "models": _safe_json_loads(tp.models_json),
                "is_active": tp.is_active,
            }
            self._db.delete(tp)
            self._provider_repo.save(data, auto_commit=False)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def restore_prompt(self, name: str) -> bool:
        try:
            tp = self._db.query(TrashPrompt).filter(TrashPrompt.name == name).first()
            if not tp:
                return False
            content = tp.content
            self._db.delete(tp)
            self._prompt_repo.save(name, content, auto_commit=False)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def permanent_delete_provider(self, name: str) -> bool:
        try:
            tp = self._db.query(TrashProvider).filter(TrashProvider.name == name).first()
            if not tp:
                return False
            self._db.delete(tp)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def permanent_delete_prompt(self, name: str) -> bool:
        try:
            tp = self._db.query(TrashPrompt).filter(TrashPrompt.name == name).first()
            if not tp:
                return False
            self._db.delete(tp)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False
