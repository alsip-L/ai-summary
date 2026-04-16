# -*- coding: utf-8 -*-
"""配置管理模块（向后兼容）

此模块已废弃，所有功能已统一到 core.config_manager
此处仅作为向后兼容保留
"""

from core.config_manager import Config, ConfigManager, load_config, save_config

__all__ = ['Config', 'ConfigManager', 'load_config', 'save_config']
