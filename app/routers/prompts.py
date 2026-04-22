# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from app.services.prompt_service import PromptService
from app.dependencies import get_prompt_service
from app.schemas.prompt import PromptCreate
from core.result import check_result

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get(
    "/",
    summary="列出所有提示词",
    description="返回所有提示词列表，包含名称和内容。",
    responses={200: {"description": "提示词列表"}},
)
def list_prompts(svc: PromptService = Depends(get_prompt_service)):
    return svc.list_all()


@router.post(
    "/",
    summary="创建提示词",
    description="创建新的提示词模板，作为 AI 处理时的 system prompt 发送。",
    responses={
        200: {"description": "创建成功"},
        400: {"description": "名称重复或参数不合法"},
    },
)
def create_prompt(
    data: PromptCreate,
    svc: PromptService = Depends(get_prompt_service),
):
    return check_result(svc.create(data.model_dump()))


@router.delete(
    "/{name}",
    summary="删除提示词",
    description="将指定提示词移入回收站（软删除）。",
    responses={
        200: {"description": "删除成功"},
        400: {"description": "提示词不存在"},
    },
)
def delete_prompt(
    name: str,
    svc: PromptService = Depends(get_prompt_service),
):
    return check_result(svc.delete(name))
