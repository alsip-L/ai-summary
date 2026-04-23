# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from app.services.trash_service import TrashService
from app.dependencies import get_trash_service
from app.auth import require_auth
from core.result import check_result

router = APIRouter(prefix="/api/settings/trash", tags=["trash"])


@router.get(
    "/",
    summary="获取回收站内容",
    description="返回回收站中所有已软删除的提供商和提示词列表。",
    responses={200: {"description": "回收站内容"}},
)
def get_trash(svc: TrashService = Depends(get_trash_service)):
    return svc.get_all()


@router.post(
    "/restore/provider/{name}",
    summary="恢复提供商",
    description="从回收站恢复指定提供商，使其重新变为活跃状态。需要 API Token 认证。",
    responses={
        200: {"description": "恢复成功"},
        400: {"description": "提供商不存在或名称冲突"},
        401: {"description": "未认证"},
    },
)
def restore_provider(
    name: str,
    svc: TrashService = Depends(get_trash_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.restore_provider(name))


@router.post(
    "/restore/prompt/{name}",
    summary="恢复提示词",
    description="从回收站恢复指定提示词，使其重新变为活跃状态。需要 API Token 认证。",
    responses={
        200: {"description": "恢复成功"},
        400: {"description": "提示词不存在或名称冲突"},
        401: {"description": "未认证"},
    },
)
def restore_prompt(
    name: str,
    svc: TrashService = Depends(get_trash_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.restore_prompt(name))


@router.delete(
    "/provider/{name}",
    summary="永久删除提供商",
    description="永久删除指定提供商，不可恢复。需要 API Token 认证。",
    responses={
        200: {"description": "删除成功"},
        400: {"description": "提供商不存在"},
        401: {"description": "未认证"},
    },
)
def permanent_delete_provider(
    name: str,
    svc: TrashService = Depends(get_trash_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.permanent_delete_provider(name))


@router.delete(
    "/prompt/{name}",
    summary="永久删除提示词",
    description="永久删除指定提示词，不可恢复。需要 API Token 认证。",
    responses={
        200: {"description": "删除成功"},
        400: {"description": "提示词不存在"},
        401: {"description": "未认证"},
    },
)
def permanent_delete_prompt(
    name: str,
    svc: TrashService = Depends(get_trash_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.permanent_delete_prompt(name))
