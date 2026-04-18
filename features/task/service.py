# -*- coding: utf-8 -*-
"""任务处理服务 — 合并状态管理、文件处理和任务编排"""

import os
import threading
import time
from openai import OpenAI
from typing import Dict, Any

from .models import ProcessingStatus, TaskStatus, TaskResult
from features.provider.repository import ProviderRepository
from features.prompt.repository import PromptRepository
from core.config import ConfigManager
from core.errors import FileProcessingError, ProviderError
from core.utils import read_file_with_encoding
from core.log import get_logger

logger = get_logger()


class ProcessingState:
    """线程安全的处理状态管理类（单例模式）

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
            data["status"] = self._state.status.value
            data["results"] = [r.model_dump() for r in self._state.results]
            return data

    def start(self, total_files: int = 0) -> None:
        with self._state_lock:
            self._state = ProcessingStatus(
                status=TaskStatus.SCANNING,
                progress=0,
                total_files=total_files,
                start_time=time.time(),
            )
            logger.info("处理状态已重置为 scanning")

    def start_processing(self, total_files: int) -> None:
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
        with self._state_lock:
            self._state.processed_files_count = processed_count
            if current_file is not None:
                self._state.current_file = current_file
            if progress is not None:
                self._state.progress = progress
            elif self._state.total_files > 0:
                self._state.progress = int((processed_count / self._state.total_files) * 100)

    def add_result(self, source: str, output: str = None, error: str = None) -> None:
        with self._state_lock:
            self._state.results.append(TaskResult(source=source, output=output, error=error))

    def complete(self) -> None:
        with self._state_lock:
            self._state.status = TaskStatus.COMPLETED
            self._state.progress = 100
            self._state.current_file = ''
            self._state.cancelled = False

    def set_error(self, error_message: str) -> None:
        with self._state_lock:
            self._state.status = TaskStatus.ERROR
            self._state.error = error_message
            self._state.current_file = ''

    def cancel(self) -> None:
        with self._state_lock:
            self._state.status = TaskStatus.CANCELLED
            self._state.error = '用户取消了处理'
            self._state.current_file = ''
            self._state.cancelled = True

    def set_cancelled(self) -> None:
        with self._state_lock:
            self._state.cancelled = True

    def is_cancelled(self) -> bool:
        with self._state_lock:
            return self._state.cancelled

    def is_running(self) -> bool:
        with self._state_lock:
            return self._state.status in (TaskStatus.PROCESSING, TaskStatus.SCANNING)


class ProcessingService:
    """AI 文件处理服务"""

    def __init__(self, state: ProcessingState):
        self._state = state

    # ---- 单文件处理 ----

    @staticmethod
    def read_file(file_path: str) -> str:
        return read_file_with_encoding(file_path)

    @staticmethod
    def call_ai(client: OpenAI, content: str, system_prompt: str, model_id: str) -> str:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                stream=False,
            )
            if not completion or not completion.choices:
                raise ProviderError("API 返回空响应")
            return completion.choices[0].message.content
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"AI 调用失败: {str(e).splitlines()[0]}")

    @staticmethod
    def save_response(file_path: str, response: str) -> str:
        md_path = os.path.splitext(file_path)[0] + ".md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(response)
            return md_path
        except Exception as e:
            raise FileProcessingError(f"保存结果失败: {e}")

    def process_file(self, file_path: str, client: OpenAI, prompt: str, model_id: str) -> TaskResult:
        try:
            content = self.read_file(file_path)
            response = self.call_ai(client, content, prompt, model_id)
            output_path = self.save_response(file_path, response)
            return TaskResult(source=file_path, output=output_path)
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return TaskResult(source=file_path, error=str(e))

    # ---- 批量处理 ----

    @staticmethod
    def scan_txt_files(directory: str, skip_existing: bool = False) -> list[str]:
        """扫描目录中的 .txt 文件"""
        if not os.path.isdir(directory):
            raise ValueError(f"目录不存在: {directory}")
        txt_files = []
        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith(".txt"):
                    file_path = os.path.join(root, f)
                    if skip_existing:
                        md_path = os.path.splitext(file_path)[0] + ".md"
                        if os.path.exists(md_path):
                            continue
                    txt_files.append(file_path)
        return txt_files

    def run_batch(
        self,
        directory: str,
        client: OpenAI,
        prompt: str,
        model_id: str,
        skip_existing: bool = False,
    ) -> None:
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            txt_files = self.scan_txt_files(directory, skip_existing)
            if not txt_files:
                raise ValueError("未找到需要处理的 txt 文件")

            self._state.start_processing(len(txt_files))

            for i, file_path in enumerate(txt_files):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                progress_before = int((i / len(txt_files)) * 100)
                self._state.update_progress(i, os.path.basename(file_path), progress_before)
                result = self.process_file(file_path, client, prompt, model_id)
                progress_after = int(((i + 1) / len(txt_files)) * 100)
                self._state.update_progress(i + 1, None, progress_after)
                self._state.add_result(result.source, result.output, result.error)

            self._state.complete()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e).splitlines()[0]}")


class TaskService:
    """任务服务：验证参数、构造客户端、启动后台处理线程"""

    def __init__(self, config: ConfigManager = None):
        self._config = config or ConfigManager()
        self._state = ProcessingState()
        self._processing = ProcessingService(self._state)

    def start(
        self,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
        directory: str,
        skip_existing: bool = False,
    ) -> dict:
        """启动处理任务"""
        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
            return {"success": False, "error": "请提供有效的目录路径"}

        provider_repo = ProviderRepository(self._config)
        prompt_repo = PromptRepository(self._config)

        provider = provider_repo.get(provider_name)
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        if model_key not in provider.models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = provider.models[model_key]

        prompt = prompt_repo.get(prompt_name)
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        client = OpenAI(api_key=api_key, base_url=provider.base_url)
        thread = threading.Thread(
            target=self._processing.run_batch,
            args=(directory, client, prompt.content, model_id, skip_existing),
            daemon=True,
        )
        thread.start()

        return {"success": True, "message": "处理已启动"}

    def get_status(self) -> dict:
        return self._state.get_dict()

    def cancel(self) -> dict:
        if not self._state.is_running() and not self._state.is_cancelled():
            return {"success": False, "error": "当前没有正在进行的处理任务"}
        self._state.set_cancelled()
        if self._state.is_running():
            self._state.cancel()
        return {"success": True, "message": "处理已取消"}
