# -*- coding: utf-8 -*-
"""统一日志管理模块"""

import logging
import sys
from functools import lru_cache


def _get_log_level() -> int:
    """从配置文件读取日志级别"""
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
def get_logger(name: str = "ai_summary") -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
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
