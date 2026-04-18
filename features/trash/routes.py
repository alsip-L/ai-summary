# -*- coding: utf-8 -*-
"""回收站 API 路由"""

from flask import Blueprint, jsonify
from .service import TrashService

trash_bp = Blueprint("api_trash", __name__, url_prefix="/api/settings/trash")

_svc = TrashService()


@trash_bp.get("/")
def get_trash():
    """GET /api/settings/trash/"""
    return jsonify(_svc.get_all())


@trash_bp.post("/restore/provider/<name>")
def restore_provider(name: str):
    """POST /api/settings/trash/restore/provider/<name>"""
    result = _svc.restore_provider(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@trash_bp.post("/restore/prompt/<name>")
def restore_prompt(name: str):
    """POST /api/settings/trash/restore/prompt/<name>"""
    result = _svc.restore_prompt(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@trash_bp.delete("/provider/<name>")
def permanent_delete_provider(name: str):
    """DELETE /api/settings/trash/provider/<name>"""
    result = _svc.permanent_delete_provider(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@trash_bp.delete("/prompt/<name>")
def permanent_delete_prompt(name: str):
    """DELETE /api/settings/trash/prompt/<name>"""
    result = _svc.permanent_delete_prompt(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400
