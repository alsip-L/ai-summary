# -*- coding: utf-8 -*-
"""提供商 API 路由"""

from flask import Blueprint, request, jsonify
from .service import ProviderService

provider_bp = Blueprint("api_providers", __name__, url_prefix="/api/providers")

_svc = ProviderService()


@provider_bp.get("/")
def list_providers():
    """GET /api/providers/"""
    return jsonify(_svc.list_all())


@provider_bp.post("/")
def create_provider():
    """POST /api/providers/ — 创建提供商"""
    data = request.get_json(silent=True) or {}
    result = _svc.create(data)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@provider_bp.delete("/<name>")
def delete_provider(name: str):
    """DELETE /api/providers/<name> — 移入回收站"""
    result = _svc.delete(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@provider_bp.put("/<name>/api-key")
def update_api_key(name: str):
    """PUT /api/providers/<name>/api-key"""
    api_key = (request.get_json(silent=True) or {}).get("api_key", "")
    result = _svc.update_api_key(name, api_key)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@provider_bp.post("/<name>/models")
def add_model(name: str):
    """POST /api/providers/<name>/models"""
    data = request.get_json(silent=True) or {}
    result = _svc.add_model(name, data.get("display_name", ""), data.get("model_id", ""))
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@provider_bp.delete("/<name>/models/<model_name>")
def delete_model(name: str, model_name: str):
    """DELETE /api/providers/<name>/models/<model_name>"""
    result = _svc.delete_model(name, model_name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400
