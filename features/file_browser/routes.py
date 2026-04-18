# -*- coding: utf-8 -*-
"""文件浏览 API 路由"""

from flask import Blueprint, request, jsonify
from .service import FileBrowserService

file_bp = Blueprint("api_files", __name__, url_prefix="/api/files")

_svc = FileBrowserService()


@file_bp.get("/drives")
def get_drives():
    """GET /api/files/drives"""
    result = _svc.get_drives()
    if result.get("success"):
        return jsonify(result)
    return jsonify(result), 500


@file_bp.get("/directory")
def get_directory():
    """GET /api/files/directory?path=xxx"""
    path = request.args.get("path", "")
    result = _svc.get_directory(path)
    if result.get("success"):
        return jsonify(result)
    return jsonify(result), 400


@file_bp.get("/result")
def view_result():
    """GET /api/files/result?path=xxx"""
    file_path = request.args.get("path", "")
    result = _svc.view_result(file_path)
    if result.get("success"):
        return jsonify(result)
    if "不存在" in result.get("error", ""):
        return jsonify(result), 404
    return jsonify(result), 400
