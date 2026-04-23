# -*- coding: utf-8 -*-
from app.repositories.settings_repo import SettingsRepository
from core.config import ConfigManager
from core.log import update_log_level


class SettingsService:
    def __init__(self, settings_repo: SettingsRepository):
        self._repo = settings_repo
        self._config = ConfigManager()

    def get_preferences(self) -> dict:
        return self._repo.get_all()

    def save_preferences(self, data: dict) -> dict:
        return self._repo.save(data)

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
        if "admin_username" in data and data["admin_username"].strip():
            current["admin_username"] = data["admin_username"].strip()
        if "admin_password" in data and data["admin_password"].strip():
            current["admin_password"] = data["admin_password"].strip()
        if "allowed_paths" in data:
            current["allowed_paths"] = data["allowed_paths"]

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
