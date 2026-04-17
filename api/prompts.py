# -*- coding: utf-8 -*-
"""提示词 API"""

from flask import Blueprint, request, jsonify
from repositories.prompt_repo import PromptRepository
from repositories.trash_repo import TrashRepository
from models.prompt import PromptConfig
from core.config import ConfigManager

prompt_bp = Blueprint("api_prompts", __name__, url_prefix="/api/prompts")


def _repo() -> PromptRepository:
    return PromptRepository(ConfigManager())


@prompt_bp.get("/")
def list_prompts():
    """GET /api/prompts/"""
    prompts = _repo().get_all()
    return jsonify({name: p.content for name, p in prompts.items()})


@prompt_bp.post("/")
def create_prompt():
    """POST /api/prompts/"""
    data = request.get_json()
    prompt = PromptConfig(name=data.get("name", ""), content=data.get("content", ""))
    if _repo().save(prompt):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "保存失败"}), 400


@prompt_bp.delete("/<name>")
def delete_prompt(name: str):
    """DELETE /api/prompts/<name> — 移入回收站"""
    trash_repo = TrashRepository(ConfigManager())
    if trash_repo.move_prompt_to_trash(name):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "删除失败"}), 400
