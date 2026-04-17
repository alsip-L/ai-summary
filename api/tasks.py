# -*- coding: utf-8 -*-
"""任务 API"""

import os
import threading
from flask import Blueprint, request, jsonify
from openai import OpenAI
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from services.processing_service import ProcessingService
from services.state_service import ProcessingState
from core.config import ConfigManager

task_bp = Blueprint("api_tasks", __name__, url_prefix="/api/tasks")


@task_bp.post("/start")
def start_task():
    """POST /api/tasks/start"""
    data = request.get_json()
    provider_name = data.get("provider", "")
    model_key = data.get("model", "")
    api_key = data.get("api_key", "")
    prompt_name = data.get("prompt", "")
    directory = data.get("directory", "")

    if not api_key:
        return jsonify({"success": False, "error": "API Key 未配置"}), 400

    # 验证目录
    if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
        return jsonify({"success": False, "error": "请提供有效的目录路径"}), 400

    config = ConfigManager()
    provider_repo = ProviderRepository(config)
    prompt_repo = PromptRepository(config)

    # 验证提供商
    provider = provider_repo.get(provider_name)
    if not provider:
        return jsonify({"success": False, "error": f"提供商 '{provider_name}' 未找到"}), 400

    # 验证模型
    if model_key not in provider.models:
        return jsonify({"success": False, "error": f"模型 '{model_key}' 未找到"}), 400
    model_id = provider.models[model_key]

    # 验证提示词
    prompt = prompt_repo.get(prompt_name)
    if not prompt:
        return jsonify({"success": False, "error": f"Prompt '{prompt_name}' 未找到"}), 400
    prompt_content = prompt.content

    # 启动后台线程
    client = OpenAI(api_key=api_key, base_url=provider.base_url)
    state = ProcessingState()
    service = ProcessingService(state)

    thread = threading.Thread(
        target=service.run_batch,
        args=(directory, client, prompt_content, model_id),
        daemon=True,
    )
    thread.start()

    return jsonify({"success": True, "message": "处理已启动"})


@task_bp.get("/status")
def get_status():
    """GET /api/tasks/status"""
    state = ProcessingState()
    return jsonify(state.get_dict())


@task_bp.post("/cancel")
def cancel_task():
    """POST /api/tasks/cancel"""
    state = ProcessingState()
    state_dict = state.get_dict()
    if state_dict["status"] not in ["processing", "scanning", "started", "idle"]:
        return jsonify({"success": False, "error": "当前没有正在进行的处理任务"}), 400
    state.set_cancelled()
    if state.is_running():
        state.cancel()
    return jsonify({"success": True, "message": "处理已取消"})
