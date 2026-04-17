# -*- coding: utf-8 -*-
"""任务服务 — 封装任务启动的业务逻辑"""

import os
import threading
from openai import OpenAI
from repositories.provider_repo import ProviderRepository
from repositories.prompt_repo import PromptRepository
from services.processing_service import ProcessingService
from services.state_service import ProcessingState
from core.config import ConfigManager
from core.errors import ProviderError, ValidationError
from core.log import get_logger

logger = get_logger()


class TaskService:
    """任务服务：验证参数、构造客户端、启动后台处理线程"""

    def __init__(self, config: ConfigManager = None):
        self._config = config or ConfigManager()
        self._state = ProcessingState()
        self._service = ProcessingService(self._state)

    def start(
        self,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
        directory: str,
        skip_existing: bool = False,
    ) -> dict:
        """启动处理任务

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        # 验证
        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
            return {"success": False, "error": "请提供有效的目录路径"}

        provider_repo = ProviderRepository(self._config)
        prompt_repo = PromptRepository(self._config)

        provider = provider_repo.get(provider_name)
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        if model_key not in provider.models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = provider.models[model_key]

        prompt = prompt_repo.get(prompt_name)
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        # 构造客户端并启动后台线程
        client = OpenAI(api_key=api_key, base_url=provider.base_url)
        thread = threading.Thread(
            target=self._service.run_batch,
            args=(directory, client, prompt.content, model_id, skip_existing),
            daemon=True,
        )
        thread.start()

        return {"success": True, "message": "处理已启动"}

    def get_status(self) -> dict:
        return self._state.get_dict()

    def cancel(self) -> dict:
        if not self._state.is_running() and not self._state.is_cancelled():
            return {"success": False, "error": "当前没有正在进行的处理任务"}
        self._state.set_cancelled()
        if self._state.is_running():
            self._state.cancel()
        return {"success": True, "message": "处理已取消"}
