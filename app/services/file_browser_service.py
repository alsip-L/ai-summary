# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from core.utils import read_file_with_encoding
from core.errors import FileProcessingError
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()

# 默认允许的路径：项目 data 目录
_DEFAULT_ALLOWED_PATH = str(Path(__file__).parent.parent.parent / "data")


class FileBrowserService:
    def _validate_path(self, path: str) -> bool:
        """校验路径是否在 allowed_paths 白名单内

        allowed_paths 为空时默认限制到项目 data 目录（防止任意路径访问）。
        非空时仅允许访问列表中路径及其子路径。
        拒绝过于宽泛的路径（如根目录 / 或 C:\）。
        """
        allowed_paths = ConfigManager().get("system_settings.allowed_paths", [])
        if not allowed_paths:
            # 默认限制到 data 目录，而非允许所有路径
            allowed_paths = [_DEFAULT_ALLOWED_PATH]

        # 过滤掉过于宽泛的路径（根目录）
        import re
        _DANGEROUS_ROOTS = {"/", "\\"}
        allowed_paths = [
            p for p in allowed_paths
            if p.rstrip("\\/") not in _DANGEROUS_ROOTS
            and not re.match(r'^[A-Za-z]:[\\/]?

        if not allowed_paths:
            allowed_paths = [_DEFAULT_ALLOWED_PATH]

        real_path = os.path.realpath(path)
        for allowed in allowed_paths:
            real_allowed = os.path.realpath(allowed)
            if real_path == real_allowed or real_path.startswith(real_allowed + os.sep):
                return True
        return False

    def get_drives(self) -> dict:
        try:
            drives = []
            if sys.platform == "win32":
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
            else:
                drives.append("/")
            return {"success": True, "drives": drives}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_directory(self, path: str) -> dict:
        if not path:
            return self.get_drives()
        if not self._validate_path(path):
            logger.warning(f"路径遍历防护: 拒绝访问路径 {path}")
            return {"success": False, "error": "路径不在允许的访问范围内"}
        if not os.path.exists(path) or not os.path.isdir(path):
            return {"success": False, "error": "路径不存在"}

        parent = os.path.dirname(path)
        if sys.platform == "win32" and parent == "":
            parent = None
        elif parent == path:
            parent = None

        directories = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    directories.append({"name": item, "path": item_path})
        except PermissionError:
            return {"success": False, "error": "权限不足，无法访问该目录"}

        directories.sort(key=lambda x: x["name"].lower())
        return {"success": True, "path": path, "parent": parent, "directories": directories}

    def view_result(self, file_path: str) -> dict:
        if not file_path:
            return {"success": False, "error": "未提供文件路径"}
        if not self._validate_path(file_path):
            logger.warning(f"路径遍历防护: 拒绝访问文件 {file_path}")
            return {"success": False, "error": "路径不在允许的访问范围内"}

        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path) or not os.path.isfile(real_path):
            return {"success": False, "error": "文件不存在"}
        if not real_path.endswith((".md", ".txt")):
            return {"success": False, "error": "不支持的文件类型"}

        try:
            content = read_file_with_encoding(real_path)
            return {
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(real_path),
                "content": content,
            }
        except FileProcessingError:
            return {"success": False, "error": "文件读取失败"}
, p)  # 匹配 C:\, C:/, C: 等盘符根
            and len(p.rstrip("\\")) > 3
        ]

        if not allowed_paths:
            allowed_paths = [_DEFAULT_ALLOWED_PATH]

        real_path = os.path.realpath(path)
        for allowed in allowed_paths:
            real_allowed = os.path.realpath(allowed)
            if real_path == real_allowed or real_path.startswith(real_allowed + os.sep):
                return True
        return False

    def get_drives(self) -> dict:
        try:
            drives = []
            if sys.platform == "win32":
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
            else:
                drives.append("/")
            return {"success": True, "drives": drives}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_directory(self, path: str) -> dict:
        if not path:
            return self.get_drives()
        if not self._validate_path(path):
            logger.warning(f"路径遍历防护: 拒绝访问路径 {path}")
            return {"success": False, "error": "路径不在允许的访问范围内"}
        if not os.path.exists(path) or not os.path.isdir(path):
            return {"success": False, "error": "路径不存在"}

        parent = os.path.dirname(path)
        if sys.platform == "win32" and parent == "":
            parent = None
        elif parent == path:
            parent = None

        directories = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    directories.append({"name": item, "path": item_path})
        except PermissionError:
            return {"success": False, "error": "权限不足，无法访问该目录"}

        directories.sort(key=lambda x: x["name"].lower())
        return {"success": True, "path": path, "parent": parent, "directories": directories}

    def view_result(self, file_path: str) -> dict:
        if not file_path:
            return {"success": False, "error": "未提供文件路径"}
        if not self._validate_path(file_path):
            logger.warning(f"路径遍历防护: 拒绝访问文件 {file_path}")
            return {"success": False, "error": "路径不在允许的访问范围内"}

        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path) or not os.path.isfile(real_path):
            return {"success": False, "error": "文件不存在"}
        if not real_path.endswith((".md", ".txt")):
            return {"success": False, "error": "不支持的文件类型"}

        try:
            content = read_file_with_encoding(real_path)
            return {
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(real_path),
                "content": content,
            }
        except FileProcessingError:
            return {"success": False, "error": "文件读取失败"}
