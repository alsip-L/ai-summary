# -*- coding: utf-8 -*-
"""OpenAPI 规范增强配置"""

OPENAPI_TAGS = [
    {
        "name": "providers",
        "description": "AI 提供商管理 - 添加/编辑/删除 AI 服务提供商，支持多模型配置",
    },
    {
        "name": "prompts",
        "description": "提示词管理 - 创建和管理 AI 处理模板，作为 system prompt 发送",
    },
    {
        "name": "tasks",
        "description": "任务处理 - 批量文件处理任务启动、状态查询、取消和失败重试",
    },
    {
        "name": "files",
        "description": "文件浏览 - 目录浏览、驱动器列表和处理结果查看",
    },
    {
        "name": "trash",
        "description": "回收站 - 软删除的提供商和提示词的恢复与永久删除",
    },
    {
        "name": "settings",
        "description": "设置 - 用户偏好配置的读取和更新",
    },
    {
        "name": "logs",
        "description": "日志 - 实时日志推送（WebSocket）和日志状态查询",
    },
    {
        "name": "system",
        "description": "系统 - 系统信息查询和前端重建",
    },
]


def custom_openapi(app, original_openapi):
    """为 FastAPI 应用生成增强的 OpenAPI 规范"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = original_openapi()

    # 注入 tags 描述
    openapi_schema["tags"] = OPENAPI_TAGS

    # 为每个端点确保有通用错误响应描述
    for path_key, path_item in openapi_schema.get("paths", {}).items():
        for method_key, method_item in path_item.items():
            if method_key in ("get", "post", "put", "delete", "patch"):
                responses = method_item.setdefault("responses", {})
                if "400" not in responses:
                    responses["400"] = {
                        "description": "请求参数错误",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    }
                if "500" not in responses:
                    responses["500"] = {
                        "description": "服务器内部错误",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
