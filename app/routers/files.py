# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.file_browser_service import FileBrowserService
from app.dependencies import get_file_browser_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/drives")
def get_drives(svc: FileBrowserService = Depends(get_file_browser_service)):
    result = svc.get_drives()
    if result.get("success"):
        return result
    raise HTTPException(status_code=500, detail=result.get("error"))


@router.get("/directory")
def get_directory(
    path: str = Query(""),
    svc: FileBrowserService = Depends(get_file_browser_service),
):
    result = svc.get_directory(path)
    if result.get("success"):
        return result
    raise HTTPException(status_code=400, detail=result.get("error"))


@router.get("/result")
def view_result(
    path: str = Query(""),
    svc: FileBrowserService = Depends(get_file_browser_service),
):
    result = svc.view_result(path)
    if result.get("success"):
        return result
    if "不存在" in result.get("error", ""):
        raise HTTPException(status_code=404, detail=result.get("error"))
    raise HTTPException(status_code=400, detail=result.get("error"))
