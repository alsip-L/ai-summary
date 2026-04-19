# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.trash_service import TrashService
from app.dependencies import get_trash_service

router = APIRouter(prefix="/api/settings/trash", tags=["trash"])


@router.get("/")
def get_trash(svc: TrashService = Depends(get_trash_service)):
    return svc.get_all()


@router.post("/restore/provider/{name}")
def restore_provider(
    name: str,
    svc: TrashService = Depends(get_trash_service),
):
    result = svc.restore_provider(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.post("/restore/prompt/{name}")
def restore_prompt(
    name: str,
    svc: TrashService = Depends(get_trash_service),
):
    result = svc.restore_prompt(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/provider/{name}")
def permanent_delete_provider(
    name: str,
    svc: TrashService = Depends(get_trash_service),
):
    result = svc.permanent_delete_provider(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/prompt/{name}")
def permanent_delete_prompt(
    name: str,
    svc: TrashService = Depends(get_trash_service),
):
    result = svc.permanent_delete_prompt(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
