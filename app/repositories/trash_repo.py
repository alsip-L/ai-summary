# -*- coding: utf-8 -*-
import json
from app.models import Provider, Prompt, Model, ApiKey, Trash
from app.repositories.base_repo import BaseRepository
from app.repositories.provider_repo import ProviderRepository
from app.repositories.prompt_repo import PromptRepository
from core.log import get_logger

logger = get_logger()


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
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
                if not p:
                    return False
                p.is_deleted = True
                item_data = json.dumps({
                    "name": p.name, "base_url": p.base_url,
                    "api_key": p.api_key, "models_json": p.models_json,
                    "is_active": p.is_active,
                }, ensure_ascii=False)
                existing = self._db.query(Trash).filter(Trash.item_type == "provider", Trash.item_id == p.id).first()
                if not existing:
                    self._db.add(Trash(item_type="provider", item_id=p.id, item_name=p.name, item_data=item_data))
                logger.info(f"软删除服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"移入回收站失败: {e}", exc_info=True)
            return False

    def move_prompt_to_trash(self, name: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == False).first()
                if not p:
                    return False
                p.is_deleted = True
                item_data = json.dumps({"name": p.name, "content": p.content}, ensure_ascii=False)
                existing = self._db.query(Trash).filter(Trash.item_type == "prompt", Trash.item_id == p.id).first()
                if not existing:
                    self._db.add(Trash(item_type="prompt", item_id=p.id, item_name=p.name, item_data=item_data))
                logger.info(f"软删除提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"移入回收站失败: {e}", exc_info=True)
            return False

    def restore_provider(self, name: str) -> bool:
        return self._provider_repo.restore(name)

    def restore_prompt(self, name: str) -> bool:
        return self._prompt_repo.restore(name)

    def permanent_delete_provider(self, name: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == True).first()
                if not p:
                    return False
                # 级联删除关联的 Model 和 ApiKey 记录
                self._db.query(Model).filter(Model.provider_id == p.id).delete()
                self._db.query(ApiKey).filter(ApiKey.provider_id == p.id).delete()
                self._db.delete(p)
                self._db.query(Trash).filter(Trash.item_type == "provider", Trash.item_name == name).delete()
                logger.info(f"永久删除服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"永久删除失败: {e}", exc_info=True)
            return False

    def permanent_delete_prompt(self, name: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == True).first()
                if not p:
                    return False
                self._db.delete(p)
                self._db.query(Trash).filter(Trash.item_type == "prompt", Trash.item_name == name).delete()
                logger.info(f"永久删除提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"永久删除失败: {e}", exc_info=True)
            return False
