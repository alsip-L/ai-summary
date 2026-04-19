# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.provider_service import ProviderService
from app.dependencies import get_provider_service
from app.schemas.provider import ProviderCreate, ApiKeyUpdate, ModelCreate

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/")
def list_providers(svc: ProviderService = Depends(get_provider_service)):
    return svc.list_all()


@router.post("/")
def create_provider(
    data: ProviderCreate,
    svc: ProviderService = Depends(get_provider_service),
):
    result = svc.create(data.model_dump())
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/{name}")
def delete_provider(
    name: str,
    svc: ProviderService = Depends(get_provider_service),
):
    result = svc.delete(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.put("/{name}/api-key")
def update_api_key(
    name: str,
    data: ApiKeyUpdate,
    svc: ProviderService = Depends(get_provider_service),
):
    result = svc.update_api_key(name, data.api_key)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.post("/{name}/models")
def add_model(
    name: str,
    data: ModelCreate,
    svc: ProviderService = Depends(get_provider_service),
):
    result = svc.add_model(name, data.display_name, data.model_id)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/{name}/models/{model_name}")
def delete_model(
    name: str,
    model_name: str,
    svc: ProviderService = Depends(get_provider_service),
):
    result = svc.delete_model(name, model_name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
