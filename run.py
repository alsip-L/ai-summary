# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from core.config import ConfigManager


def main():
    settings = ConfigManager().get('system_settings', {})
    host = settings.get('host', '0.0.0.0')
    port = int(settings.get('port', 5000))
    debug = settings.get('debug', False)

    print(f"Starting AI Summary application...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Access: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")

    # 配置 uvicorn 日志，避免 buffer detached 错误
    log_config = uvicorn.config.LOGGING_CONFIG.copy()
    log_config["handlers"]["default"] = {
        "()": "core.log.SafeStreamHandler",
        "stream": "ext://sys.stdout",
    }
    log_config["handlers"]["access"] = {
        "()": "core.log.SafeStreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "access",
    }
    log_config["loggers"]["uvicorn"]["handlers"] = ["default"]
    log_config["loggers"]["uvicorn.error"]["handlers"] = ["default"]
    log_config["loggers"]["uvicorn.access"]["handlers"] = ["access"]

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_config=log_config,
    )


if __name__ == '__main__':
    main()
