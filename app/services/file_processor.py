# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from core.errors import RetryableError, FileProcessingError
from core.utils import read_file_with_encoding
from core.log import get_logger
from app.services.ai_client import AIClient

logger = get_logger()


class FileProcessor:
    """封装文件扫描、处理和结果保存逻辑"""

    def __init__(self, ai_client: AIClient):
        self._ai_client = ai_client

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

    def process_file(self, file_path: str, client: OpenAI, prompt_content: str, model_id: str, temperature: float = 0.7, frequency_penalty: float = 0.4, presence_penalty: float = 0.2) -> dict:
        """处理单个文件：读取 → AI调用 → 保存"""
        try:
            content = read_file_with_encoding(file_path)
            logger.info(f"读取文件完成: {os.path.basename(file_path)}, 字符数: {len(content)}")
            response = self._ai_client.call(client, content, prompt_content, model_id, temperature, frequency_penalty, presence_penalty)
            output_path = self.save_response(file_path, response)
            logger.info(f"文件处理成功: {os.path.basename(file_path)} -> {os.path.basename(output_path)}")
            return {"source": file_path, "output": output_path}
        except RetryableError as e:
            logger.error(f"文件处理失败（可重试）: {os.path.basename(file_path)} - {e}")
            return {"source": file_path, "error": str(e), "retryable": True}
        except Exception as e:
            logger.error(f"文件处理失败: {os.path.basename(file_path)} - {e}")
            return {"source": file_path, "error": str(e), "retryable": False}

    @staticmethod
    def save_response(file_path: str, response: str) -> str:
        """保存 AI 响应为 .md 文件"""
        md_path = os.path.splitext(file_path)[0] + ".md"
        try:
            if os.path.exists(md_path):
                logger.warning(f"覆盖已有结果文件: {os.path.basename(md_path)}")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(response)
            return md_path
        except Exception as e:
            raise FileProcessingError(f"保存结果失败: {e}")
