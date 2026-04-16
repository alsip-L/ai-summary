# -*- coding: utf-8 -*-
"""文件处理模块"""

import os
from pathlib import Path
from typing import List, Optional
from core.logger import get_logger
from core.exceptions import FileProcessingError

logger = get_logger()


class FileProcessor:
    """文件处理器
    
    封装文件相关的操作，包括扫描、读取和保存。
    """
    
    def __init__(self, directory: str):
        """初始化文件处理器
        
        Args:
            directory: 目标目录路径
            
        Raises:
            FileProcessingError: 当目录不存在时抛出
        """
        self.directory = Path(directory)
        if not self.directory.exists():
            raise FileProcessingError(f"目录不存在: {directory}")
        if not self.directory.is_dir():
            raise FileProcessingError(f"路径不是目录: {directory}")
        
        logger.info(f"文件处理器初始化: {directory}")
    
    def scan_txt_files(self) -> List[Path]:
        """扫描目录中的 txt 文件
        
        递归扫描目录及其子目录中的所有 .txt 文件。
        
        Returns:
            txt 文件路径列表
        """
        try:
            txt_files = list(self.directory.rglob("*.txt"))
            logger.info(f"扫描目录 {self.directory}，找到 {len(txt_files)} 个 txt 文件")
            return txt_files
        except Exception as e:
            logger.error(f"扫描文件失败: {e}")
            raise FileProcessingError(f"扫描文件失败: {e}")
    
    def read_file(self, file_path: Path) -> str:
        """读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
            
        Raises:
            FileProcessingError: 当文件读取失败时抛出
        """
        # 验证文件存在性
        if not file_path.exists():
            raise FileProcessingError(f"文件不存在: {file_path}")
        if not file_path.is_file():
            raise FileProcessingError(f"路径不是文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"读取文件成功: {file_path}")
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                logger.debug(f"使用 GBK 编码读取文件成功: {file_path}")
                return content
            except Exception as e:
                logger.error(f"读取文件失败 (GBK): {file_path}, {e}")
                raise FileProcessingError(f"读取文件失败: {file_path}, {e}")
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            raise FileProcessingError(f"读取文件失败: {file_path}, {e}")
    
    def save_response(self, source_file: Path, content: str) -> Path:
        """保存响应内容为 Markdown 文件
        
        将生成的内容保存为与源文件同名的 .md 文件。
        
        Args:
            source_file: 源文件路径
            content: 要保存的内容
            
        Returns:
            保存的文件路径
            
        Raises:
            FileProcessingError: 当保存失败时抛出
        """
        md_file = source_file.with_suffix('.md')
        
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"保存响应成功: {md_file}")
            return md_file
        except Exception as e:
            logger.error(f"保存响应失败: {md_file}, {e}")
            raise FileProcessingError(f"保存响应失败: {md_file}, {e}")
    
    def get_file_info(self, file_path: Path) -> dict:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文件信息的字典
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, {e}")
            raise FileProcessingError(f"获取文件信息失败: {file_path}, {e}")


# 向后兼容的函数
def scan_txt_files(directory: str) -> List[str]:
    """扫描目录中的 txt 文件（向后兼容）"""
    processor = FileProcessor(directory)
    files = processor.scan_txt_files()
    return [str(f) for f in files]


def save_response(file_path: str, response: str) -> str:
    """保存响应（向后兼容）"""
    source = Path(file_path)
    processor = FileProcessor(str(source.parent))
    result = processor.save_response(source, response)
    return str(result)
