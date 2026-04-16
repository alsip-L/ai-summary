# utils.py - 优化版本的工具函数
import os
import json
import threading
import time
import traceback
from openai import OpenAI
from core.config_manager import ConfigManager
from core.logger import get_logger
from core.exceptions import FileProcessingError, ProviderError

logger = get_logger()

DEBUG_LEVEL = os.environ.get('DEBUG_LEVEL', 'ERROR').upper()


def debug_print(level, message):
    """统一的调试输出函数，委托给 core.logger"""
    level_map = {
        'DEBUG': logger.debug,
        'INFO': logger.info,
        'WARNING': logger.warning,
        'ERROR': logger.error,
        'CRITICAL': logger.critical
    }
    log_func = level_map.get(level.upper(), logger.info)
    log_func(message)


class ConfigManagerWrapper:
    """配置管理包装类（向后兼容 utils.py 中的 ConfigManager）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._manager = ConfigManager()
        return cls._instance

    @staticmethod
    def load():
        """加载配置文件"""
        return ConfigManager().get_all()

    @staticmethod
    def save(config):
        """保存配置文件"""
        from core.config_manager import save_config as _save_config
        return _save_config(config)


class PromptManager:
    """提示词管理类"""

    _manager = None

    @classmethod
    def _get_manager(cls):
        if cls._manager is None:
            cls._manager = ConfigManager()
        return cls._manager

    @staticmethod
    def load():
        """加载所有提示词"""
        config = ConfigManager().get_all()
        prompts = config.get('custom_prompts', {})

        processed_prompts = {}
        for name, content in prompts.items():
            if isinstance(content, list):
                processed_prompts[name] = '\n'.join(content)
            else:
                processed_prompts[name] = content

        return processed_prompts

    @staticmethod
    def save(prompts):
        """保存自定义提示词"""
        try:
            manager = ConfigManager()
            manager.set('custom_prompts', prompts)
            return True
        except Exception as e:
            debug_print('ERROR', f"保存自定义提示词失败: {e}")
            return False

    @staticmethod
    def move_to_trash(name):
        """移动提示词到回收站"""
        try:
            manager = ConfigManager()
            prompts = manager.get('custom_prompts', {})

            if name in prompts:
                trash = manager.get('trash', {})
                if 'custom_prompts' not in trash:
                    trash['custom_prompts'] = {}
                trash['custom_prompts'][name] = prompts[name]
                del prompts[name]
                manager.set('trash', trash)
                manager.set('custom_prompts', prompts)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"移动提示词到回收站失败: {e}")
            return False

    @staticmethod
    def restore_from_trash(name):
        """从回收站恢复提示词"""
        try:
            manager = ConfigManager()
            trash = manager.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})

            if name in trash_prompts:
                prompts = manager.get('custom_prompts', {})
                prompts[name] = trash_prompts[name]
                del trash_prompts[name]
                manager.set('custom_prompts', prompts)
                manager.set('trash', trash)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站恢复提示词失败: {e}")
            return False

    @staticmethod
    def permanent_delete_from_trash(name):
        """从回收站永久删除提示词"""
        try:
            manager = ConfigManager()
            trash = manager.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})

            if name in trash_prompts:
                del trash_prompts[name]
                manager.set('trash', trash)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站永久删除提示词失败: {e}")
            return False


class ProviderManager:
    """AI提供商管理类"""

    @staticmethod
    def load():
        """加载所有AI提供商"""
        config = ConfigManager().get_all()
        providers_list = config.get('providers', [])

        providers_dict = {}
        for provider in providers_list:
            if 'name' in provider:
                providers_dict[provider['name']] = provider

        return providers_dict

    @staticmethod
    def save(name, base_url, api_key="", models=None):
        """保存AI提供商"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            providers_list = config.get('providers', [])

            existing_index = -1
            for i, provider in enumerate(providers_list):
                if provider.get('name') == name:
                    existing_index = i
                    break

            new_provider = {
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "models": models or {}
            }

            if existing_index >= 0:
                providers_list[existing_index] = new_provider
            else:
                providers_list.append(new_provider)

            manager.set('providers', providers_list)
            return True
        except Exception as e:
            debug_print('ERROR', f"保存AI提供商失败: {e}")
            return False

    @staticmethod
    def get_api_key(provider_name):
        """获取提供商的API密钥"""
        providers = ProviderManager.load()
        provider = providers.get(provider_name, {})
        api_key = provider.get('api_key', '')
        if not api_key:
            debug_print('WARNING', f"提供商 '{provider_name}' 的API密钥未配置")
        return api_key

    @staticmethod
    def save_api_key(provider_name, api_key):
        """保存提供商的API密钥"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            providers_list = config.get('providers', [])

            found = False
            for provider in providers_list:
                if provider.get('name') == provider_name:
                    provider['api_key'] = api_key
                    found = True
                    break

            if not found:
                debug_print('WARNING', f"提供商 '{provider_name}' 未找到，无法保存API密钥")
                return False

            manager.set('providers', providers_list)
            return True
        except Exception as e:
            debug_print('ERROR', f"保存提供商API密钥失败: {e}")
            return False

    @staticmethod
    def move_to_trash(name):
        """移动提供商到回收站"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            providers_list = config.get('providers', [])

            provider_to_move = None
            for i, provider in enumerate(providers_list):
                if provider.get('name') == name:
                    provider_to_move = provider
                    providers_list.pop(i)
                    break

            if provider_to_move:
                trash = config.get('trash', {})
                if 'providers' not in trash:
                    trash['providers'] = {}
                trash['providers'][name] = provider_to_move
                manager.set('providers', providers_list)
                manager.set('trash', trash)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"移动提供商到回收站失败: {e}")
            return False

    @staticmethod
    def restore_from_trash(name):
        """从回收站恢复提供商"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            trash = config.get('trash', {})
            trash_providers = trash.get('providers', {})

            if name in trash_providers:
                providers_list = config.get('providers', [])
                providers_list.append(trash_providers[name])
                del trash_providers[name]
                manager.set('providers', providers_list)
                manager.set('trash', trash)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站恢复提供商失败: {e}")
            return False

    @staticmethod
    def permanent_delete_from_trash(name):
        """从回收站永久删除提供商"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            trash = config.get('trash', {})
            trash_providers = trash.get('providers', {})

            if name in trash_providers:
                del trash_providers[name]
                manager.set('trash', trash)
                return True
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站永久删除提供商失败: {e}")
            return False

    @staticmethod
    def delete_model(provider_name, model_name):
        """从提供商中删除模型"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            providers_list = config.get('providers', [])

            for provider in providers_list:
                if provider.get('name') == provider_name and 'models' in provider:
                    if model_name in provider['models']:
                        del provider['models'][model_name]
                        manager.set('providers', providers_list)
                        return True
            return False
        except Exception as e:
            debug_print('ERROR', f"从提供商删除模型失败: {e}")
            return False

    @staticmethod
    def add_model(provider_name, model_display_name, model_id):
        """向提供商添加模型"""
        try:
            manager = ConfigManager()
            config = manager.get_all()
            providers_list = config.get('providers', [])

            for provider in providers_list:
                if provider.get('name') == provider_name:
                    if 'models' not in provider:
                        provider['models'] = {}
                    provider['models'][model_display_name] = model_id
                    manager.set('providers', providers_list)
                    return True
            return False
        except Exception as e:
            debug_print('ERROR', f"向提供商添加模型失败: {e}")
            return False


class UserPreferencesManager:
    """用户偏好管理类"""

    @staticmethod
    def save(preferences):
        """保存用户偏好"""
        try:
            manager = ConfigManager()
            current = manager.get('user_preferences', {})
            current.update(preferences)
            manager.set('user_preferences', current)
            return True
        except Exception as e:
            debug_print('ERROR', f"保存用户偏好失败: {e}")
            return False

    @staticmethod
    def load():
        """加载用户偏好"""
        try:
            return ConfigManager().get('user_preferences', {})
        except Exception as e:
            debug_print('ERROR', f"加载用户偏好失败: {e}")
            return {}


class FileManager:
    """文件管理类"""

    @staticmethod
    def scan_txt_files(directory):
        """扫描目录中的txt文件"""
        try:
            if not os.path.isdir(directory):
                raise ValueError(f"目录不存在: {directory}")

            txt_files = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.txt'):
                        txt_files.append(os.path.join(root, file))

            debug_print('INFO', f"扫描目录 {directory}，找到 {len(txt_files)} 个txt文件")
            return txt_files
        except Exception as e:
            debug_print('ERROR', f"扫描txt文件失败: {e}")
            return []

    @staticmethod
    def process_file(file_path, client, system_prompt, model_id):
        """处理单个文件

        Raises:
            FileProcessingError: 当文件读取失败时
            ProviderError: 当AI调用失败时
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception as e:
                raise FileProcessingError(f"读取文件失败: {os.path.basename(file_path)}, {e}")
        except Exception as e:
            raise FileProcessingError(f"读取文件失败: {os.path.basename(file_path)}, {e}")

        ai_call_start_time = time.time()
        debug_print('INFO', f"开始处理文件: {os.path.basename(file_path)}, 模型: {model_id}")

        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': content}
                ],
                stream=False
            )

            if completion is None or completion.choices is None or len(completion.choices) == 0:
                raise ProviderError("API返回空响应")

            response_content = completion.choices[0].message.content
            ai_call_duration = time.time() - ai_call_start_time

            debug_print('INFO', f"处理文件 {os.path.basename(file_path)} 耗时 {ai_call_duration:.2f}秒")
            return response_content
        except (FileProcessingError, ProviderError):
            raise
        except Exception as e:
            error_msg = f"处理文件 '{os.path.basename(file_path)}' 时出错: {str(e).splitlines()[0]}"
            debug_print('ERROR', error_msg)
            raise ProviderError(error_msg)

    @staticmethod
    def save_response(file_path, response):
        """保存响应为md文件

        Raises:
            FileProcessingError: 当保存失败时
        """
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        md_filename = filename.replace('.txt', '.md')
        md_path = os.path.join(directory, md_filename)

        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(response)

            debug_print('INFO', f"保存响应到 {md_path}")
            return md_path
        except Exception as e:
            error_msg = f"保存结果到 {md_path} 时出错: {str(e)}"
            debug_print('ERROR', error_msg)
            raise FileProcessingError(error_msg)


def load_config():
    """加载配置文件（向后兼容）"""
    return ConfigManager().get_all()


def save_config(config):
    """保存配置文件（向后兼容）"""
    from core.config_manager import save_config as _save_config
    return _save_config(config)


def load_custom_prompts():
    """加载自定义提示词（向后兼容）"""
    return PromptManager.load()


def save_custom_prompts(prompts):
    """保存自定义提示词（向后兼容）"""
    return PromptManager.save(prompts)


def save_provider(name, base_url, api_key="", models=None):
    """保存AI提供商（向后兼容）"""
    return ProviderManager.save(name, base_url, api_key, models)


def load_providers():
    """加载AI提供商（向后兼容）"""
    return ProviderManager.load()


def get_provider_api_key(provider_name):
    """获取提供商API密钥（向后兼容）"""
    return ProviderManager.get_api_key(provider_name)


def save_provider_api_key(provider_name, api_key):
    """保存提供商API密钥（向后兼容）"""
    return ProviderManager.save_api_key(provider_name, api_key)


def move_prompt_to_trash(name):
    """移动提示词到回收站（向后兼容）"""
    return PromptManager.move_to_trash(name)


def restore_prompt_from_trash(name):
    """从回收站恢复提示词（向后兼容）"""
    return PromptManager.restore_from_trash(name)


def permanent_delete_prompt_from_trash(name):
    """从回收站永久删除提示词（向后兼容）"""
    return PromptManager.permanent_delete_from_trash(name)


def move_provider_to_trash(name):
    """移动提供商到回收站（向后兼容）"""
    return ProviderManager.move_to_trash(name)


def restore_provider_from_trash(name):
    """从回收站恢复提供商（向后兼容）"""
    return ProviderManager.restore_from_trash(name)


def permanent_delete_provider_from_trash(name):
    """从回收站永久删除提供商（向后兼容）"""
    return ProviderManager.permanent_delete_from_trash(name)


def delete_model_from_provider(provider_name, model_name):
    """从提供商删除模型（向后兼容）"""
    return ProviderManager.delete_model(provider_name, model_name)


def add_model_to_provider(provider_name, model_display_name, model_id):
    """向提供商添加模型（向后兼容）"""
    return ProviderManager.add_model(provider_name, model_display_name, model_id)


def scan_txt_files(directory):
    """扫描txt文件（向后兼容）"""
    return FileManager.scan_txt_files(directory)


def process_file(file_path, client, system_prompt, model_id):
    """处理文件（向后兼容）"""
    return FileManager.process_file(file_path, client, system_prompt, model_id)


def save_response(file_path, response):
    """保存响应（向后兼容）"""
    return FileManager.save_response(file_path, response)


def save_user_preferences(preferences):
    """保存用户偏好（向后兼容）"""
    return UserPreferencesManager.save(preferences)


def load_user_preferences():
    """加载用户偏好（向后兼容）"""
    return UserPreferencesManager.load()


def delete_custom_prompt(prompt_name):
    """直接删除自定义提示词（向后兼容）"""
    try:
        manager = ConfigManager()
        prompts = manager.get('custom_prompts', {})
        if prompt_name in prompts:
            del prompts[prompt_name]
            manager.set('custom_prompts', prompts)
            return True
        return False
    except Exception as e:
        debug_print('ERROR', f"删除自定义提示词失败: {e}")
        return False


def get_trash_items():
    """获取回收站项目（向后兼容）"""
    try:
        return ConfigManager().get('trash', {})
    except Exception as e:
        debug_print('ERROR', f"获取回收站项目失败: {e}")
        return {}
