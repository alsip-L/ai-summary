# -*- coding: utf-8 -*-
"""公共工具函数"""

import os
from core.errors import FileProcessingError


def read_file_with_encoding(file_path: str, encodings: list[str] = None) -> str:
    """尝试多种编码读取文件内容"""
    if encodings is None:
        encodings = ["utf-8", "gbk"]
    try:
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
