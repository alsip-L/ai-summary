# -*- coding: utf-8 -*-
import hmac
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.services.settings_service import SettingsService
from app.dependencies import get_settings_service
from app.schemas.settings import PreferencesUpdate, SystemSettingsUpdate
from app.auth import require_auth, generate_api_token
from core.result import check_result
from core.config import ConfigManager

router = APIRouter(prefix="/api/settings", tags=["settings"])


class TokenRequest(BaseModel):
    secret_key: str = Field(min_length=1, description="用于派生 API Token 的密钥")


@router.post(
    "/token",
    summary="获取 API Token",
    description="使用 secret_key 派生 API Token，用于后续需要认证的请求。",
    responses={200: {"description": "API Token"}, 401: {"description": "密钥不匹配"}},
)
def get_token(data: TokenRequest):
    config_key = ConfigManager().get("system_settings.secret_key", "")
    if not config_key or not hmac.compare_digest(data.secret_key, config_key):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="密钥不匹配")
    token = generate_api_token(data.secret_key)
    return {"success": True, "token": token}


@router.get(
    "/preferences",
    summary="获取用户偏好",
    description="返回当前用户的偏好配置，敏感字段（api_key）已脱敏。",
    responses={200: {"description": "用户偏好配置"}},
)
def get_preferences(svc: SettingsService = Depends(get_settings_service)):
    return svc.get_preferences()


@router.get(
    "/preferences/api-key",
    summary="获取完整 API Key",
    description="返回未脱敏的完整 API Key，需要认证。",
    responses={200: {"description": "完整 API Key"}, 401: {"description": "未认证"}},
)
def get_api_key_raw(
    svc: SettingsService = Depends(get_settings_service),
    _auth=Depends(require_auth),
):
    return svc.get_api_key_raw()


@router.patch(
    "/preferences",
    summary="更新用户偏好",
    description="部分更新用户偏好配置，仅传入需要修改的字段，未传入的字段保持不变。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "参数不合法"},
    },
)
def save_preferences(
    data: PreferencesUpdate,
    svc: SettingsService = Depends(get_settings_service),
):
    return check_result(svc.save_preferences(data.model_dump(exclude_none=True)))


def _mask_secret(value: str) -> str:
    """脱敏密钥，仅显示前4后4字符"""
    if not value or len(value) <= 8:
        return "***" if value else ""
    return value[:4] + "******" + value[-4:]


@router.get(
    "/system",
    summary="获取系统设置",
    description="返回系统设置，敏感字段（secret_key、admin_password）已脱敏。",
    responses={200: {"description": "系统设置"}},
)
def get_system_settings():
    settings = ConfigManager().get("system_settings", {})
    return {
        "success": True,
        "settings": {
            "debug_level": settings.get("debug_level", "ERROR"),
            "secret_key": _mask_secret(settings.get("secret_key", "")),
            "host": settings.get("host", "0.0.0.0"),
            "port": settings.get("port", 5000),
            "debug": settings.get("debug", False),
            "admin_username": settings.get("admin_username", "admin"),
            "admin_password": _mask_secret(settings.get("admin_password", "")),
            "allowed_paths": settings.get("allowed_paths", []),
        },
    }


@router.put(
    "/system",
    summary="更新系统设置",
    description="更新系统设置，需要 API Token 认证。修改 host/port/secret_key/debug 后需重启生效。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "参数不合法"},
        401: {"description": "未认证"},
    },
)
def save_system_settings(
    data: SystemSettingsUpdate,
    svc: SettingsService = Depends(get_settings_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.save_system_settings(data.model_dump(exclude_none=True)))
