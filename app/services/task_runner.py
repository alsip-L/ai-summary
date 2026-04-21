# -*- coding: utf-8 -*-
import os
import time
from openai import OpenAI
from app.services.processing_state import ProcessingState, FILE_MAX_RETRIES, RETRY_BASE_DELAY
from app.services.file_processor import FileProcessor
from app.services.failed_record_service import FailedRecordService
from core.log import get_logger

logger = get_logger()


class TaskRunner:
    """批量文件处理任务执行器"""

    def __init__(
        self,
        state: ProcessingState,
        file_processor: FileProcessor,
        failed_record_service: FailedRecordService,
    ):
        self._state = state
        self._file_processor = file_processor
        self._failed_record_svc = failed_record_service

    def run_batch(self, directory, client, prompt_content, model_id, skip_existing):
        """批量处理主循环"""
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            logger.info(f"开始扫描目录: {directory}")
            txt_files = self._file_processor.scan_txt_files(directory, skip_existing)
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
                result = self._process_file_with_retry(file_path, client, prompt_content, model_id)
                progress_after = int(((i + 1) / len(txt_files)) * 100)
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
            logger.info(f"处理完成: 共处理 {len(txt_files)} 个文件, 成功 {success_count} 个, 失败 {fail_count} 个")
            self._failed_record_svc.persist_from_state()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e)}")
            self._failed_record_svc.persist_from_state()

    def run_retry_batch(self, file_paths, client, prompt_content, model_id):
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
                result = self._process_file_with_retry(file_path, client, prompt_content, model_id)
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
            self._failed_record_svc.persist_from_state()
        except Exception as e:
            logger.error(f"重跑任务失败: {e}")
            self._state.set_error(f"重跑失败: {str(e)}")
            self._failed_record_svc.persist_from_state()

    def _process_file_with_retry(self, file_path, client, prompt_content, model_id):
        """处理单个文件，失败时自动重试（仅对可重试错误，最多FILE_MAX_RETRIES次）"""
        result = self._file_processor.process_file(file_path, client, prompt_content, model_id)

        # 如果成功或不可重试，直接返回
        if not result.get("error") or not result.get("retryable"):
            return result

        # 可重试错误：自动重试
        last_error = result["error"]
        for attempt in range(2, FILE_MAX_RETRIES + 1):
            if self._state.is_cancelled():
                logger.info(f"文件重试已取消: {os.path.basename(file_path)}")
                return {"source": file_path, "error": "用户取消了处理", "retryable": False}

            delay = RETRY_BASE_DELAY * (2 ** (attempt - 2))
            logger.warning(
                f"文件处理失败，第 {attempt}/{FILE_MAX_RETRIES} 次重试 "
                f"({delay}秒后): {os.path.basename(file_path)} - {last_error}"
            )
            self._state.set_retrying(attempt)
            time.sleep(delay)

            if self._state.is_cancelled():
                self._state.clear_retrying()
                logger.info(f"文件重试已取消: {os.path.basename(file_path)}")
                return {"source": file_path, "error": "用户取消了处理", "retryable": False}

            result = self._file_processor.process_file(file_path, client, prompt_content, model_id)
            if not result.get("error"):
                logger.info(f"文件重试成功（第{attempt}次）: {os.path.basename(file_path)}")
                self._state.clear_retrying()
                return result

            if not result.get("retryable"):
                self._state.clear_retrying()
                return result

            last_error = result["error"]

        # 所有重试都失败
        logger.error(
            f"文件处理失败（已重试{FILE_MAX_RETRIES}次）: "
            f"{os.path.basename(file_path)} - {last_error}"
        )
        self._state.clear_retrying()
        return {"source": file_path, "error": f"重试{FILE_MAX_RETRIES}次仍失败: {last_error}", "retryable": True}
