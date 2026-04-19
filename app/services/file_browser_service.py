# -*- coding: utf-8 -*-
import sys
import os
from core.utils import read_file_with_encoding
from core.errors import FileProcessingError


class FileBrowserService:
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
            pass

        directories.sort(key=lambda x: x["name"].lower())
        return {"success": True, "path": path, "parent": parent, "directories": directories}

    def view_result(self, file_path: str) -> dict:
        if not file_path:
            return {"success": False, "error": "未提供文件路径"}

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
