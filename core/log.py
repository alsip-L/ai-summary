# -*- coding: utf-8 -*-
"""统一日志管理模块"""

import logging
import sys
import json
import queue
from pathlib import Path
from functools import lru_cache

LOGGER_NAME = "ai_summary"


class WebSocketLogHandler(logging.Handler):
    """将日志消息放入队列，由 WebSocket 端消费"""

    def __init__(self):
        super().__init__()
        self._queue = queue.Queue()

    def emit(self, record):
        try:
            msg = self.format(record)
            self._queue.put_nowait(msg)
        except Exception:
            pass

    def put_stream(self, token: str):
        """直接放入流式内容（绕过 logging 格式化）"""
        try:
            self._queue.put_nowait(json.dumps({"type": "stream", "data": token}, ensure_ascii=False))
        except Exception:
            pass

    def put_stream_end(self):
        """标记流式输出结束"""
        try:
            self._queue.put_nowait(json.dumps({"type": "stream_end"}))
        except Exception:
            pass

    def get_pending(self):
        """获取所有待发送的日志消息"""
        messages = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return messages


def get_ws_handler() -> WebSocketLogHandler:
    """从 logger 中获取 WebSocketLogHandler 实例"""
    logger = logging.getLogger(LOGGER_NAME)
    for h in logger.handlers:
        if isinstance(h, WebSocketLogHandler):
            return h
    return None


def _get_log_level() -> int:
    """从配置文件读取日志级别"""
    try:
        config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        level_str = config.get('system_settings', {}).get('debug_level', 'ERROR').upper()
    except Exception:
        level_str = 'ERROR'

    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level_str in valid_levels:
        return getattr(logging, level_str)
    return logging.ERROR


@lru_cache()
def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        ws_handler = WebSocketLogHandler()
        ws_handler.setFormatter(formatter)
        logger.addHandler(ws_handler)

        logger.setLevel(_get_log_level())
        logger.propagate = False
    return logger


def update_log_level(level_str: str) -> bool:
    """动态更新日志级别（热更新）"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level_upper = level_str.upper()
    if level_upper not in valid_levels:
        return False
    logger = get_logger()
    logger.setLevel(getattr(logging, level_upper))
    return True
