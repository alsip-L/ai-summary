# -*- coding: utf-8 -*-
"""任务处理状态模型"""

from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class TaskResult(BaseModel):
    """单个文件的处理结果"""
    source: str
    output: str | None = None
    error: str | None = None


class ProcessingStatus(BaseModel):
    """处理状态快照（只读视图）"""
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    total_files: int = 0
    processed_files_count: int = 0
    current_file: str = ""
    results: list[TaskResult] = Field(default_factory=list)
    error: str | None = None
    start_time: float | None = None
    cancelled: bool = False
