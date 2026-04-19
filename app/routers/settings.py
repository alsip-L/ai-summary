# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.settings_service import SettingsService
from app.dependencies import get_settings_service
from app.schemas.settings import PreferencesUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/preferences")
def get_preferences(svc: SettingsService = Depends(get_settings_service)):
    return svc.get_preferences()


@router.put("/preferences")
def save_preferences(
    data: PreferencesUpdate,
    svc: SettingsService = Depends(get_settings_service),
):
    result = svc.save_preferences(data.model_dump(exclude_none=True))
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
