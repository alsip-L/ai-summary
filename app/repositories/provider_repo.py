# -*- coding: utf-8 -*-
import json
from app.models import Provider
from app.repositories.base_repo import BaseRepository
from core.utils import safe_json_loads
from core.crypto import encrypt_api_key, decrypt_api_key
from core.log import get_logger

logger = get_logger()


def _mask_api_key(api_key: str) -> str:
    """脱敏API Key，隐藏中间6位。如 sk-abc***xyz -> sk-abc***xyz"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return api_key[:2] + "***" + api_key[-2:] if len(api_key) >= 4 else "***"
    return api_key[:4] + "******" + api_key[-4:]


class ProviderRepository(BaseRepository):

    def _to_dict_masked(self, p: Provider) -> dict:
        """Provider ORM → 字典（API Key 脱敏）"""
        raw_key = decrypt_api_key(p.api_key)
        return {
            "name": p.name,
            "base_url": p.base_url,
            "api_key": _mask_api_key(raw_key),
            "api_key_masked": bool(raw_key),
            "models": safe_json_loads(p.models_json),
            "is_active": p.is_active,
        }

    def _to_dict_raw(self, p: Provider) -> dict:
        """Provider ORM → 字典（API Key 不脱敏）"""
        return {
            "name": p.name,
            "base_url": p.base_url,
            "api_key": decrypt_api_key(p.api_key),
            "models": safe_json_loads(p.models_json),
            "is_active": p.is_active,
        }

    def get_all(self) -> list[dict]:
        providers = self._db.query(Provider).filter(Provider.is_deleted == False).all()
        return [self._to_dict_masked(p) for p in providers]

    def get(self, name: str) -> dict | None:
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
        if not p:
            return None
        return self._to_dict_masked(p)

    def get_raw(self, name: str) -> dict | None:
        """获取未脱敏的完整provider数据（供TaskService使用）"""
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_deleted == False).first()
        if not p:
            return None
        return self._to_dict_raw(p)

    def save(self, data: dict, auto_commit: bool = True) -> bool:
        try:
            with self._write_session(auto_commit):
                name = data["name"]
                p = self._db.query(Provider).filter(Provider.name == name).first()
                if p:
                    p.base_url = data.get("base_url", p.base_url)
                    if "api_key" in data:
                        p.api_key = encrypt_api_key(data["api_key"])
                    p.models_json = json.dumps(data.get("models", {}), ensure_ascii=False)
                    if "is_active" in data:
                        p.is_active = data["is_active"]
                    if p.is_deleted:
                        p.is_deleted = False
                    logger.info(f"更新服务商: {name}")
                else:
                    p = Provider(
                        name=name,
                        base_url=data.get("base_url", ""),
                        api_key=encrypt_api_key(data.get("api_key", "")),
                        models_json=json.dumps(data.get("models", {}), ensure_ascii=False),
                        is_active=data.get("is_active", True),
                    )
                    self._db.add(p)
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
                p.api_key = encrypt_api_key(api_key)
                logger.info(f"更新API Key: {name}")
            return True
        except Exception as e:
            logger.error(f"更新API Key失败: {e}", exc_info=True)
            return False

    def add_model_variant(self, provider_name: str, display_name: str, model_id: str) -> bool:
        try:
            with self._write_session():
                p = self._db.query(Provider).filter(Provider.name == provider_name).first()
                if not p:
                    return False
                models = safe_json_loads(p.models_json)
                models[display_name] = model_id
                p.models_json = json.dumps(models, ensure_ascii=False)
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
        return [self._to_dict_masked(p) for p in providers]
