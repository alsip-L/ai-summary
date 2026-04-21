# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from app.services.task_service import TaskService
from app.services.failed_record_service import FailedRecordService
from app.dependencies import get_task_service
from app.schemas.task import TaskStartRequest, RetryFailedRequest

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/start")
def start_task(
    data: TaskStartRequest,
    svc: TaskService = Depends(get_task_service),
):
    result = svc.start(
        provider_name=data.provider,
        model_key=data.model,
        api_key=data.api_key,
        prompt_name=data.prompt,
        directory=data.directory,
        skip_existing=data.skip_existing,
    )
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.get("/status")
def get_status(svc: TaskService = Depends(get_task_service)):
    return svc.get_status()


@router.post("/cancel")
def cancel_task(svc: TaskService = Depends(get_task_service)):
    result = svc.cancel()
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@router.get("/failed")
def get_failed_records():
    result = FailedRecordService.get_failed_records()
    if result["success"]:
        return result
    raise HTTPException(status_code=500, detail=result["error"])


@router.delete("/failed")
def clear_failed_records():
    result = FailedRecordService.clear_failed_records()
    if result["success"]:
        return result
    raise HTTPException(status_code=500, detail=result["error"])


@router.post("/retry-failed")
def retry_failed(
    data: RetryFailedRequest,
    svc: TaskService = Depends(get_task_service),
):
    result = svc.retry_failed(
        provider_name=data.provider,
        model_key=data.model,
        api_key=data.api_key,
        prompt_name=data.prompt,
    )
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])
