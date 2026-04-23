# -*- coding: utf-8 -*-
import sys
import os
import re
from pathlib import Path
from core.utils import read_file_with_encoding
from core.errors import FileProcessingError
from core.config import ConfigManager
from core.log import get_logger

logger = get_logger()

_DEFAULT_ALLOWED_PATH = str(Path(__file__).parent.parent.parent / "data")

_DANGEROUS_ROOTS = {"/", "\\"}
_ROOT_DRIVE_RE = re.compile(r'^[A-Za-z]:[\\/]?$', re.IGNORECASE)


class FileBrowserService:
    def _validate_path(self, path: str) -> bool:
        allowed_paths = ConfigManager().get("system_settings.allowed_paths", [])
        if not allowed_paths:
            allowed_paths = [_DEFAULT_ALLOWED_PATH]

        allowed_paths = [
            p for p in allowed_paths
            if p.rstrip("\\/") not in _DANGEROUS_ROOTS
            and not _ROOT_DRIVE_RE.match(p)
            and len(p.rstrip("\\/")) > 3
        ]

        if not allowed_paths:
            allowed_paths = [_DEFAULT_ALLOWED_PATH]

        real_path = os.path.realpath(path)
        for allowed in allowed_paths:
            real_allowed = os.path.realpath(allowed)
            # Windows 路径比较大小写不敏感
            if sys.platform == "win32":
                if real_path.lower() == real_allowed.lower() or real_path.lower().startswith(real_allowed.lower() + os.sep):
                    return True
            else:
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
            return {"success": False, "error": "未提供文件路径", "error_code": "invalid_request"}
        if not self._validate_path(file_path):
            logger.warning(f"路径遍历防护: 拒绝访问文件 {file_path}")
            return {"success": False, "error": "路径不在允许的访问范围内", "error_code": "forbidden"}

        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path) or not os.path.isfile(real_path):
            return {"success": False, "error": "文件不存在", "error_code": "not_found"}
        if not real_path.endswith((".md", ".txt")):
            return {"success": False, "error": "不支持的文件类型", "error_code": "unsupported_type"}

        try:
            content = read_file_with_encoding(real_path)
            return {
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(real_path),
                "content": content,
            }
        except FileProcessingError:
            return {"success": False, "error": "文件读取失败", "error_code": "read_error"}
