# -*- coding: utf-8 -*-
import sys
import codecs

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except Exception:
        pass

# 重定向输出到UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        pass

from flask import Flask
from core.config import ConfigManager

# 初始化Flask应用
app = Flask(__name__, static_folder="frontend", static_url_path="/static")
app.secret_key = ConfigManager().get('system_settings.flask_secret_key', 'default-dev-secret-key-please-change-in-prod')

# 注册新 API 蓝图
from api.providers import provider_bp
from api.prompts import prompt_bp
from api.tasks import task_bp
from api.files import file_bp
from api.settings import settings_bp
from api.pages import page_bp

app.register_blueprint(provider_bp)
app.register_blueprint(prompt_bp)
app.register_blueprint(task_bp)
app.register_blueprint(file_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(page_bp)

if __name__ == '__main__':
    settings = ConfigManager().get('system_settings', {})
    debug_level = settings.get('debug_level', 'ERROR').upper()
    host = settings.get('host', '0.0.0.0')
    port = settings.get('port', 5000)
    debug = settings.get('debug', False) or debug_level == 'DEBUG'
    app.run(debug=debug, host=host, port=port)
