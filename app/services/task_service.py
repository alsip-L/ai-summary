# -*- coding: utf-8 -*-
import os
import threading
import time
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models import Provider, Prompt
from app.services.provider_repo import ProviderRepository
from app.services.prompt_repo import PromptRepository
from core.errors import FileProcessingError, ProviderError
from core.utils import read_file_with_encoding
from core.log import get_logger

logger = get_logger()


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
        self._initialized = True

    def get_dict(self) -> dict:
        with self._state_lock:
            return {
                "status": self._status,
                "progress": self._progress,
                "total_files": self._total_files,
                "processed_files_count": self._processed_files_count,
                "current_file": self._current_file,
                "results": self._results,
                "error": self._error,
                "start_time": self._start_time,
                "cancelled": self._cancelled,
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

    def add_result(self, source: str, output: str = None, error: str = None):
        with self._state_lock:
            self._results.append({"source": source, "output": output, "error": error})

    def complete(self):
        with self._state_lock:
            self._status = "completed"
            self._progress = 100
            self._current_file = ""
            self._cancelled = False

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


class TaskService:
    def __init__(self, db: Session):
        self._db = db
        self._state = ProcessingState()

    def start(
        self,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
        directory: str,
        skip_existing: bool = False,
    ) -> dict:
        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
            return {"success": False, "error": "请提供有效的目录路径"}

        import json as json_mod
        provider = self._db.query(Provider).filter(Provider.name == provider_name, Provider.is_active == True).first()
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        models = json_mod.loads(provider.models_json)
        if model_key not in models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = models[model_key]

        prompt = self._db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        client = OpenAI(api_key=api_key, base_url=provider.base_url)
        thread = threading.Thread(
            target=self._run_batch,
            args=(directory, client, prompt.content, model_id, skip_existing),
            daemon=True,
        )
        thread.start()
        return {"success": True, "message": "处理已启动"}

    def _run_batch(self, directory, client, prompt_content, model_id, skip_existing):
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            txt_files = self._scan_txt_files(directory, skip_existing)
            if not txt_files:
                raise ValueError("未找到需要处理的 txt 文件")

            self._state.start_processing(len(txt_files))

            for i, file_path in enumerate(txt_files):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                progress_before = int((i / len(txt_files)) * 100)
                self._state.update_progress(i, os.path.basename(file_path), progress_before)
                result = self._process_file(file_path, client, prompt_content, model_id)
                progress_after = int(((i + 1) / len(txt_files)) * 100)
                self._state.update_progress(i + 1, None, progress_after)
                self._state.add_result(result["source"], result.get("output"), result.get("error"))

            self._state.complete()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e).splitlines()[0]}")

    @staticmethod
    def _scan_txt_files(directory: str, skip_existing: bool = False) -> list[str]:
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

    @staticmethod
    def _process_file(file_path, client, prompt_content, model_id):
        try:
            content = read_file_with_encoding(file_path)
            response = TaskService._call_ai(client, content, prompt_content, model_id)
            output_path = TaskService._save_response(file_path, response)
            return {"source": file_path, "output": output_path}
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return {"source": file_path, "error": str(e)}

    @staticmethod
    def _call_ai(client, content, system_prompt, model_id):
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
    def _save_response(file_path, response):
        md_path = os.path.splitext(file_path)[0] + ".md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(response)
            return md_path
        except Exception as e:
            raise FileProcessingError(f"保存结果失败: {e}")

    def get_status(self) -> dict:
        return self._state.get_dict()

    def cancel(self) -> dict:
        if not self._state.is_running() and not self._state.is_cancelled():
            return {"success": False, "error": "当前没有正在进行的处理任务"}
        self._state.set_cancelled()
        if self._state.is_running():
            self._state.cancel()
        return {"success": True, "message": "处理已取消"}
