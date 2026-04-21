# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.settings_service import SettingsService
from app.dependencies import get_settings_service
from app.schemas.settings import PreferencesUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get(
    "/preferences",
    summary="获取用户偏好",
    description="返回当前用户的偏好配置，包含选中的提供商、模型、提示词和目录路径。",
    responses={200: {"description": "用户偏好配置"}},
)
def get_preferences(svc: SettingsService = Depends(get_settings_service)):
    return svc.get_preferences()


@router.put(
    "/preferences",
    summary="更新用户偏好",
    description="更新用户偏好配置，仅传入需要修改的字段。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "参数不合法"},
    },
)
def save_preferences(
    data: PreferencesUpdate,
    svc: SettingsService = Depends(get_settings_service),
):
    result = svc.save_preferences(data.model_dump(exclude_none=True))
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
