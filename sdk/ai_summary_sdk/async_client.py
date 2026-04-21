# -*- coding: utf-8 -*-
"""AI Summary 异步 SDK 客户端"""
import httpx
from ._base import BaseClientConfig, BaseResourceGroup, _handle_response, _validate_response
from ._retry import retry_with_backoff
from . import models


class AsyncProvidersResource(BaseResourceGroup):
    """异步提供商 API 分组"""

    async def list(self) -> list[dict]:
        """列出所有活跃提供商"""
        resp = await self._client.get(self._url("/api/providers/"), headers=self._headers())
        return _handle_response(resp)

    async def create(self, name: str, base_url: str, api_key: str,
                     models_map: dict[str, str] | None = None, is_active: bool = True) -> dict:
        """创建提供商"""
        body = models.ProviderCreate(
            name=name, base_url=base_url, api_key=api_key,
            models=models_map or {}, is_active=is_active,
        ).model_dump()
        resp = await self._client.post(self._url("/api/providers/"), json=body, headers=self._headers())
        return _handle_response(resp)

    async def delete(self, name: str) -> dict:
        """删除提供商（移入回收站）"""
        resp = await self._client.delete(self._url(f"/api/providers/{name}"), headers=self._headers())
        return _handle_response(resp)

    async def update_api_key(self, name: str, api_key: str) -> dict:
        """更新 API Key"""
        body = models.ApiKeyUpdate(api_key=api_key).model_dump()
        resp = await self._client.put(self._url(f"/api/providers/{name}/api-key"), json=body, headers=self._headers())
        return _handle_response(resp)

    async def add_model(self, name: str, display_name: str, model_id: str) -> dict:
        """添加模型"""
        body = models.ModelCreate(display_name=display_name, model_id=model_id).model_dump()
        resp = await self._client.post(self._url(f"/api/providers/{name}/models"), json=body, headers=self._headers())
        return _handle_response(resp)

    async def delete_model(self, name: str, model_name: str) -> dict:
        """删除模型"""
        resp = await self._client.delete(self._url(f"/api/providers/{name}/models/{model_name}"), headers=self._headers())
        return _handle_response(resp)


class AsyncPromptsResource(BaseResourceGroup):
    """异步提示词 API 分组"""

    async def list(self) -> list[dict]:
        """列出所有提示词"""
        resp = await self._client.get(self._url("/api/prompts/"), headers=self._headers())
        return _handle_response(resp)

    async def create(self, name: str, content: str) -> dict:
        """创建提示词"""
        body = models.PromptCreate(name=name, content=content).model_dump()
        resp = await self._client.post(self._url("/api/prompts/"), json=body, headers=self._headers())
        return _handle_response(resp)

    async def delete(self, name: str) -> dict:
        """删除提示词（移入回收站）"""
        resp = await self._client.delete(self._url(f"/api/prompts/{name}"), headers=self._headers())
        return _handle_response(resp)


class AsyncTasksResource(BaseResourceGroup):
    """异步任务 API 分组"""

    async def start(self, provider: str, model: str, api_key: str,
                    prompt: str, directory: str, skip_existing: bool = False) -> dict:
        """启动处理任务"""
        body = models.TaskStartRequest(
            provider=provider, model=model, api_key=api_key,
            prompt=prompt, directory=directory, skip_existing=skip_existing,
        ).model_dump()
        resp = await self._client.post(self._url("/api/tasks/start"), json=body, headers=self._headers())
        return _handle_response(resp)

    async def status(self) -> dict:
        """获取当前任务状态"""
        resp = await self._client.get(self._url("/api/tasks/status"), headers=self._headers())
        return _handle_response(resp)

    async def cancel(self) -> dict:
        """取消当前任务"""
        resp = await self._client.post(self._url("/api/tasks/cancel"), headers=self._headers())
        return _handle_response(resp)

    async def get_failed(self) -> dict:
        """获取失败记录"""
        resp = await self._client.get(self._url("/api/tasks/failed"), headers=self._headers())
        return _handle_response(resp)

    async def clear_failed(self) -> dict:
        """清除失败记录"""
        resp = await self._client.delete(self._url("/api/tasks/failed"), headers=self._headers())
        return _handle_response(resp)

    async def retry_failed(self, provider: str, model: str, api_key: str, prompt: str) -> dict:
        """重试失败记录"""
        body = models.RetryFailedRequest(
            provider=provider, model=model, api_key=api_key, prompt=prompt,
        ).model_dump()
        resp = await self._client.post(self._url("/api/tasks/retry-failed"), json=body, headers=self._headers())
        return _handle_response(resp)


class AsyncFilesResource(BaseResourceGroup):
    """异步文件 API 分组"""

    async def drives(self) -> dict:
        """获取可用驱动器"""
        resp = await self._client.get(self._url("/api/files/drives"), headers=self._headers())
        return _handle_response(resp)

    async def directory(self, path: str = "") -> dict:
        """获取目录内容"""
        resp = await self._client.get(self._url("/api/files/directory"), params={"path": path}, headers=self._headers())
        return _handle_response(resp)

    async def result(self, path: str = "") -> dict:
        """查看处理结果"""
        resp = await self._client.get(self._url("/api/files/result"), params={"path": path}, headers=self._headers())
        return _handle_response(resp)


class AsyncTrashResource(BaseResourceGroup):
    """异步回收站 API 分组"""

    async def list(self) -> dict:
        """获取回收站内容"""
        resp = await self._client.get(self._url("/api/settings/trash/"), headers=self._headers())
        return _handle_response(resp)

    async def restore_provider(self, name: str) -> dict:
        """恢复提供商"""
        resp = await self._client.post(self._url(f"/api/settings/trash/restore/provider/{name}"), headers=self._headers())
        return _handle_response(resp)

    async def restore_prompt(self, name: str) -> dict:
        """恢复提示词"""
        resp = await self._client.post(self._url(f"/api/settings/trash/restore/prompt/{name}"), headers=self._headers())
        return _handle_response(resp)

    async def delete_provider(self, name: str) -> dict:
        """永久删除提供商"""
        resp = await self._client.delete(self._url(f"/api/settings/trash/provider/{name}"), headers=self._headers())
        return _handle_response(resp)

    async def delete_prompt(self, name: str) -> dict:
        """永久删除提示词"""
        resp = await self._client.delete(self._url(f"/api/settings/trash/prompt/{name}"), headers=self._headers())
        return _handle_response(resp)


class AsyncSettingsResource(BaseResourceGroup):
    """异步设置 API 分组"""

    async def get_preferences(self) -> dict:
        """获取用户偏好"""
        resp = await self._client.get(self._url("/api/settings/preferences"), headers=self._headers())
        return _handle_response(resp)

    async def update_preferences(self, **kwargs) -> dict:
        """更新用户偏好"""
        body = models.PreferencesUpdate(**kwargs).model_dump(exclude_none=True)
        resp = await self._client.put(self._url("/api/settings/preferences"), json=body, headers=self._headers())
        return _handle_response(resp)


class AsyncAISummaryClient:
    """AI Summary 异步 SDK 客户端

    示例:
        async with AsyncAISummaryClient(base_url="http://localhost:5000") as client:
            providers = await client.providers.list()
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self._config = BaseClientConfig(
            base_url=base_url, api_key=api_key,
            timeout=timeout, max_retries=max_retries, retry_delay=retry_delay,
        )
        self._client = httpx.AsyncClient(timeout=self._config.timeout)

        # 初始化 API 分组
        self.providers = AsyncProvidersResource(self._client, self._config)
        self.prompts = AsyncPromptsResource(self._client, self._config)
        self.tasks = AsyncTasksResource(self._client, self._config)
        self.files = AsyncFilesResource(self._client, self._config)
        self.trash = AsyncTrashResource(self._client, self._config)
        self.settings = AsyncSettingsResource(self._client, self._config)

    async def close(self) -> None:
        """关闭 HTTP 客户端，释放连接"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
