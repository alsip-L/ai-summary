# -*- coding: utf-8 -*-
"""文件处理服务模块

.. deprecated::
    此模块当前未被主流程使用，功能由 utils.py 中的 FileManager 提供。
    保留供未来架构迁移使用。
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from openai import OpenAI
from core.config_manager import ConfigManager
from core.exceptions import FileProcessingError, ProviderError
from core.logger import get_logger

logger = get_logger()


class FileService:
    """文件处理服务类

    封装文件扫描、读取、保存和处理等功能
    """

    def __init__(self):
        self.config = ConfigManager()

    def scan_txt_files(self, directory: str) -> List[str]:
        """扫描目录中的txt文件

        Args:
            directory: 要扫描的目录路径

        Returns:
            txt文件路径列表

        Raises:
            FileProcessingError: 当目录无效时抛出
        """
        if not os.path.isdir(directory):
            raise FileProcessingError(f"目录不存在: {directory}")

        try:
            txt_files = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.txt'):
                        txt_files.append(os.path.join(root, file))

            logger.info(f"扫描目录 {directory}，找到 {len(txt_files)} 个txt文件")
            return txt_files
        except Exception as e:
            logger.error(f"扫描txt文件失败: {e}")
            raise FileProcessingError(f"扫描txt文件失败: {e}")

    def read_file(self, file_path: str) -> str:
        """读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容

        Raises:
            FileProcessingError: 当文件读取失败时抛出
        """
        path = Path(file_path)

        if not path.exists():
            raise FileProcessingError(f"文件不存在: {file_path}")
        if not path.is_file():
            raise FileProcessingError(f"路径不是文件: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"读取文件成功: {file_path}")
            return content
        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='gbk') as f:
                    content = f.read()
                logger.debug(f"使用 GBK 编码读取文件成功: {file_path}")
                return content
            except Exception as e:
                logger.error(f"读取文件失败 (GBK): {file_path}, {e}")
                raise FileProcessingError(f"读取文件失败: {e}")
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            raise FileProcessingError(f"读取文件失败: {e}")

    def save_response(self, source_file: str, content: str) -> str:
        """保存响应内容为Markdown文件

        Args:
            source_file: 源文件路径
            content: 要保存的内容

        Returns:
            保存的文件路径

        Raises:
            FileProcessingError: 当保存失败时抛出
        """
        path = Path(source_file)
        md_file = path.with_suffix('.md')

        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"保存响应成功: {md_file}")
            return str(md_file)
        except Exception as e:
            logger.error(f"保存响应失败: {md_file}, {e}")
            raise FileProcessingError(f"保存响应失败: {e}")

    def process_single_file(
        self,
        file_path: str,
        client: OpenAI,
        system_prompt: str,
        model_id: str
    ) -> str:
        """处理单个文件

        Args:
            file_path: 文件路径
            client: OpenAI客户端
            system_prompt: 系统提示词
            model_id: 模型ID

        Returns:
            AI生成的响应内容

        Raises:
            FileProcessingError: 当文件处理失败时抛出
            ProviderError: 当AI调用失败时抛出
        """
        try:
            content = self.read_file(file_path)

            start_time = time.time()
            logger.info(f"开始处理文件: {os.path.basename(file_path)}, 模型: {model_id}")

            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': content}
                ],
                stream=False
            )

            if completion is None or completion.choices is None or len(completion.choices) == 0:
                raise ProviderError("API返回空响应")

            response_content = completion.choices[0].message.content
            duration = time.time() - start_time

            logger.info(f"处理文件 {os.path.basename(file_path)} 耗时 {duration:.2f}秒")
            return response_content

        except ProviderError:
            raise
        except FileProcessingError:
            raise
        except Exception as e:
            error_msg = f"处理文件 '{os.path.basename(file_path)}' 时出错: {str(e).splitlines()[0]}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg)

    def get_output_path(self, input_file_path: str, output_dir: str = None) -> str:
        """根据输入文件路径生成输出文件路径

        Args:
            input_file_path: 输入文件完整路径
            output_dir: 输出目录（可选，默认与输入路径相同）

        Returns:
            输出md文件的路径
        """
        input_path = Path(input_file_path)

        if output_dir:
            relative = input_path.name
            output_path = Path(output_dir) / relative.replace('.txt', '.md')
        else:
            output_path = input_path.with_suffix('.md')

        return str(output_path)

    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            包含文件信息的字典
        """
        path = Path(file_path)

        try:
            stat = path.stat()
            return {
                'name': path.name,
                'path': str(path),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, {e}")
            raise FileProcessingError(f"获取文件信息失败: {e}")
