# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.task_service import TaskService
from app.services.failed_record_service import FailedRecordService
from app.dependencies import get_task_service, get_db
from app.schemas.task import TaskStartRequest, RetryFailedRequest
from app.auth import require_auth
from core.result import check_result

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post(
    "/start",
    summary="启动处理任务",
    description="启动批量文件处理任务。需指定提供商、模型、API Key、提示词和目标目录。任务在后台线程中执行。",
    responses={
        200: {"description": "任务启动成功"},
        400: {"description": "参数不合法或已有任务在运行"},
    },
)
def start_task(
    data: TaskStartRequest,
    db: Session = Depends(get_db),
    svc: TaskService = Depends(get_task_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.start(
        db=db,
        provider_name=data.provider,
        model_key=data.model,
        api_key=data.api_key,
        prompt_name=data.prompt,
        directory=data.directory,
        skip_existing=data.skip_existing,
    ))


@router.get(
    "/status",
    summary="获取处理状态",
    description="返回当前任务的处理状态、进度、已处理文件数和结果列表。",
    responses={200: {"description": "任务状态信息"}},
)
def get_status(svc: TaskService = Depends(get_task_service)):
    return svc.get_status()


@router.post(
    "/cancel",
    summary="取消处理任务",
    description="请求取消当前正在运行的处理任务。",
    responses={
        200: {"description": "取消成功"},
        400: {"description": "无任务运行或取消失败"},
    },
)
def cancel_task(svc: TaskService = Depends(get_task_service), _auth=Depends(require_auth)):
    return check_result(svc.cancel())


@router.get(
    "/failed",
    summary="获取失败记录",
    description="返回所有处理失败的文件记录，包含错误信息和是否可重试标记。",
    responses={200: {"description": "失败记录列表"}},
)
def get_failed_records(_auth=Depends(require_auth)):
    return check_result(FailedRecordService.get_failed_records(), status_code=500)


@router.delete(
    "/failed",
    summary="清除失败记录",
    description="手动清除所有失败记录。",
    responses={200: {"description": "清除成功"}},
)
def clear_failed_records(_auth=Depends(require_auth)):
    return check_result(FailedRecordService.clear_failed_records(), status_code=500)


@router.post(
    "/retry-failed",
    summary="重试失败记录",
    description="重新处理之前失败的文件，需重新指定提供商、模型、API Key 和提示词。",
    responses={
        200: {"description": "重试启动成功"},
        400: {"description": "参数不合法或无失败记录"},
    },
)
def retry_failed(
    data: RetryFailedRequest,
    db: Session = Depends(get_db),
    svc: TaskService = Depends(get_task_service),
    _auth=Depends(require_auth),
):
    return check_result(svc.retry_failed(
        db=db,
        provider_name=data.provider,
        model_key=data.model,
        api_key=data.api_key,
        prompt_name=data.prompt,
    ))
