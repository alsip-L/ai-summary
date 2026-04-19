# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import Session
from app.models import UserPreference
from core.config import ConfigManager
from core.log import update_log_level


class SettingsService:
    def __init__(self, db: Session):
        self._db = db
        self._config = ConfigManager()

    def get_preferences(self) -> dict:
        prefs = self._db.query(UserPreference).all()
        result = {}
        for p in prefs:
            result[p.key] = self._parse_value(p.value)
        return result

    def save_preferences(self, data: dict) -> dict:
        try:
            for key, value in data.items():
                p = self._db.query(UserPreference).filter(UserPreference.key == key).first()
                str_value = json.dumps(value, ensure_ascii=False)
                if p:
                    p.value = str_value
                else:
                    p = UserPreference(key=key, value=str_value)
                    self._db.add(p)
            self._db.commit()
            return {"success": True}
        except Exception:
            self._db.rollback()
            return {"success": False, "error": "保存失败"}

    def get_system_settings(self) -> dict:
        return self._config.get("system_settings", {})

    def save_system_settings(self, data: dict) -> dict:
        if not data:
            return {"success": False, "error": "无效的请求数据"}

        current = self._config.get("system_settings", {})

        old_debug_level = current.get("debug_level", "ERROR")
        old_host = current.get("host", "0.0.0.0")
        old_port = current.get("port", 5000)
        old_secret = current.get("secret_key", "")
        old_debug = current.get("debug", False)

        if "debug_level" in data:
            current["debug_level"] = data["debug_level"].upper()
        if "secret_key" in data and data["secret_key"].strip():
            current["secret_key"] = data["secret_key"].strip()
        if "host" in data:
            current["host"] = data["host"].strip()
        if "port" in data:
            try:
                current["port"] = int(data["port"])
            except (ValueError, TypeError):
                return {"success": False, "error": "端口必须为数字"}
        if "debug" in data:
            current["debug"] = bool(data["debug"])

        if self._config.set("system_settings", current):
            if current.get("debug_level") != old_debug_level:
                update_log_level(current["debug_level"])

            needs_restart = (
                current.get("host") != old_host
                or current.get("port") != old_port
                or current.get("secret_key") != old_secret
                or current.get("debug") != old_debug
            )
            return {"success": True, "needs_restart": needs_restart}
        return {"success": False, "error": "保存失败"}

    @staticmethod
    def _parse_value(value: str):
        if not value:
            return ""
        try:
            parsed = json.loads(value)
            return parsed
        except (json.JSONDecodeError, TypeError):
            return value
