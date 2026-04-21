# -*- coding: utf-8 -*-
import threading
import time

# 文件级别重试配置
FILE_MAX_RETRIES = 2  # 文件级别最大重试次数（AI调用级已有3次重试，文件级2次即可）
RETRY_BASE_DELAY = 2  # 秒，指数退避基数


class ProcessingState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if self._initialized:
                return
            self._state_lock = threading.Lock()
            self._status = "idle"
            self._progress = 0
            self._total_files = 0
            self._processed_files_count = 0
            self._current_file = ""
            self._results = []
            self._error = None
            self._start_time = None
            self._cancelled = False
            self._retrying = False
            self._retry_attempt = 0
            self._retry_max = FILE_MAX_RETRIES
            self._initialized = True

    def get_dict(self) -> dict:
        with self._state_lock:
            return {
                "status": self._status,
                "progress": self._progress,
                "total_files": self._total_files,
                "processed_files_count": self._processed_files_count,
                "current_file": self._current_file,
                "results": list(self._results),
                "error": self._error,
                "start_time": self._start_time,
                "cancelled": self._cancelled,
                "retrying": self._retrying,
                "retry_attempt": self._retry_attempt,
                "retry_max": self._retry_max,
            }

    def start(self, total_files: int = 0):
        with self._state_lock:
            self._status = "scanning"
            self._progress = 0
            self._total_files = total_files
            self._processed_files_count = 0
            self._current_file = ""
            self._results = []
            self._error = None
            self._start_time = time.time()
            self._cancelled = False
            self._retrying = False
            self._retry_attempt = 0

    def start_processing(self, total_files: int):
        with self._state_lock:
            self._status = "processing"
            self._total_files = total_files
            self._current_file = f'准备处理 {total_files} 个文件...'

    def update_progress(self, processed_count: int, current_file: str = None, progress: int = None):
        with self._state_lock:
            self._processed_files_count = processed_count
            if current_file is not None:
                self._current_file = current_file
            if progress is not None:
                self._progress = progress
            elif self._total_files > 0:
                self._progress = int((processed_count / self._total_files) * 100)

    def add_result(self, source: str, output: str = None, error: str = None, retryable: bool = False):
        with self._state_lock:
            self._results.append({
                "source": source,
                "output": output,
                "error": error,
                "retryable": retryable,
            })

    def set_retrying(self, attempt: int):
        with self._state_lock:
            self._retrying = True
            self._retry_attempt = attempt

    def clear_retrying(self):
        with self._state_lock:
            self._retrying = False
            self._retry_attempt = 0

    def complete(self):
        with self._state_lock:
            if self._cancelled:
                self._status = "cancelled"
            else:
                self._status = "completed"
            self._progress = 100
            self._current_file = ""

    def set_error(self, error_message: str):
        with self._state_lock:
            self._status = "error"
            self._error = error_message
            self._current_file = ""

    def cancel(self):
        with self._state_lock:
            self._status = "cancelled"
            self._error = '用户取消了处理'
            self._current_file = ""
            self._cancelled = True

    def set_cancelled(self):
        with self._state_lock:
            self._cancelled = True

    def request_cancel(self) -> bool:
        """原子地请求取消，返回是否成功"""
        with self._state_lock:
            if self._status in ("processing", "scanning"):
                self._cancelled = True
                self._status = "cancelled"
                self._error = '用户取消了处理'
                self._current_file = ""
                return True
            return False

    def is_cancelled(self) -> bool:
        with self._state_lock:
            return self._cancelled

    def is_running(self) -> bool:
        with self._state_lock:
            return self._status in ("processing", "scanning")

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._instance = None
