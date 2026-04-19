# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.prompt_service import PromptService
from app.dependencies import get_prompt_service
from app.schemas.prompt import PromptCreate

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("/")
def list_prompts(svc: PromptService = Depends(get_prompt_service)):
    return svc.list_all()


@router.post("/")
def create_prompt(
    data: PromptCreate,
    svc: PromptService = Depends(get_prompt_service),
):
    result = svc.create(data.model_dump())
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.delete("/{name}")
def delete_prompt(
    name: str,
    svc: PromptService = Depends(get_prompt_service),
):
    result = svc.delete(name)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
