# -*- coding: utf-8 -*-
import json
from app.models import Provider, Model, ApiKey
from app.repositories.base_repo import BaseRepository
from core.utils import safe_json_loads
from core.log import get_logger

logger = get_logger()


class ProviderRepository(BaseRepository):

    def _to_dict(self, p: Provider) -> dict:
        """Provider ORM → 字典"""
        models_simple = safe_json_loads(p.models_json)
        models_detail = {}
        for m in self._db.query(Model).filter(Model.provider_id == p.id).all():
            models_detail[m.display_name] = {
                "model_id": m.model_id,
                "temperature": m.temperature,
                "frequency_penalty": m.frequency_penalty,
                "presence_penalty": m.presence_penalty,
            }
        return {
            "name": p.name,
            "base_url": p.base_url,
            "api_key": p.api_key,
            "models": models_simple,
            "models_detail": models_detail,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    def get_all(self) -> list[dict]:
        providers = self._db.query(Provider).filter(Provider.is_deleted == False).all()
        return [self._to_dict(p) for p in providers]

    def get(self, name: str) -> dict | None:
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
        if not p:
            return None
        return self._to_dict(p)

    def get_raw(self, name: str) -> dict | None:
        """获取完整provider数据（供TaskService使用）"""
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
        if not p:
            return None
        return self._to_dict(p)

    def save(self, data: dict, auto_commit: bool = True) -> bool:
        try:
            with self._write_session(auto_commit):
                name = data["name"]
                models_dict = data.get("models", {})
                p = self._db.query(Provider).filter(Provider.name == name).first()
                if p:
                    p.base_url = data.get("base_url", p.base_url)
                    if "api_key" in data:
                        p.api_key = data["api_key"]
                        # 同步 api_keys 表
                        existing_key = self._db.query(ApiKey).filter(
                            ApiKey.provider_id == p.id, ApiKey.source == "provider"
                        ).first()
                        if existing_key:
                            existing_key.key_value = data["api_key"]
                        else:
                            self._db.add(ApiKey(provider_id=p.id, key_value=data["api_key"], source="provider"))
                    p.models_json = json.dumps(models_dict, ensure_ascii=False)
                    existing_models = {m.display_name: m for m in self._db.query(Model).filter(Model.provider_id == p.id).all()}
                    new_display_names = set(models_dict.keys())
                    for display_name in set(existing_models.keys()) - new_display_names:
                        self._db.delete(existing_models[display_name])
                    for display_name, model_id in models_dict.items():
                        existing = existing_models.get(display_name)
                        if existing:
                            existing.model_id = model_id
                        else:
                            self._db.add(Model(provider_id=p.id, display_name=display_name, model_id=model_id, temperature=0.7, frequency_penalty=0.4, presence_penalty=0.2))
                    if "is_active" in data:
                        p.is_active = data["is_active"]
                    if p.is_deleted:
                        p.is_deleted = False
                    logger.info(f"更新服务商: {name}")
                else:
                    p = Provider(
                        name=name,
                        base_url=data.get("base_url", ""),
                        api_key=data.get("api_key", ""),
                        models_json=json.dumps(models_dict, ensure_ascii=False),
                        is_active=data.get("is_active", True),
                    )
                    self._db.add(p)
                    self._db.flush()  # 获取 p.id
                    # 同步 api_keys 表
                    if data.get("api_key", ""):
                        self._db.add(ApiKey(provider_id=p.id, key_value=data["api_key"], source="provider"))
                    # 同步 models 表
                    for display_name, model_id in models_dict.items():
                        self._db.add(Model(provider_id=p.id, display_name=display_name, model_id=model_id, temperature=0.7, frequency_penalty=0.4, presence_penalty=0.2))
                    logger.info(f"新增服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"保存服务商失败: {e}", exc_info=True)
            return False

    def update_api_key(self, name: str, api_key: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name).first()
                if not p:
                    return False
                p.api_key = api_key
                # 同步 api_keys 表
                existing_key = self._db.query(ApiKey).filter(
                    ApiKey.provider_id == p.id, ApiKey.source == "provider"
                ).first()
                if existing_key:
                    existing_key.key_value = api_key
                else:
                    self._db.add(ApiKey(provider_id=p.id, key_value=api_key, source="provider"))
                logger.info(f"更新API Key: {name}")
            return True
        except Exception as e:
            logger.error(f"更新API Key失败: {e}", exc_info=True)
            return False

    def add_model_variant(self, provider_name: str, display_name: str, model_id: str, temperature: float = 0.7, frequency_penalty: float = 0.4, presence_penalty: float = 0.2) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == provider_name).first()
                if not p:
                    return False
                models = safe_json_loads(p.models_json)
                models[display_name] = model_id
                p.models_json = json.dumps(models, ensure_ascii=False)
                self._db.add(Model(provider_id=p.id, display_name=display_name, model_id=model_id, temperature=temperature, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty))
            return True
        except Exception as e:
            logger.error(f"添加模型变体失败: {e}", exc_info=True)
            return False

    def delete_model(self, provider_name: str, model_name: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == provider_name).first()
                if not p:
                    return False
                models = safe_json_loads(p.models_json)
                if model_name not in models:
                    return False
                del models[model_name]
                p.models_json = json.dumps(models, ensure_ascii=False)
                # 同步 models 表
                self._db.query(Model).filter(
                    Model.provider_id == p.id, Model.display_name == model_name
                ).delete()
            return True
        except Exception as e:
            logger.error(f"删除模型失败: {e}", exc_info=True)
            return False

    def soft_delete(self, name: str) -> bool:
        """软删除：设置 is_deleted=True"""
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
                if not p:
                    return False
                p.is_deleted = True
                logger.info(f"软删除服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"软删除服务商失败: {e}", exc_info=True)
            return False

    def restore(self, name: str) -> bool:
        """恢复：设置 is_deleted=False"""
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == True).first()
                if not p:
                    return False
                active = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
                if active:
                    return False
                p.is_deleted = False
                logger.info(f"恢复服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"恢复服务商失败: {e}", exc_info=True)
            return False

    def permanent_delete(self, name: str) -> bool:
        """永久删除：从数据库中物理移除"""
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == True).first()
                if not p:
                    return False
                self._db.delete(p)
                logger.info(f"永久删除服务商: {name}")
            return True
        except Exception as e:
            logger.error(f"永久删除服务商失败: {e}", exc_info=True)
            return False

    def get_all_deleted(self) -> list[dict]:
        """获取所有已软删除的 Provider"""
        providers = self._db.query(Provider).filter(Provider.is_deleted == True).all()
        return [self._to_dict(p) for p in providers]
