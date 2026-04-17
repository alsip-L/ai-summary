# -*- coding: utf-8 -*-
"""设置 API"""

from flask import Blueprint, request, jsonify
from repositories.trash_repo import TrashRepository
from core.config import ConfigManager
from core.log import get_logger, update_log_level

logger = get_logger()
settings_bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


@settings_bp.get("/trash")
def get_trash():
    """GET /api/settings/trash"""
    return jsonify(TrashRepository(ConfigManager()).get_all())


@settings_bp.post("/trash/restore/provider/<name>")
def restore_provider(name: str):
    if TrashRepository(ConfigManager()).restore_provider(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "恢复失败"}), 400


@settings_bp.post("/trash/restore/prompt/<name>")
def restore_prompt(name: str):
    if TrashRepository(ConfigManager()).restore_prompt(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "恢复失败"}), 400


@settings_bp.delete("/trash/provider/<name>")
def permanent_delete_provider(name: str):
    if TrashRepository(ConfigManager()).permanent_delete_provider(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400


@settings_bp.delete("/trash/prompt/<name>")
def permanent_delete_prompt(name: str):
    if TrashRepository(ConfigManager()).permanent_delete_prompt(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400


@settings_bp.get("/system")
def get_system_settings():
    """GET /api/settings/system"""
    return jsonify(ConfigManager().get("system_settings", {}))


@settings_bp.put("/system")
def save_system_settings():
    """PUT /api/settings/system"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400

        config = ConfigManager()
        current = config.get("system_settings", {})

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
                return jsonify({"success": False, "error": "端口必须为数字"}), 400
        if "debug" in data:
            current["debug"] = bool(data["debug"])

        if config.set("system_settings", current):
            if current.get("debug_level") != old_debug_level:
                update_log_level(current["debug_level"])

            needs_restart = (
                current.get("host") != old_host
                or current.get("port") != old_port
                or current.get("flask_secret_key") != old_secret
                or current.get("debug") != old_debug
            )
            return jsonify({"success": True, "needs_restart": needs_restart})
        return jsonify({"success": False, "error": "保存失败"}), 500
    except Exception as e:
        logger.error(f"保存系统设置失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.get("/preferences")
def get_preferences():
    """GET /api/settings/preferences"""
    return jsonify(ConfigManager().get("user_preferences", {}))


@settings_bp.put("/preferences")
def save_preferences():
    """PUT /api/settings/preferences"""
    data = request.get_json()
    config = ConfigManager()
    current = config.get("user_preferences", {})
    current.update(data)
    if config.set("user_preferences", current):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "保存失败"}), 400
