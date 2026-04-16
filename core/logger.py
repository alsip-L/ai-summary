# -*- coding: utf-8 -*-
"""统一日志管理模块"""

import logging
import sys
from functools import lru_cache


def _get_log_level() -> int:
    """从配置文件读取日志级别"""
    try:
        from core.config_manager import ConfigManager
        level_str = ConfigManager().get('system_settings.debug_level', 'ERROR').upper()
    except Exception:
        level_str = 'ERROR'

    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level_str in valid_levels:
        return getattr(logging, level_str)
    return logging.ERROR


@lru_cache()
def get_logger(name: str = "ai_summary") -> logging.Logger:
    """获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 从配置文件读取日志级别
        logger.setLevel(_get_log_level())
        
        # 防止日志传播到父记录器
        logger.propagate = False
    
    return logger


def update_log_level(level_str: str) -> bool:
    """动态更新日志级别（热更新，无需重启）

    Args:
        level_str: 日志级别字符串 (DEBUG/INFO/WARNING/ERROR/CRITICAL)

    Returns:
        是否更新成功
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level_upper = level_str.upper()
    if level_upper not in valid_levels:
        return False

    logger = get_logger()
    logger.setLevel(getattr(logging, level_upper))
    return True


# 向后兼容的函数
def debug_print(level: str, message: str) -> None:
    """统一的调试输出函数（向后兼容）
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: 日志消息
    """
    logger = get_logger()
    
    # 直接使用 logger 的对应方法，避免重复编码处理
    level_upper = level.upper()
    if level_upper == 'DEBUG':
        logger.debug(message)
    elif level_upper == 'INFO':
        logger.info(message)
    elif level_upper == 'WARNING':
        logger.warning(message)
    elif level_upper == 'ERROR':
        logger.error(message)
    elif level_upper == 'CRITICAL':
        logger.critical(message)
    else:
        logger.info(message)
