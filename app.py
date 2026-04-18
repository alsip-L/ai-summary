# -*- coding: utf-8 -*-
import sys
import codecs

# 重定向输出到UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        pass

from flask import Flask, jsonify
from core.config import ConfigManager
from core.errors import AISummaryException, ValidationError, ProviderError, FileProcessingError

# 初始化Flask应用
app = Flask(__name__, static_folder="frontend", static_url_path="/static")
app.secret_key = ConfigManager().get('system_settings.flask_secret_key', 'default-dev-secret-key-please-change-in-prod')

# 全局错误处理器 — 统一返回 {"success": false, "error": "描述"}
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"success": False, "error": e.message}), 400

@app.errorhandler(ProviderError)
def handle_provider_error(e):
    return jsonify({"success": False, "error": e.message}), 400

@app.errorhandler(FileProcessingError)
def handle_file_error(e):
    return jsonify({"success": False, "error": e.message}), 500

@app.errorhandler(AISummaryException)
def handle_base_error(e):
    return jsonify({"success": False, "error": e.message}), 500

# 注册功能模块蓝图
from features.provider import provider_bp
from features.prompt import prompt_bp
from features.task import task_bp
from features.file_browser import file_bp
from features.trash import trash_bp
from features.settings import settings_bp
from features.pages import page_bp

app.register_blueprint(provider_bp)
app.register_blueprint(prompt_bp)
app.register_blueprint(task_bp)
app.register_blueprint(file_bp)
app.register_blueprint(trash_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(page_bp)
