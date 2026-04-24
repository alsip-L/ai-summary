# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from app.services.provider_service import ProviderService
from app.dependencies import get_provider_service
from app.schemas.provider import ProviderCreate, ApiKeyUpdate, ModelCreate
from app.auth import require_auth
from core.result import check_result

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get(
    "/",
    summary="列出所有活跃提供商",
    description="返回所有未被软删除的 AI 提供商列表，包含名称、Base URL、模型列表和激活状态。",
    responses={200: {"description": "提供商列表"}},
)
def list_providers(svc: ProviderService = Depends(get_provider_service)):
    return svc.list_all()


@router.post(
    "/",
    summary="创建提供商",
    description="创建新的 AI 提供商。名称不可重复，base_url 须以 http:// 或 https:// 开头。",
    responses={
        200: {"description": "创建成功"},
        400: {"description": "名称重复或参数不合法"},
    },
)
def create_provider(
    data: ProviderCreate,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.create(data.model_dump()))


@router.delete(
    "/{name}",
    summary="删除提供商",
    description="将指定提供商移入回收站（软删除），不永久删除数据。",
    responses={
        200: {"description": "删除成功"},
        400: {"description": "提供商不存在"},
    },
)
def delete_provider(
    name: str,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.delete(name))


@router.get(
    "/{name}/api-key",
    summary="获取完整 API Key",
    description="获取指定提供商的完整 API Key，供复制使用。",
    responses={
        200: {"description": "API Key"},
        400: {"description": "提供商不存在"},
    },
)
def get_api_key(
    name: str,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.get_api_key(name))


@router.put(
    "/{name}/api-key",
    summary="更新 API Key",
    description="更新指定提供商的 API Key，用于认证 AI 服务调用。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "提供商不存在"},
    },
)
def update_api_key(
    name: str,
    data: ApiKeyUpdate,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.update_api_key(name, data.api_key))


@router.post(
    "/{name}/models",
    summary="添加模型",
    description="为指定提供商添加一个 AI 模型，display_name 为前端展示名，model_id 为 API 调用标识。",
    responses={
        200: {"description": "添加成功"},
        400: {"description": "提供商不存在或模型名重复"},
    },
)
def add_model(
    name: str,
    data: ModelCreate,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.add_model(name, data.display_name, data.model_id))


@router.delete(
    "/{name}/models/{model_name}",
    summary="删除模型",
    description="从指定提供商中移除一个 AI 模型。",
    responses={
        200: {"description": "删除成功"},
        400: {"description": "提供商或模型不存在"},
    },
)
def delete_model(
    name: str,
    model_name: str,
    svc: ProviderService = Depends(get_provider_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.delete_model(name, model_name))
