# -*- coding: utf-8 -*-
import os
import threading
import time
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models import Provider, Prompt
from app.services.provider_repo import ProviderRepository, _safe_json_loads
from app.services.prompt_repo import PromptRepository
from app.services.failed_record_repo import FailedRecordRepository
from app.database import SessionLocal
from core.errors import (
    FileProcessingError, ProviderError, RetryableError,
    NetworkError, RateLimitError,
)
from core.utils import read_file_with_encoding
from core.log import get_logger, get_ws_handler

logger = get_logger()

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 秒，指数退避基数


def _classify_openai_error(e: Exception) -> Exception:
    """将 OpenAI SDK 异常分类为项目自定义异常

    策略：AI 调用相关的异常默认可重试（网络抖动、限流、服务端临时错误等），
    仅明确的客户端逻辑错误（如 API Key 无效、模型不存在）不可重试。
    """
    error_name = type(e).__name__
    module = type(e).__module__ or ""
    error_str = str(e)

    # OpenAI SDK 的限流错误
    if "RateLimitError" in error_name or "rate_limit" in error_str.lower() or "429" in error_str:
        return RateLimitError(f"API 限流", cause=e)

    # OpenAI SDK 的网络/连接错误
    if "APIConnectionError" in error_name or "ConnectionError" in error_name:
        return NetworkError(f"网络连接失败", cause=e)

    # OpenAI SDK 的超时错误
    if "APITimeoutError" in error_name or "Timeout" in error_name:
        return NetworkError(f"请求超时", cause=e)

    # OpenAI SDK 的服务端错误 (5xx)
    if "APIStatusError" in error_name or "InternalServerError" in error_name:
        if "5" in error_str[:20]:
            return RetryableError(f"服务端临时错误", cause=e)

    # 明确不可重试的客户端错误：认证失败、模型不存在
    non_retryable_keywords = ["invalid_api_key", "authentication", "model_not_found", "invalid x-api-key"]
    if any(kw in error_str.lower() for kw in non_retryable_keywords):
        return ProviderError(f"AI 调用失败: {error_str}", cause=e)

    # 其他 OpenAI/API 相关异常默认可重试（包括 400 invalid_parameter 等）
    if "openai" in module.lower() or "APIStatusError" in error_name or "APIError" in error_name:
        return RetryableError(f"API 临时错误", cause=e)

    # 非OpenAI异常，视为不可重试
    return ProviderError(f"AI 调用失败: {error_str}", cause=e)


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
            self._retry_max = MAX_RETRIES
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
        if self._state.is_running():
            return {"success": False, "error": "已有任务正在运行"}

        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
            return {"success": False, "error": "请提供有效的目录路径"}

        provider = self._db.query(Provider).filter(Provider.name == provider_name, Provider.is_active == True).first()
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        models = _safe_json_loads(provider.models_json)
        if model_key not in models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = models[model_key]

        prompt = self._db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        client = OpenAI(api_key=api_key, base_url=provider.base_url)
        logger.info(f"启动处理任务: provider={provider_name}, model={model_id}, directory={directory}")
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

            logger.info(f"开始扫描目录: {directory}")
            txt_files = self._scan_txt_files(directory, skip_existing)
            if not txt_files:
                raise ValueError("未找到需要处理的 txt 文件")

            logger.info(f"扫描完成: 找到 {len(txt_files)} 个 txt 文件")
            self._state.start_processing(len(txt_files))

            for i, file_path in enumerate(txt_files):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                progress_before = int((i / len(txt_files)) * 100)
                self._state.update_progress(i, os.path.basename(file_path), progress_before)
                logger.info(f"处理文件 [{i+1}/{len(txt_files)}]: {os.path.basename(file_path)}")
                result = self._process_file(file_path, client, prompt_content, model_id)
                progress_after = int(((i + 1) / len(txt_files)) * 100)
                self._state.update_progress(i + 1, None, progress_after)
                self._state.add_result(
                    result["source"],
                    result.get("output"),
                    result.get("error"),
                    result.get("retryable", False),
                )

            self._state.complete()
            # 统计成功/失败数
            with self._state._state_lock:
                results = list(self._state._results)
            success_count = sum(1 for r in results if not r.get("error"))
            fail_count = sum(1 for r in results if r.get("error"))
            logger.info(f"处理完成: 共处理 {len(txt_files)} 个文件, 成功 {success_count} 个, 失败 {fail_count} 个")
            self._persist_failed_records()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e)}")
            self._persist_failed_records()

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
            logger.info(f"读取文件完成: {os.path.basename(file_path)}, 字符数: {len(content)}")
            response = TaskService._call_ai(client, content, prompt_content, model_id)
            output_path = TaskService._save_response(file_path, response)
            logger.info(f"文件处理成功: {os.path.basename(file_path)} -> {os.path.basename(output_path)}")
            return {"source": file_path, "output": output_path}
        except RetryableError as e:
            logger.error(f"文件处理失败（可重试）: {os.path.basename(file_path)} - {e}")
            return {"source": file_path, "error": str(e), "retryable": True}
        except Exception as e:
            logger.error(f"文件处理失败: {os.path.basename(file_path)} - {e}")
            return {"source": file_path, "error": str(e), "retryable": False}

    @staticmethod
    def _call_ai(client, content, system_prompt, model_id):
        """调用 AI API，带指数退避重试（仅对可重试异常）"""
        state = ProcessingState()
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            ws_handler = get_ws_handler()
            try:
                if attempt > 1:
                    state.set_retrying(attempt)
                    logger.info(f"第 {attempt} 次重试调用 AI 模型: {model_id}...")
                else:
                    logger.info(f"调用 AI 模型: {model_id}...")
                stream = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    stream=True,
                )
                full_response = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_response.append(token)
                        if ws_handler:
                            ws_handler.put_stream(token)
                response = "".join(full_response)
                if ws_handler:
                    ws_handler.put_stream_end()
                if not response:
                    raise ProviderError("API 返回空响应")
                logger.info(f"AI 响应完成, 字符数: {len(response)}")
                if attempt > 1:
                    logger.info(f"第 {attempt} 次重试成功")
                state.clear_retrying()
                return response
            except (ProviderError, FileProcessingError):
                # 确保流式输出结束标记已发送
                if ws_handler:
                    ws_handler.put_stream_end()
                state.clear_retrying()
                raise
            except RetryableError:
                if ws_handler:
                    ws_handler.put_stream_end()
                state.clear_retrying()
                raise
            except Exception as e:
                # 确保流式输出结束标记已发送
                if ws_handler:
                    ws_handler.put_stream_end()
                classified = _classify_openai_error(e)
                if isinstance(classified, RetryableError):
                    last_error = classified
                    if attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        logger.warning(
                            f"AI 调用失败（第{attempt}次，{delay}秒后重试）: {classified}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"AI 调用失败（已重试{MAX_RETRIES}次）: {classified}")
                        state.clear_retrying()
                        raise classified
                else:
                    logger.error(f"AI 调用失败（不可重试）: {classified}")
                    state.clear_retrying()
                    raise classified
        state.clear_retrying()
        if last_error:
            raise last_error

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
        if self._state.request_cancel():
            return {"success": True, "message": "处理已取消"}
        return {"success": False, "error": "当前没有正在进行的处理任务"}

    # ---- 失败记录持久化（SQLite） ----

    @staticmethod
    def _persist_failed_records():
        """将当前任务中的失败文件写入数据库，同时移除已成功的记录"""
        state = ProcessingState()
        with state._state_lock:
            failed = [
                {"source": r["source"], "error": r.get("error", ""), "retryable": r.get("retryable", False)}
                for r in state._results if r.get("error")
            ]
            succeeded = [
                r["source"] for r in state._results if not r.get("error")
            ]

        db = SessionLocal()
        try:
            repo = FailedRecordRepository(db)
            # 新增失败记录
            if failed:
                count = repo.add_batch(failed)
                logger.info(f"失败记录已写入数据库: {count} 条")
            # 移除本次处理成功的记录（重跑成功后自动清除）
            for source in succeeded:
                repo.remove_by_source(source)
        except Exception as e:
            logger.error(f"持久化失败记录时出错: {e}")
        finally:
            db.close()

    @staticmethod
    def get_failed_records() -> dict:
        """读取数据库中的失败记录"""
        db = SessionLocal()
        try:
            repo = FailedRecordRepository(db)
            records = repo.get_all()
            return {"success": True, "failed": records, "count": len(records)}
        except Exception as e:
            logger.error(f"读取失败记录时出错: {e}")
            return {"success": False, "error": f"读取失败记录出错: {e}"}
        finally:
            db.close()

    @staticmethod
    def clear_failed_records() -> dict:
        """手动清除所有失败记录"""
        db = SessionLocal()
        try:
            repo = FailedRecordRepository(db)
            count = repo.clear_all()
            logger.info(f"失败记录已清除: {count} 条")
            return {"success": True, "message": f"已清除 {count} 条失败记录"}
        except Exception as e:
            return {"success": False, "error": f"清除失败记录出错: {e}"}
        finally:
            db.close()

    # ---- 部分重跑 ----

    def retry_failed(
        self,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
    ) -> dict:
        """仅重跑之前失败的文件"""
        if self._state.is_running():
            return {"success": False, "error": "已有任务正在运行"}

        # 从数据库读取失败记录
        db = SessionLocal()
        try:
            repo = FailedRecordRepository(db)
            failed_records = repo.get_all()
            failed_sources = repo.get_sources()
        except Exception as e:
            return {"success": False, "error": f"读取失败记录出错: {e}"}
        finally:
            db.close()

        if not failed_records:
            return {"success": False, "error": "没有失败记录可重跑"}

        # 验证文件仍然存在
        existing_sources = [s for s in failed_sources if os.path.exists(s)]
        if not existing_sources:
            return {"success": False, "error": "失败记录中的文件已不存在，请清除失败记录"}

        # 验证 provider/prompt
        provider = self._db.query(Provider).filter(Provider.name == provider_name, Provider.is_active == True).first()
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        models = _safe_json_loads(provider.models_json)
        if model_key not in models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = models[model_key]

        prompt = self._db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        client = OpenAI(api_key=api_key, base_url=provider.base_url)
        logger.info(f"启动失败重跑: {len(existing_sources)} 个文件")

        thread = threading.Thread(
            target=self._run_retry_batch,
            args=(existing_sources, client, prompt.content, model_id),
            daemon=True,
        )
        thread.start()
        return {"success": True, "message": f"重跑已启动，共 {len(existing_sources)} 个文件"}

    def _run_retry_batch(self, file_paths, client, prompt_content, model_id):
        """重跑失败文件的主循环"""
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            self._state.start_processing(len(file_paths))
            logger.info(f"开始重跑 {len(file_paths)} 个失败文件")

            for i, file_path in enumerate(file_paths):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                progress_before = int((i / len(file_paths)) * 100)
                self._state.update_progress(i, os.path.basename(file_path), progress_before)
                logger.info(f"重跑文件 [{i+1}/{len(file_paths)}]: {os.path.basename(file_path)}")
                result = self._process_file(file_path, client, prompt_content, model_id)
                progress_after = int(((i + 1) / len(file_paths)) * 100)
                self._state.update_progress(i + 1, None, progress_after)
                self._state.add_result(
                    result["source"],
                    result.get("output"),
                    result.get("error"),
                    result.get("retryable", False),
                )

            self._state.complete()
            with self._state._state_lock:
                results = list(self._state._results)
            success_count = sum(1 for r in results if not r.get("error"))
            fail_count = sum(1 for r in results if r.get("error"))
            logger.info(f"重跑完成: 共处理 {len(file_paths)} 个文件, 成功 {success_count} 个, 失败 {fail_count} 个")
            self._persist_failed_records()
        except Exception as e:
            logger.error(f"重跑任务失败: {e}")
            self._state.set_error(f"重跑失败: {str(e)}")
            self._persist_failed_records()
