# -*- coding: utf-8 -*-
"""统一配置管理模块

提供唯一的配置管理实现，支持：
- 单例模式（线程安全）
- 点号路径访问嵌套配置（支持列表索引）
- 深拷贝保护内部缓存
- 原子写入（先写临时文件再替换，防崩溃损坏）
- 读取加锁（保证一致性快照）
"""

import copy
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from core.log import get_logger

logger = get_logger()


class ConfigManager:
    """统一配置管理器（线程安全单例模式）"""

    _instance = None
    _class_lock = threading.Lock()
    _config_path: Path = Path(__file__).parent.parent / "config.json"
    _cache: Dict = None
    _loaded: bool = False
    _lock = threading.Lock()

    def __new__(cls):
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not self._loaded:
            self._load()

    def _load(self) -> None:
        """加载配置文件"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                logger.warning(f"配置文件不存在: {self._config_path}")
                self._cache = self._default_config()
                self._save()
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            self._cache = self._default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._cache = self._default_config()
        finally:
            self._loaded = True

    def _save_unsafe(self) -> bool:
        """内部保存方法（原子写入：先写临时文件再替换，调用方需持有锁）"""
        try:
            # 在同目录下写临时文件，确保同文件系统以支持原子 replace
            tmp_fd, tmp_path = tempfile.mkstemp(
                suffix='.tmp', dir=str(self._config_path.parent), prefix='config_'
            )
            try:
                with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, str(self._config_path))
            except Exception:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "providers": [],
            "custom_prompts": {},
            "current_prompt": "",
            "trash": {"providers": {}, "custom_prompts": {}},
            "user_preferences": {},
            "system_settings": {
                "debug_level": "ERROR",
                "flask_secret_key": "default-dev-secret-key-please-change-in-prod",
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            }
        }

    def get(self, key: str = None, default: Any = None) -> Any:
        """获取配置项（支持点号路径，含列表索引，线程安全读取）"""
        with self._lock:
            if not key:
                return copy.deepcopy(self._cache)

            keys = key.split('.')
            value = self._cache

            for k in keys:
                if isinstance(value, list):
                    try:
                        idx = int(k)
                        if 0 <= idx < len(value):
                            value = value[idx]
                        else:
                            return default
                    except (ValueError, IndexError):
                        return default
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return copy.deepcopy(value)

    def set(self, key: str, value: Any) -> bool:
        """设置配置项（支持点号路径，线程安全，原子写入）"""
        with self._lock:
            if not key:
                self._cache = value
                return self._save_unsafe()

            keys = key.split('.')
            config = self._cache

            for k in keys[:-1]:
                if isinstance(config, list):
                    try:
                        idx = int(k)
                        config = config[idx]
                    except (ValueError, IndexError):
                        logger.error(f"无效的列表索引: {k}")
                        return False
                elif isinstance(config, dict):
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                else:
                    logger.error(f"无法在非容器类型上设置路径: {k}")
                    return False

            last_key = keys[-1]
            if isinstance(config, list):
                try:
                    idx = int(last_key)
                    if 0 <= idx < len(config):
                        config[idx] = value
                    else:
                        logger.error(f"列表索引越界: {last_key}")
                        return False
                except ValueError:
                    logger.error(f"无效的列表索引: {last_key}")
                    return False
            elif isinstance(config, dict):
                config[last_key] = value
            else:
                logger.error(f"无法在非容器类型上设置键: {last_key}")
                return False

            return self._save_unsafe()

    def delete(self, key: str) -> bool:
        """删除配置项（支持点号路径）"""
        with self._lock:
            if not key:
                return False

            keys = key.split('.')
            config = self._cache

            for k in keys[:-1]:
                if isinstance(config, list):
                    try:
                        idx = int(k)
                        config = config[idx]
                    except (ValueError, IndexError):
                        return False
                elif isinstance(config, dict) and k in config:
                    config = config[k]
                else:
                    return False

            if isinstance(config, dict) and keys[-1] in config:
                del config[keys[-1]]
                return self._save_unsafe()

            return False

    def save(self) -> bool:
        """保存配置到文件"""
        with self._lock:
            return self._save_unsafe()

    @classmethod
    def reset(cls):
        """重置单例状态（主要用于测试）"""
        with cls._class_lock:
            cls._instance = None
            cls._cache = None
            cls._loaded = False
