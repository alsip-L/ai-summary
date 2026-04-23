# -*- coding: utf-8 -*-
"""公共工具函数"""

import json
import os
from core.errors import FileProcessingError
from core.log import get_logger

logger = get_logger()


def safe_json_loads(json_str: str, fallback=None):
    """安全解析 JSON，失败时返回降级值

    Args:
        json_str: JSON 字符串
        fallback: 解析失败时的降级返回值，默认为空字典
    """
    if fallback is None:
        fallback = {}
    if not json_str:
        return fallback
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"JSON解析失败，降级为{fallback}: {str(json_str)[:50]}")
        return fallback


def read_file_with_encoding(file_path: str, encodings: list[str] = None, max_size: int = 10 * 1024 * 1024) -> str:
    """尝试多种编码读取文件内容

    Args:
        file_path: 文件路径
        encodings: 尝试的编码列表
        max_size: 最大读取字节数，默认 10MB，防止 OOM
    """
    if encodings is None:
        encodings = ["utf-8", "gbk"]
    try:
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise FileProcessingError(f"文件过大 ({file_size} 字节，上限 {max_size} 字节): {os.path.basename(file_path)}")
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise FileProcessingError(f"无法解码文件: {os.path.basename(file_path)}")
    except FileNotFoundError:
        raise FileProcessingError(f"文件不存在: {os.path.basename(file_path)}")
    except PermissionError:
        raise FileProcessingError(f"无权限读取文件: {os.path.basename(file_path)}")
    except OSError as e:
        raise FileProcessingError(f"读取文件失败: {os.path.basename(file_path)} ({e})")
