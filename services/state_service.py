# -*- coding: utf-8 -*-
"""处理状态服务模块

使用 models.task 中的 Pydantic ProcessingStatus 和 TaskStatus 枚举，
确保状态值类型安全，消除硬编码字符串。
"""

import copy
import threading
import time
from typing import Dict, List, Any, Optional
from models.task import ProcessingStatus, TaskStatus, TaskResult
from core.log import get_logger

logger = get_logger()


class ProcessingState:
    """线程安全的处理状态管理类

    提供原子性的状态更新操作，支持多线程环境下的并发访问。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._state_lock = threading.Lock()
        self._state = ProcessingStatus()
        self._initialized = True

    def get_dict(self) -> Dict[str, Any]:
        """获取当前状态的字典形式（深拷贝，线程安全）"""
        with self._state_lock:
            data = self._state.model_dump()
            # 将 TaskStatus 枚举转为字符串，results 中 TaskResult 也转为 dict
            data["status"] = self._state.status.value
            data["results"] = [r.model_dump() for r in self._state.results]
            return data

    def reset(self) -> None:
        """重置状态为初始值"""
        with self._state_lock:
            self._state = ProcessingStatus()

    def start(self, total_files: int = 0) -> None:
        """开始处理"""
        with self._state_lock:
            self._state = ProcessingStatus(
                status=TaskStatus.SCANNING,
                progress=0,
                total_files=total_files,
                start_time=time.time(),
            )
            logger.info("处理状态已重置为 scanning")

    def start_processing(self, total_files: int) -> None:
        """开始实际处理"""
        with self._state_lock:
            self._state.status = TaskStatus.PROCESSING
            self._state.total_files = total_files
            self._state.current_file = f'准备处理 {total_files} 个文件...'

    def update_progress(
        self,
        processed_count: int,
        current_file: str = None,
        progress: int = None
    ) -> None:
        """更新处理进度"""
        with self._state_lock:
            self._state.processed_files_count = processed_count
            if current_file is not None:
                self._state.current_file = current_file
            if progress is not None:
                self._state.progress = progress
            elif self._state.total_files > 0:
                self._state.progress = int((processed_count / self._state.total_files) * 100)

    def add_result(self, source: str, output: str = None, error: str = None) -> None:
        """添加处理结果"""
        with self._state_lock:
            self._state.results.append(TaskResult(source=source, output=output, error=error))

    def complete(self) -> None:
        """标记处理完成"""
        with self._state_lock:
            self._state.status = TaskStatus.COMPLETED
            self._state.progress = 100
            self._state.current_file = ''
            self._state.end_time = time.time()
            self._state.cancelled = False

    def set_error(self, error_message: str) -> None:
        """设置错误状态"""
        with self._state_lock:
            self._state.status = TaskStatus.ERROR
            self._state.error = error_message
            self._state.current_file = ''
            self._state.end_time = time.time()

    def cancel(self) -> None:
        """取消处理"""
        with self._state_lock:
            self._state.status = TaskStatus.CANCELLED
            self._state.error = '用户取消了处理'
            self._state.current_file = ''
            self._state.end_time = time.time()
            self._state.cancelled = True

    def set_cancelled(self) -> None:
        """设置取消标志"""
        with self._state_lock:
            self._state.cancelled = True

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        with self._state_lock:
            return self._state.cancelled

    def is_running(self) -> bool:
        """检查是否正在处理"""
        with self._state_lock:
            return self._state.status in (TaskStatus.PROCESSING, TaskStatus.SCANNING)

    def get_elapsed_time(self) -> float:
        """获取已消耗的时间（秒）"""
        with self._state_lock:
            if self._state.start_time is None:
                return 0
            end = self._state.end_time or time.time()
            return end - self._state.start_time
