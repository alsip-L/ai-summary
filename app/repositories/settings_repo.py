# -*- coding: utf-8 -*-
import json
from app.models import UserPreference, ApiKey
from app.repositories.base_repo import BaseRepository
from core.utils import safe_json_loads
from core.log import get_logger

logger = get_logger()


class SettingsRepository(BaseRepository):

    def get_all(self) -> dict:
        """获取所有用户偏好"""
        prefs = self._db.query(UserPreference).all()
        result = {}
        for p in prefs:
            parsed = safe_json_loads(p.value, fallback=p.value) if p.value else ""
            result[p.key] = parsed
        return result

    def get_api_key_raw(self) -> str | None:
        """获取完整 API Key"""
        p = self._db.query(UserPreference).filter(UserPreference.key == "api_key").first()
        if not p or not p.value:
            return None
        parsed = safe_json_loads(p.value, fallback=p.value)
        if isinstance(parsed, str) and parsed:
            return parsed
        return None

    def save(self, data: dict) -> dict:
        """保存用户偏好"""
        try:
            with self._write_session():
                for key, value in data.items():
                    p = self._db.query(UserPreference).filter(UserPreference.key == key).first()
                    if key == "api_key" and isinstance(value, str) and value:
                        str_value = json.dumps(value, ensure_ascii=False)
                    else:
                        str_value = json.dumps(value, ensure_ascii=False)
                    if p:
                        p.value = str_value
                    else:
                        p = UserPreference(key=key, value=str_value)
                        self._db.add(p)
                    # 同步 api_keys 表（仅 api_key 偏好）
                    if key == "api_key" and isinstance(value, str) and value:
                        existing = self._db.query(ApiKey).filter(
                            ApiKey.source == "preference", ApiKey.provider_id.is_(None)
                        ).first()
                        if existing:
                            existing.key_value = value
                        else:
                            self._db.add(ApiKey(provider_id=None, key_value=value, source="preference"))
            return {"success": True}
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}", exc_info=True)
            return {"success": False, "error": f"保存失败: {e}"}
