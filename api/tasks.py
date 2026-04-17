# -*- coding: utf-8 -*-
"""任务 API"""

from flask import Blueprint, request, jsonify
from services.task_service import TaskService

task_bp = Blueprint("api_tasks", __name__, url_prefix="/api/tasks")


@task_bp.post("/start")
def start_task():
    """POST /api/tasks/start"""
    data = request.get_json()
    result = TaskService().start(
        provider_name=data.get("provider", ""),
        model_key=data.get("model", ""),
        api_key=data.get("api_key", ""),
        prompt_name=data.get("prompt", ""),
        directory=data.get("directory", ""),
        skip_existing=data.get("skip_existing", False),
    )
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@task_bp.get("/status")
def get_status():
    """GET /api/tasks/status"""
    return jsonify(TaskService().get_status())


@task_bp.post("/cancel")
def cancel_task():
    """POST /api/tasks/cancel"""
    result = TaskService().cancel()
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400
