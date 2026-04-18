# -*- coding: utf-8 -*-
"""页面路由"""

from flask import Blueprint, send_from_directory
import os

page_bp = Blueprint("pages", __name__)

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


@page_bp.route("/")
def index():
    """渲染主页面"""
    return send_from_directory(_FRONTEND_DIR, "index.html")
