# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import Session
from app.models import Provider
from core.log import get_logger

logger = get_logger()


def _safe_json_loads(json_str: str) -> dict:
    """安全解析JSON，失败时返回空字典"""
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"JSON解析失败，降级为空字典: {str(json_str)[:50]}")
        return {}


class ProviderRepository:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def get_all(self) -> dict[str, dict]:
        providers = self._db.query(Provider).filter(Provider.is_active == True).all()
        result = {}
        for p in providers:
            result[p.name] = {
                "name": p.name,
                "base_url": p.base_url,
                "api_key": p.api_key,
                "models": _safe_json_loads(p.models_json),
                "is_active": p.is_active,
            }
        return result

    def get(self, name: str) -> dict | None:
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_active == True).first()
        if not p:
            return None
        return {
            "name": p.name,
            "base_url": p.base_url,
            "api_key": p.api_key,
            "models": _safe_json_loads(p.models_json),
            "is_active": p.is_active,
        }

    def _get_raw(self, name: str) -> dict | None:
        """获取未脱敏的完整provider数据（供TaskService使用）"""
        p = self._db.query(Provider).filter(Provider.name == name, Provider.is_active == True).first()
        if not p:
            return None
        return {
            "name": p.name,
            "base_url": p.base_url,
            "api_key": p.api_key,
            "models": _safe_json_loads(p.models_json),
            "is_active": p.is_active,
        }

    def save(self, data: dict, auto_commit: bool = True) -> bool:
        try:
            name = data["name"]
            p = self._db.query(Provider).filter(Provider.name == name).first()
            if p:
                p.base_url = data.get("base_url", p.base_url)
                p.api_key = data.get("api_key", p.api_key)
                p.models_json = json.dumps(data.get("models", {}), ensure_ascii=False)
                if "is_active" in data:
                    p.is_active = data["is_active"]
                logger.info(f"更新服务商: {name}")
            else:
                p = Provider(
                    name=name,
                    base_url=data.get("base_url", ""),
                    api_key=data.get("api_key", ""),
                    models_json=json.dumps(data.get("models", {}), ensure_ascii=False),
                    is_active=data.get("is_active", True),
                )
                self._db.add(p)
                logger.info(f"新增服务商: {name}")
            if auto_commit:
                self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def update_api_key(self, name: str, api_key: str) -> bool:
        try:
            p = self._db.query(Provider).filter(Provider.name == name).first()
            if not p:
                return False
            p.api_key = api_key
            self._db.commit()
            logger.info(f"更新API Key: {name}")
            return True
        except Exception:
            self._db.rollback()
            return False

    def add_model_variant(self, provider_name: str, display_name: str, model_id: str) -> bool:
        try:
            p = self._db.query(Provider).filter(Provider.name == provider_name).first()
            if not p:
                return False
            models = _safe_json_loads(p.models_json)
            models[display_name] = model_id
            p.models_json = json.dumps(models, ensure_ascii=False)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def delete_model(self, provider_name: str, model_name: str) -> bool:
        try:
            p = self._db.query(Provider).filter(Provider.name == provider_name).first()
            if not p:
                return False
            models = _safe_json_loads(p.models_json)
            if model_name not in models:
                return False
            del models[model_name]
            p.models_json = json.dumps(models, ensure_ascii=False)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def remove(self, name: str) -> dict | None:
        try:
            p = self._db.query(Provider).filter(Provider.name == name).first()
            if not p:
                return None
            data = {
                "name": p.name,
                "base_url": p.base_url,
                "api_key": p.api_key,
                "models": _safe_json_loads(p.models_json),
                "is_active": p.is_active,
            }
            self._db.delete(p)
            self._db.commit()
            logger.info(f"删除服务商: {name}")
            return data
        except Exception:
            self._db.rollback()
            return None
