# -*- coding: utf-8 -*-
"""统一配置管理模块

提供唯一的配置管理实现，支持：
- 单例模式
- 点号路径访问嵌套配置
- 配置热加载
- 向后兼容
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from core.logger import get_logger

logger = get_logger()


class ConfigManager:
    """统一配置管理器（单例模式）

    职责：统一管理配置文件的读写，提供统一的配置访问接口

    使用示例：
        config = ConfigManager()

        # 读取配置
        providers = config.get('providers', [])

        # 写入配置
        config.set('providers', new_providers)

        # 支持点号路径
        api_key = config.get('providers.0.api_key')

        # 保存配置
        config.save()
    """

    _instance = None
    _config_path: Path = Path("config.json")
    _cache: Dict = None
    _loaded: bool = False

    def __new__(cls):
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
                logger.info("配置文件加载成功")
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

    def _save(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.debug("配置文件保存成功")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "providers": [],
            "current_provider": {},
            "custom_prompts": {},
            "current_prompt": "",
            "file_paths": {
                "input": "",
                "output": ""
            },
            "trash": {
                "providers": {},
                "custom_prompts": {}
            },
            "user_preferences": {}
        }

    def get(self, key: str = None, default: Any = None) -> Any:
        """获取配置项（支持点号路径）

        Args:
            key: 配置键，支持点号路径如 'providers.0.name'
                 如果为 None 或空字符串，返回完整配置
            default: 默认值

        Returns:
            配置值，如果不存在返回默认值
        """
        if not key:
            return self._cache.copy()

        keys = key.split('.')
        value = self._cache

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """设置配置项（支持点号路径）

        Args:
            key: 配置键，支持点号路径
            value: 配置值

        Returns:
            是否保存成功
        """
        if not key:
            self._cache = value
            return self._save()

        keys = key.split('.')
        config = self._cache

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        return self._save()

    def update(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置

        Args:
            updates: 要更新的配置字典

        Returns:
            是否保存成功
        """
        for key, value in updates.items():
            self.set(key, value)
        return True

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._cache.copy()

    def reload(self) -> None:
        """重新加载配置"""
        self._load()
        logger.info("配置文件已重新加载")

    def save(self) -> bool:
        """保存配置到文件"""
        return self._save()

    def delete(self, key: str) -> bool:
        """删除配置项（支持点号路径）

        Args:
            key: 配置键，支持点号路径

        Returns:
            是否删除成功
        """
        if not key:
            return False

        keys = key.split('.')
        config = self._cache

        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False

        if isinstance(config, dict) and keys[-1] in config:
            del config[keys[-1]]
            return self._save()

        return False

    def setdefault(self, key: str, default: Any = None) -> Any:
        """如果键不存在则设置默认值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        config = self._cache

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        last_key = keys[-1]
        if last_key not in config:
            config[last_key] = default
            self._save()

        return config.get(last_key, default)


class Config:
    """配置管理类（向后兼容）

    兼容原有的 Config 类用法，内部委托给 ConfigManager
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._manager = ConfigManager()
        return cls._instance

    def __init__(self):
        self._manager = ConfigManager()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._manager.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._manager.set(key, value)

    def save(self) -> bool:
        """保存配置"""
        return self._manager.save()

    def reload(self) -> None:
        """重新加载"""
        self._manager.reload()

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._manager.get_all()

    def delete(self, key: str) -> bool:
        """删除配置项"""
        return self._manager.delete(key)


def load_config():
    """加载配置文件（向后兼容）"""
    return ConfigManager().get_all()


def save_config(config):
    """保存配置文件（向后兼容）"""
    manager = ConfigManager()
    manager._cache = config
    return manager.save()
