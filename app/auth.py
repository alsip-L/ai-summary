# -*- coding: utf-8 -*-
"""API Token 认证模块

提供基于 secret_key 派生的 API Token 认证机制，
用于保护敏感 API 端点（如获取完整 API Key、系统重建等）。
"""

import hmac
import hashlib
from fastapi import Request, HTTPException
from core.config import ConfigManager


def generate_api_token(secret_key: str) -> str:
    """从 secret_key 派生 API Token（HMAC-SHA256）"""
    return hmac.new(
        secret_key.encode("utf-8"),
        b"ai-summary-api-token",
        hashlib.sha256,
    ).hexdigest()


async def require_auth(request: Request):
    """FastAPI 依赖：验证 X-API-Token header

    敏感端点使用 Depends(require_auth) 保护。
    Token 由 secret_key 通过 HMAC-SHA256 派生。
    """
    token = request.headers.get("X-API-Token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing API token")

    secret_key = ConfigManager().get("system_settings.secret_key", "")
    if not secret_key:
        raise HTTPException(status_code=401, detail="Server secret key not configured")

    expected = generate_api_token(secret_key)
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid API token")
