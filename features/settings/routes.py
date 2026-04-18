# -*- coding: utf-8 -*-
"""设置 API 路由"""

from flask import Blueprint, request, jsonify
from .service import SettingsService

settings_bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")

_svc = SettingsService()


@settings_bp.get("/system")
def get_system_settings():
    """GET /api/settings/system"""
    return jsonify(_svc.get_system_settings())


@settings_bp.put("/system")
def save_system_settings():
    """PUT /api/settings/system"""
    try:
        data = request.get_json()
        result = _svc.save_system_settings(data)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.get("/preferences")
def get_preferences():
    """GET /api/settings/preferences"""
    return jsonify(_svc.get_preferences())


@settings_bp.put("/preferences")
def save_preferences():
    """PUT /api/settings/preferences"""
    data = request.get_json()
    result = _svc.save_preferences(data)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400
