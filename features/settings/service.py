# -*- coding: utf-8 -*-
"""系统设置与用户偏好业务逻辑层"""

from core.config import ConfigManager
from core.log import get_logger, update_log_level

logger = get_logger()


class SettingsService:
    """设置服务：系统设置和用户偏好的读写"""

    def __init__(self):
        self._config = ConfigManager()

    def get_system_settings(self) -> dict:
        """获取系统设置"""
        return self._config.get("system_settings", {})

    def save_system_settings(self, data: dict) -> dict:
        """保存系统设置"""
        if not data:
            return {"success": False, "error": "无效的请求数据"}

        current = self._config.get("system_settings", {})

        old_debug_level = current.get("debug_level", "ERROR")
        old_host = current.get("host", "0.0.0.0")
        old_port = current.get("port", 5000)
        old_secret = current.get("flask_secret_key", "")
        old_debug = current.get("debug", False)

        if "debug_level" in data:
            current["debug_level"] = data["debug_level"].upper()
        if "flask_secret_key" in data and data["flask_secret_key"].strip():
            current["flask_secret_key"] = data["flask_secret_key"].strip()
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
                or current.get("flask_secret_key") != old_secret
                or current.get("debug") != old_debug
            )
            return {"success": True, "needs_restart": needs_restart}
        return {"success": False, "error": "保存失败"}

    def get_preferences(self) -> dict:
        """获取用户偏好"""
        return self._config.get("user_preferences", {})

    def save_preferences(self, data: dict) -> dict:
        """保存用户偏好"""
        current = self._config.get("user_preferences", {})
        current.update(data)
        if self._config.set("user_preferences", current):
            return {"success": True}
        return {"success": False, "error": "保存失败"}
