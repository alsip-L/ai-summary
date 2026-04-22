# -*- coding: utf-8 -*-
import json
from app.models import UserPreference
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
            result[p.key] = safe_json_loads(p.value, fallback=p.value) if p.value else ""
        return result

    def save(self, data: dict) -> dict:
        """保存用户偏好"""
        try:
            with self._write_session():
                for key, value in data.items():
                    p = self._db.query(UserPreference).filter(UserPreference.key == key).first()
                    str_value = json.dumps(value, ensure_ascii=False)
                    if p:
                        p.value = str_value
                    else:
                        p = UserPreference(key=key, value=str_value)
                        self._db.add(p)
            return {"success": True}
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}", exc_info=True)
            return {"success": False, "error": f"保存失败: {e}"}
