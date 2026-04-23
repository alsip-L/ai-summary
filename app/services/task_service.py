# -*- coding: utf-8 -*-
import os
import threading
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models import Provider, Prompt
from app.repositories.provider_repo import ProviderRepository
from core.utils import safe_json_loads
from app.repositories.prompt_repo import PromptRepository
from app.services.processing_state import ProcessingState
from app.services.task_runner import TaskRunner
from app.services.ai_client import AIClient
from app.services.file_processor import FileProcessor
from app.services.failed_record_service import FailedRecordService
from app.services.file_browser_service import FileBrowserService
from core.log import get_logger

logger = get_logger()


class TaskService:
    def __init__(self):
        self._state = ProcessingState()
        self._failed_record_svc = FailedRecordService()
        self._runner = TaskRunner(
            state=self._state,
            file_processor=FileProcessor(AIClient(self._state)),
            failed_record_service=self._failed_record_svc,
        )

    def _validate_and_create_client(
        self, db: Session, provider_name: str, model_key: str, api_key: str, prompt_name: str
    ) -> dict:
        """验证 Provider/Prompt 并返回连接参数

        Returns:
            成功: {"api_key": str, "base_url": str, "model_id": str, "prompt_content": str}
            失败: {"success": False, "error": str}
        """
        provider = db.query(Provider).filter(Provider.name == provider_name, Provider.is_active == True, Provider.is_deleted == False).first()
        if not provider:
            return {"success": False, "error": f"提供商 '{provider_name}' 未找到"}

        models = safe_json_loads(provider.models_json)
        if model_key not in models:
            return {"success": False, "error": f"模型 '{model_key}' 未找到"}
        model_id = models[model_key]

        prompt = db.query(Prompt).filter(Prompt.name == prompt_name, Prompt.is_deleted == False).first()
        if not prompt:
            return {"success": False, "error": f"Prompt '{prompt_name}' 未找到"}

        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        return {"api_key": api_key, "base_url": provider.base_url, "model_id": model_id, "prompt_content": prompt.content}

    def start(
        self,
        db: Session,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
        directory: str,
        skip_existing: bool = False,
    ) -> dict:
        if self._state.is_running():
            return {"success": False, "error": "已有任务正在运行"}

        if not api_key:
            return {"success": False, "error": "API Key 未配置"}

        validation = self._validate_and_create_client(db, provider_name, model_key, api_key, prompt_name)
        if not validation.get("api_key"):
            return validation

        if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
            return {"success": False, "error": "请提供有效的目录路径"}

        file_browser = FileBrowserService()
        if not file_browser._validate_path(directory):
            return {"success": False, "error": "目录不在允许的访问范围内"}

        model_id = validation["model_id"]
        prompt_content = validation["prompt_content"]
        # 在后台线程中创建独立的 OpenAI 客户端，避免跨线程共享
        client_api_key = validation["api_key"]
        client_base_url = validation["base_url"]

        logger.info(f"启动处理任务: provider={provider_name}, model={model_id}, directory={directory}")

        self._state.start()

        def _run_in_thread():
            client = OpenAI(api_key=client_api_key, base_url=client_base_url)
            try:
                self._runner.run_batch(directory, client, prompt_content, model_id, skip_existing)
            except Exception as e:
                logger.error(f"后台任务异常: {e}")
                self._state.set_error(f"后台任务异常: {str(e)}")
                self._failed_record_svc.persist_from_state()
            finally:
                client.close()

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        return {"success": True, "message": "处理已启动"}

    def get_status(self) -> dict:
        return self._state.get_dict()

    def cancel(self) -> dict:
        if self._state.request_cancel():
            return {"success": True, "message": "处理已取消"}
        return {"success": False, "error": "当前没有正在进行的处理任务"}

    def retry_failed(
        self,
        db: Session,
        provider_name: str,
        model_key: str,
        api_key: str,
        prompt_name: str,
    ) -> dict:
        """仅重跑之前失败的文件"""
        if self._state.is_running():
            return {"success": False, "error": "已有任务正在运行"}

        # 从数据库读取失败记录
        try:
            failed_records, failed_sources = self._failed_record_svc.get_sources_for_retry()
        except Exception as e:
            return {"success": False, "error": f"读取失败记录出错: {e}"}

        if not failed_records:
            return {"success": False, "error": "没有失败记录可重跑"}

        # 验证文件仍然存在
        existing_sources = [s for s in failed_sources if os.path.exists(s)]
        if not existing_sources:
            return {"success": False, "error": "失败记录中的文件已不存在，请清除失败记录"}

        # 验证 provider/prompt
        validation = self._validate_and_create_client(db, provider_name, model_key, api_key, prompt_name)
        if not validation.get("api_key"):
            return validation

        model_id = validation["model_id"]
        prompt_content = validation["prompt_content"]
        client_api_key = validation["api_key"]
        client_base_url = validation["base_url"]

        logger.info(f"启动失败重跑: {len(existing_sources)} 个文件")

        self._state.start()

        def _run_in_thread():
            client = OpenAI(api_key=client_api_key, base_url=client_base_url)
            try:
                self._runner.run_retry_batch(existing_sources, client, prompt_content, model_id)
            except Exception as e:
                logger.error(f"后台重跑任务异常: {e}")
                self._state.set_error(f"后台重跑任务异常: {str(e)}")
                self._failed_record_svc.persist_from_state()
            finally:
                client.close()

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        return {"success": True, "message": f"重跑已启动，共 {len(existing_sources)} 个文件"}
