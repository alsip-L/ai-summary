# -*- coding: utf-8 -*-
"""Managers module for AI Summary application."""

from .model_manager import ModelManager, ModelConfig
from .prompt_manager import PromptManager
from .file_manager import FilePathManager, PathConfig
from .trash_manager import TrashManager

__all__ = ['ModelManager', 'ModelConfig', 'PromptManager', 'FilePathManager', 'PathConfig', 'TrashManager']
