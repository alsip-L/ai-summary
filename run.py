# -*- coding: utf-8 -*-
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from core.config import ConfigManager


class _SafeStreamHandler(logging.StreamHandler):
    """防止 buffer detached 的 StreamHandler，用于 uvicorn root logger"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._null_stream = None  # 缓存 null 设备，避免重复打开泄漏 fd

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if stream is None:
                return
            try:
                stream.write(msg + self.terminator)
                stream.flush()
            except (ValueError, AttributeError, OSError):
                self._recover_stream()
                try:
                    self.stream.write(msg + self.terminator)
                    self.stream.flush()
                except Exception:
                    pass
        except Exception:
            pass

    def _recover_stream(self):
        """尝试恢复 stdout 流"""
        try:
            if hasattr(sys, '__stdout__') and sys.__stdout__ is not None:
                self.stream = sys.__stdout__
            elif sys.stdout is not None and hasattr(sys.stdout, 'write'):
                self.stream = sys.stdout
            else:
                # 复用 null 设备，避免每次恢复都泄漏文件描述符
                if self._null_stream is None:
                    if sys.platform == 'win32':
                        self._null_stream = open('NUL', 'w')
                    else:
                        self._null_stream = open('/dev/null', 'w')
                self.stream = self._null_stream
        except Exception:
            pass


def _patch_root_logger():
    """替换 root logger 的 StreamHandler 为安全版本"""
    root = logging.getLogger()
    for i, h in enumerate(root.handlers):
        if isinstance(h, logging.StreamHandler) and not isinstance(h, _SafeStreamHandler):
            safe = _SafeStreamHandler(h.stream)
            safe.setFormatter(h.formatter)
            safe.setLevel(h.level)
            root.handlers[i] = safe


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
        "()": __name__ + "._SafeStreamHandler",
        "stream": "ext://sys.stdout",
    }
    log_config["handlers"]["access"] = {
        "()": __name__ + "._SafeStreamHandler",
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
