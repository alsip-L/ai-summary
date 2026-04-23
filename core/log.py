# -*- coding: utf-8 -*-
"""统一日志管理模块

设计：
1. SafeStreamHandler — 防止 buffer detached 错误
2. WebSocketLogHandler — 统一缓冲区，普通日志和流式消息都写入
   - 每条记录带递增 seq，WebSocket 端按 seq 增量读取
   - 新连接可回放历史日志（含流式内容）
   - 多个 WebSocket 连接独立读取，互不干扰
"""

import logging
import sys
import json
import time
import threading
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from functools import lru_cache
from collections import deque

LOGGER_NAME = "ai_summary"

# 环形缓冲区大小：保留最近 N 条记录供新连接回放
LOG_BUFFER_SIZE = 2000

# 缓冲区记录最大保留天数，超过此天数的记录在读取时自动过滤
LOG_BUFFER_MAX_AGE_DAYS = 7


class SafeStreamHandler(logging.StreamHandler):
    """安全的 StreamHandler，处理 buffer detached 等异常"""

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


class WebSocketLogHandler(logging.Handler):
    """统一缓冲区日志 handler

    所有内容（普通日志 + 流式消息）都写入环形缓冲区，
    每条记录带递增 seq 和时间戳。WebSocket 端按 seq 增量读取，
    多个连接独立读取互不干扰，新连接可回放历史。
    超过 LOG_BUFFER_MAX_AGE_DAYS 天的记录在读取时自动过滤。
    """

    def __init__(self):
        super().__init__()
        self._buffer = deque(maxlen=LOG_BUFFER_SIZE)
        self._buffer_lock = threading.Lock()
        self._seq = 0

    def emit(self, record):
        """普通日志 → 写入缓冲区"""
        try:
            msg = self.format(record)
            with self._buffer_lock:
                self._seq += 1
                self._buffer.append((self._seq, msg, time.time()))
        except Exception:
            pass

    def put_stream(self, token: str):
        """流式内容 → 写入缓冲区（JSON 格式）"""
        try:
            msg = json.dumps({"type": "stream", "data": token}, ensure_ascii=False)
            with self._buffer_lock:
                self._seq += 1
                self._buffer.append((self._seq, msg, time.time()))
        except Exception:
            pass

    def put_stream_end(self):
        """流式输出结束 → 写入缓冲区"""
        try:
            msg = json.dumps({"type": "stream_end"})
            with self._buffer_lock:
                self._seq += 1
                self._buffer.append((self._seq, msg, time.time()))
        except Exception:
            pass

    def get_buffer_since(self, after_seq: int = 0) -> list[tuple[int, str]]:
        """获取序号大于 after_seq 的缓冲记录（增量读取）
        
        如果 after_seq 指向的记录已被环形缓冲区淘汰，
        则返回缓冲区中所有记录（从最旧的可用记录开始）。
        
        超过 LOG_BUFFER_MAX_AGE_DAYS 天的记录自动过滤，不返回。
        """
        max_age = LOG_BUFFER_MAX_AGE_DAYS * 86400  # 天转秒
        now = time.time()
        with self._buffer_lock:
            if not self._buffer:
                return []
            # 过滤超龄记录
            valid = [(seq, msg) for seq, msg, ts in self._buffer if now - ts <= max_age]
            if not valid:
                return []
            if after_seq <= 0:
                return valid
            min_seq = valid[0][0]
            if after_seq < min_seq:
                return valid
            return [(seq, msg) for seq, msg in valid if seq > after_seq]

    @property
    def current_seq(self) -> int:
        with self._buffer_lock:
            return self._seq

    @property
    def buffer_size(self) -> int:
        with self._buffer_lock:
            return len(self._buffer)

    def clear_buffer(self):
        """清空环形缓冲区中的所有记录"""
        with self._buffer_lock:
            self._buffer.clear()


def get_ws_handler() -> WebSocketLogHandler:
    """从 logger 中获取 WebSocketLogHandler 实例"""
    logger = logging.getLogger(LOGGER_NAME)
    for h in logger.handlers:
        if isinstance(h, WebSocketLogHandler):
            return h
    return None


def _get_log_level() -> int:
    """从 ConfigManager 读取日志级别"""
    try:
        from core.config import ConfigManager
        level_str = ConfigManager().get('system_settings.debug_level', 'ERROR').upper()
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

        stream_handler = SafeStreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        ws_handler = WebSocketLogHandler()
        ws_handler.setFormatter(formatter)
        logger.addHandler(ws_handler)

        # 文件日志：按天轮转，保留7天，自动清理过期日志文件
        try:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            file_handler = TimedRotatingFileHandler(
                filename=log_dir / "ai_summary.log",
                when='midnight',
                interval=1,
                backupCount=LOG_BUFFER_MAX_AGE_DAYS,
                encoding='utf-8',
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # 文件日志创建失败不影响其他handler

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
