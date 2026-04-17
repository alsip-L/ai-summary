# -*- coding: utf-8 -*-
"""AI 文件处理服务 — 合并原 ai_processor.py + task_processor.py"""

import os
from openai import OpenAI
from models.task import TaskResult
from services.state_service import ProcessingState
from core.log import get_logger
from core.errors import FileProcessingError, ProviderError

logger = get_logger()


class ProcessingService:
    """AI 文件处理服务"""

    def __init__(self, state: ProcessingState):
        self._state = state

    # ---- 单文件处理（原 AIProcessor.process_file + save_response）----

    @staticmethod
    def read_file(file_path: str) -> str:
        for encoding in ["utf-8", "gbk"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise FileProcessingError(f"无法解码文件: {os.path.basename(file_path)}")

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
        except (FileProcessingError, ProviderError):
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

    # ---- 批量处理（原 task_processor.run_processing_task）----

    @staticmethod
    def scan_txt_files(directory: str) -> list[str]:
        if not os.path.isdir(directory):
            raise ValueError(f"目录不存在: {directory}")
        txt_files = []
        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith(".txt"):
                    txt_files.append(os.path.join(root, f))
        return txt_files

    def run_batch(self, directory: str, client: OpenAI, prompt: str, model_id: str) -> None:
        self._state.start()
        try:
            if self._state.is_cancelled():
                self._state.cancel()
                return

            txt_files = self.scan_txt_files(directory)
            if not txt_files:
                raise ValueError("未找到 txt 文件")

            self._state.start_processing(len(txt_files))

            for i, file_path in enumerate(txt_files):
                if self._state.is_cancelled():
                    self._state.cancel()
                    return

                self._state.update_progress(i, os.path.basename(file_path))
                result = self.process_file(file_path, client, prompt, model_id)
                progress = int(((i + 1) / len(txt_files)) * 100)
                self._state.update_progress(i + 1, None, progress)
                self._state.add_result(result.source, result.output, result.error)

            self._state.complete()
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            self._state.set_error(f"处理失败: {str(e).splitlines()[0]}")
