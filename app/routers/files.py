# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Query
from app.services.file_browser_service import FileBrowserService
from app.dependencies import get_file_browser_service
from core.result import check_result

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get(
    "/drives",
    summary="获取可用驱动器",
    description="返回系统上所有可用的磁盘驱动器列表，用于目录浏览的起始点。",
    responses={200: {"description": "驱动器列表"}},
)
def get_drives(svc: FileBrowserService = Depends(get_file_browser_service)):
    return check_result(svc.get_drives(), status_code=500)


@router.get(
    "/directory",
    summary="获取目录内容",
    description="返回指定路径下的子目录和文件列表，用于浏览文件系统。",
    responses={
        200: {"description": "目录内容列表"},
        400: {"description": "路径不合法"},
    },
)
def get_directory(
    path: str = Query(""),
    svc: FileBrowserService = Depends(get_file_browser_service),
):
    return check_result(svc.get_directory(path))


@router.get(
    "/result",
    summary="查看处理结果",
    description="查看指定路径文件的处理结果内容。",
    responses={
        200: {"description": "处理结果内容"},
        404: {"description": "结果文件不存在"},
        400: {"description": "路径不合法"},
    },
)
def view_result(
    path: str = Query(""),
    svc: FileBrowserService = Depends(get_file_browser_service),
):
    result = svc.view_result(path)
    if not result.get("success"):
        error = result.get("error", "")
        if "不存在" in error or "not found" in error.lower():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=error)
        if "不支持" in error or "不在允许" in error:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=error)
    return check_result(result)
