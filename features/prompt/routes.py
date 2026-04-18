# -*- coding: utf-8 -*-
"""提示词 API 路由"""

from flask import Blueprint, request, jsonify
from .service import PromptService

prompt_bp = Blueprint("api_prompts", __name__, url_prefix="/api/prompts")

_svc = PromptService()


@prompt_bp.get("/")
def list_prompts():
    """GET /api/prompts/"""
    return jsonify(_svc.list_all())


@prompt_bp.post("/")
def create_prompt():
    """POST /api/prompts/"""
    data = request.get_json(silent=True) or {}
    result = _svc.create(data)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@prompt_bp.delete("/<name>")
def delete_prompt(name: str):
    """DELETE /api/prompts/<name> — 移入回收站"""
    result = _svc.delete(name)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400
