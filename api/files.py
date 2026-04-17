# -*- coding: utf-8 -*-
"""文件 API"""

import sys
import os
from flask import Blueprint, request, jsonify
from core.log import get_logger

logger = get_logger()
file_bp = Blueprint("api_files", __name__, url_prefix="/api/files")


@file_bp.get("/drives")
def get_drives():
    """GET /api/files/drives"""
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
        return jsonify({"success": True, "drives": drives})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@file_bp.get("/directory")
def get_directory():
    """GET /api/files/directory?path=xxx"""
    path = request.args.get("path", "")
    if not path:
        return get_drives()
    if not os.path.exists(path) or not os.path.isdir(path):
        return jsonify({"success": False, "error": "路径不存在"}), 400

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
    return jsonify({"success": True, "path": path, "parent": parent, "directories": directories})


@file_bp.get("/result")
def view_result():
    """GET /api/files/result?path=xxx"""
    file_path = request.args.get("path", "")
    if not file_path:
        return jsonify({"success": False, "error": "未提供文件路径"}), 400

    real_path = os.path.realpath(file_path)
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        return jsonify({"success": False, "error": "文件不存在"}), 404
    if not real_path.endswith((".md", ".txt")):
        return jsonify({"success": False, "error": "不支持的文件类型"}), 400

    for encoding in ["utf-8", "gbk"]:
        try:
            with open(real_path, "r", encoding=encoding) as f:
                content = f.read()
            return jsonify({
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(real_path),
                "content": content,
            })
        except UnicodeDecodeError:
            continue
    return jsonify({"success": False, "error": "文件读取失败"}), 500
