# -*- coding: utf-8 -*-
"""AI 处理模块"""

import time
from typing import Optional, Dict, Any
from openai import OpenAI
from core.logger import get_logger
from core.config_manager import ConfigManager
from core.exceptions import ProviderError

logger = get_logger()


class AIProcessor:
    """AI 处理器
    
    封装 AI 模型调用相关的操作。
    """
    
    def __init__(self, provider_name: str, api_key: str):
        """初始化 AI 处理器
        
        Args:
            provider_name: AI 提供商名称
            api_key: API 密钥
            
        Raises:
            ProviderError: 当提供商配置错误或 API 密钥无效时抛出
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self.config = ConfigManager()
        self.client = self._create_client()
        
        logger.info(f"AI 处理器初始化: {provider_name}")
    
    def _create_client(self) -> OpenAI:
        """创建 AI 客户端
        
        Returns:
            OpenAI 客户端实例
            
        Raises:
            ProviderError: 当提供商配置错误时抛出
        """
        providers = self.config.get('providers', [])
        provider = next(
            (p for p in providers if p.get('name') == self.provider_name),
            None
        )
        
        if not provider:
            raise ProviderError(f"提供商未找到: {self.provider_name}")
        
        base_url = provider.get('base_url')
        if not base_url:
            raise ProviderError(f"提供商 {self.provider_name} 未配置 base_url")
        
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
            logger.debug(f"AI 客户端创建成功: {self.provider_name}")
            return client
        except Exception as e:
            logger.error(f"创建 AI 客户端失败: {e}")
            raise ProviderError(f"创建 AI 客户端失败: {e}")
    
    def process(self, content: str, model_id: str, system_prompt: str) -> str:
        """处理内容
        
        调用 AI 模型处理文本内容。
        
        Args:
            content: 要处理的文本内容
            model_id: 模型 ID
            system_prompt: 系统提示词
            
        Returns:
            AI 生成的响应内容
            
        Raises:
            ProviderError: 当 AI 调用失败时抛出
        """
        start_time = time.time()
        
        try:
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': content}
                ],
                stream=False
            )
            
            response_content = completion.choices[0].message.content
            
            # 检查空响应
            if response_content is None:
                raise ProviderError("AI 返回空响应")
            
            duration = time.time() - start_time
            
            logger.info(f"AI 处理完成，耗时 {duration:.2f} 秒")
            return response_content
            
        except Exception as e:
            logger.error(f"AI 处理失败: {e}")
            raise ProviderError(f"AI 处理失败: {e}")
    
    def process_with_retry(
        self,
        content: str,
        model_id: str,
        system_prompt: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """带重试机制的处理
        
        当 AI 调用失败时自动重试。
        
        Args:
            content: 要处理的文本内容
            model_id: 模型 ID
            system_prompt: 系统提示词
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            AI 生成的响应内容
            
        Raises:
            ProviderError: 当所有重试都失败时抛出
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.process(content, model_id, system_prompt)
            except ProviderError as e:
                last_error = e
                logger.warning(f"AI 处理失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
        
        logger.error(f"AI 处理失败，已重试 {max_retries} 次")
        raise last_error
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """获取模型信息
        
        Args:
            model_key: 模型键名
            
        Returns:
            模型信息字典，如果未找到则返回 None
        """
        providers = self.config.get('providers', [])
        provider = next(
            (p for p in providers if p.get('name') == self.provider_name),
            None
        )
        
        if not provider:
            return None
        
        models = provider.get('models', {})
        model_id = models.get(model_key)
        
        if not model_id:
            return None
        
        return {
            'key': model_key,
            'id': model_id,
            'provider': self.provider_name
        }


# 向后兼容的函数
def process_file(file_path: str, client: OpenAI, system_prompt: str, model_id: str) -> str:
    """处理文件（向后兼容）
    
    注意：此函数需要传入已创建的 OpenAI 客户端
    """
    from pathlib import Path
    from processors.file_processor import FileProcessor
    
    file_path_obj = Path(file_path)
    processor = FileProcessor(str(file_path_obj.parent))
    content = processor.read_file(file_path_obj)
    
    start_time = time.time()
    
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': content}
            ],
            stream=False
        )
        
        response_content = completion.choices[0].message.content
        duration = time.time() - start_time
        
        logger.info(f"处理文件 {file_path_obj.name} 耗时 {duration:.2f} 秒")
        return response_content
        
    except Exception as e:
        logger.error(f"处理文件失败: {file_path}, {e}")
        raise ProviderError(f"处理文件失败: {e}")
