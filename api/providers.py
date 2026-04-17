# -*- coding: utf-8 -*-
"""提供商 API"""

from flask import Blueprint, request, jsonify
from repositories.provider_repo import ProviderRepository
from repositories.trash_repo import TrashRepository
from models.provider import ProviderConfig
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()
provider_bp = Blueprint("api_providers", __name__, url_prefix="/api/providers")


def _repo() -> ProviderRepository:
    return ProviderRepository(ConfigManager())


@provider_bp.get("/")
def list_providers():
    """GET /api/providers/"""
    return jsonify(_repo().get_all_as_dict())


@provider_bp.post("/")
def create_provider():
    """POST /api/providers/ — 创建提供商"""
    data = request.get_json()
    try:
        provider = ProviderConfig(**data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    if _repo().save(provider):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "保存失败"}), 400


@provider_bp.put("/<name>")
def update_provider(name: str):
    """PUT /api/providers/<name>"""
    data = request.get_json()
    data["name"] = name
    try:
        provider = ProviderConfig(**data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    if _repo().save(provider):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "更新失败"}), 400


@provider_bp.delete("/<name>")
def delete_provider(name: str):
    """DELETE /api/providers/<name> — 移入回收站"""
    trash_repo = TrashRepository(ConfigManager())
    if trash_repo.move_provider_to_trash(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400


@provider_bp.put("/<name>/api-key")
def update_api_key(name: str):
    """PUT /api/providers/<name>/api-key"""
    api_key = request.get_json().get("api_key", "")
    if _repo().update_api_key(name, api_key):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "更新失败"}), 400


@provider_bp.post("/<name>/models")
def add_model(name: str):
    """POST /api/providers/<name>/models"""
    data = request.get_json()
    if _repo().add_model_variant(name, data.get("display_name", ""), data.get("model_id", "")):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "添加失败"}), 400


@provider_bp.delete("/<name>/models/<model_name>")
def delete_model(name: str, model_name: str):
    """DELETE /api/providers/<name>/models/<model_name>"""
    if _repo().delete_model(name, model_name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400
