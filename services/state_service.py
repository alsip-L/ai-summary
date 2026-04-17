# -*- coding: utf-8 -*-
"""处理状态服务模块"""

import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from core.log import get_logger

logger = get_logger()


@dataclass
class ProcessingStatus:
    """处理状态数据类"""
    status: str = 'idle'
    progress: int = 0
    total_files: int = 0
    processed_files_count: int = 0
    current_file: str = ''
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    cancelled: bool = False


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
        self._history: List[ProcessingStatus] = []
        self._max_history = 10
        self._initialized = True

    def get(self) -> ProcessingStatus:
        """获取当前状态的副本

        Returns:
            ProcessingStatus对象的副本
        """
        with self._state_lock:
            return ProcessingStatus(
                status=self._state.status,
                progress=self._state.progress,
                total_files=self._state.total_files,
                processed_files_count=self._state.processed_files_count,
                current_file=self._state.current_file,
                results=self._state.results.copy(),
                error=self._state.error,
                start_time=self._state.start_time,
                end_time=self._state.end_time,
                cancelled=self._state.cancelled
            )

    def get_dict(self) -> Dict[str, Any]:
        """获取当前状态的字典形式

        Returns:
            状态字典
        """
        with self._state_lock:
            return {
                'status': self._state.status,
                'progress': self._state.progress,
                'total_files': self._state.total_files,
                'processed_files_count': self._state.processed_files_count,
                'current_file': self._state.current_file,
                'results': self._state.results.copy(),
                'error': self._state.error,
                'start_time': self._state.start_time,
                'end_time': self._state.end_time,
                'cancelled': self._state.cancelled
            }

    def update(self, **kwargs) -> None:
        """更新状态字段

        Args:
            **kwargs: 要更新的字段
        """
        with self._state_lock:
            self._save_history()
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)

    def reset(self) -> None:
        """重置状态为初始值"""
        with self._state_lock:
            self._save_history()
            self._state = ProcessingStatus()

    def start(self, total_files: int = 0) -> None:
        """开始处理

        Args:
            total_files: 总文件数
        """
        with self._state_lock:
            self._save_history()
            self._state = ProcessingStatus(
                status='scanning',
                progress=0,
                total_files=total_files,
                processed_files_count=0,
                current_file='',
                results=[],
                error=None,
                start_time=time.time(),
                end_time=None,
                cancelled=False
            )
            logger.info("处理状态已重置为 scanning")

    def start_processing(self, total_files: int) -> None:
        """开始实际处理

        Args:
            total_files: 总文件数
        """
        with self._state_lock:
            self._save_history()
            self._state.status = 'processing'
            self._state.total_files = total_files
            self._state.current_file = f'准备处理 {total_files} 个文件...'

    def update_progress(
        self,
        processed_count: int,
        current_file: str = None,
        progress: int = None
    ) -> None:
        """更新处理进度

        Args:
            processed_count: 已处理文件数
            current_file: 当前处理的文件名
            progress: 进度百分比（可选）
        """
        with self._state_lock:
            self._state.processed_files_count = processed_count
            if current_file is not None:
                self._state.current_file = current_file
            if progress is not None:
                self._state.progress = progress
            elif self._state.total_files > 0:
                self._state.progress = int((processed_count / self._state.total_files) * 100)

    def add_result(self, source: str, output: str = None, error: str = None) -> None:
        """添加处理结果

        Args:
            source: 源文件路径
            output: 输出文件路径
            error: 错误信息
        """
        with self._state_lock:
            self._state.results.append({
                'source': source,
                'output': output,
                'error': error
            })

    def complete(self) -> None:
        """标记处理完成"""
        with self._state_lock:
            self._save_history()
            self._state.status = 'completed'
            self._state.progress = 100
            self._state.current_file = ''
            self._state.end_time = time.time()
            self._state.cancelled = False

    def set_error(self, error_message: str) -> None:
        """设置错误状态

        Args:
            error_message: 错误信息
        """
        with self._state_lock:
            self._save_history()
            self._state.status = 'error'
            self._state.error = error_message
            self._state.current_file = ''
            self._state.end_time = time.time()

    def cancel(self) -> None:
        """取消处理"""
        with self._state_lock:
            self._save_history()
            self._state.status = 'cancelled'
            self._state.error = '用户取消了处理'
            self._state.current_file = ''
            self._state.end_time = time.time()
            self._state.cancelled = True

    def set_cancelled(self) -> None:
        """设置取消标志"""
        with self._state_lock:
            self._state.cancelled = True

    def is_cancelled(self) -> bool:
        """检查是否已取消

        Returns:
            是否已取消
        """
        with self._state_lock:
            return self._state.cancelled

    def is_running(self) -> bool:
        """检查是否正在处理

        Returns:
            是否正在处理
        """
        with self._state_lock:
            return self._state.status in ['processing', 'scanning', 'started']

    def get_elapsed_time(self) -> float:
        """获取已消耗的时间

        Returns:
            时间（秒）
        """
        with self._state_lock:
            if self._state.start_time is None:
                return 0
            end = self._state.end_time or time.time()
            return end - self._state.start_time

    def _save_history(self) -> None:
        """保存历史状态"""
        self._history.append(ProcessingStatus(
            status=self._state.status,
            progress=self._state.progress,
            total_files=self._state.total_files,
            processed_files_count=self._state.processed_files_count,
            current_file=self._state.current_file,
            results=self._state.results.copy(),
            error=self._state.error,
            start_time=self._state.start_time,
            end_time=self._state.end_time,
            cancelled=self._state.cancelled
        ))
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def get_history(self) -> List[ProcessingStatus]:
        """获取状态历史

        Returns:
            状态历史列表
        """
        with self._state_lock:
            return self._history.copy()
