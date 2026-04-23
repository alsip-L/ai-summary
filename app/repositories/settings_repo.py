# -*- coding: utf-8 -*-
import json
from app.models import UserPreference
from app.repositories.base_repo import BaseRepository
from core.utils import safe_json_loads
from core.crypto import encrypt_api_key, decrypt_api_key
from core.log import get_logger

logger = get_logger()


class SettingsRepository(BaseRepository):

    def _mask_api_key(self, api_key: str) -> str:
        """脱敏 API Key，隐藏中间部分"""
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return api_key[:2] + "***" + api_key[-2:] if len(api_key) >= 4 else "***"
        return api_key[:4] + "******" + api_key[-4:]

    def get_all(self) -> dict:
        """获取所有用户偏好（api_key 已脱敏）"""
        prefs = self._db.query(UserPreference).all()
        result = {}
        for p in prefs:
            parsed = safe_json_loads(p.value, fallback=p.value) if p.value else ""
            if p.key == "api_key" and isinstance(parsed, str) and parsed:
                raw_key = decrypt_api_key(parsed)
                result[p.key] = self._mask_api_key(raw_key)
                result["api_key_masked"] = bool(raw_key)
            else:
                result[p.key] = parsed
        return result

    def get_api_key_raw(self) -> str | None:
        """获取未脱敏的完整 API Key（仅限认证端点使用）"""
        p = self._db.query(UserPreference).filter(UserPreference.key == "api_key").first()
        if not p or not p.value:
            return None
        parsed = safe_json_loads(p.value, fallback=p.value)
        if isinstance(parsed, str) and parsed:
            return decrypt_api_key(parsed)
        return None

    def save(self, data: dict) -> dict:
        """保存用户偏好"""
        try:
            with self._write_session():
                for key, value in data.items():
                    p = self._db.query(UserPreference).filter(UserPreference.key == key).first()
                    if key == "api_key" and isinstance(value, str) and value:
                        str_value = json.dumps(encrypt_api_key(value), ensure_ascii=False)
                    else:
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
