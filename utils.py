# utils.py - 优化版本的工具函数
import os
import json
import threading
import time
import traceback
from openai import OpenAI

# 生产环境调试级别控制
DEBUG_LEVEL = os.environ.get('DEBUG_LEVEL', 'ERROR').upper()

def debug_print(level, message):
    """统一的调试输出函数"""
    if DEBUG_LEVEL in ['DEBUG', 'ALL'] or (DEBUG_LEVEL == 'ERROR' and level == 'ERROR'):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"[{timestamp}] {level}: {message}", flush=True)

def safe_load_json(file_path, default=None):
    """安全的JSON加载函数"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default or {}
    except FileNotFoundError:
        debug_print('WARNING', f"配置文件 {file_path} 未找到")
        return default or {}
    except json.JSONDecodeError as e:
        debug_print('ERROR', f"JSON解析错误 {file_path}: {e}")
        return default or {}
    except Exception as e:
        debug_print('ERROR', f"加载配置文件失败 {file_path}: {e}")
        return default or {}

def safe_save_json(data, file_path):
    """安全的JSON保存函数"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        debug_print('ERROR', f"保存配置文件失败 {file_path}: {e}")
        return False

class ConfigManager:
    """配置管理类"""
    
    @staticmethod
    def load():
        """加载配置文件"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                debug_print('INFO', "配置文件加载成功")
                return config_data
            else:
                debug_print('ERROR', "配置文件 config.json 不存在")
                raise FileNotFoundError("config.json not found. Please create and configure it manually.")
        except Exception as e:
            debug_print('ERROR', f"加载配置文件失败: {e}")
            raise
    
    @staticmethod
    def save(config):
        """保存配置文件"""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            debug_print('INFO', "配置文件保存成功")
            return True
        except Exception as e:
            debug_print('ERROR', f"保存配置文件失败: {e}")
            return False

class PromptManager:
    """提示词管理类"""
    
    @staticmethod
    def load():
        """加载所有提示词"""
        config = ConfigManager.load()
        prompts = config.get('custom_prompts', {})
        
        # 处理长文本格式兼容性
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
            config = ConfigManager.load()
            config['custom_prompts'] = prompts
            return ConfigManager.save(config)
        except Exception as e:
            debug_print('ERROR', f"保存自定义提示词失败: {e}")
            return False
    
    @staticmethod
    def move_to_trash(name):
        """移动提示词到回收站"""
        try:
            config = ConfigManager.load()
            prompts = config.get('custom_prompts', {})
            
            if name in prompts:
                # 初始化回收站结构
                if 'trash' not in config:
                    config['trash'] = {}
                if 'custom_prompts' not in config['trash']:
                    config['trash']['custom_prompts'] = {}
                
                # 移动到回收站
                config['trash']['custom_prompts'][name] = prompts[name]
                del prompts[name]
                
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"移动提示词到回收站失败: {e}")
            return False
    
    @staticmethod
    def restore_from_trash(name):
        """从回收站恢复提示词"""
        try:
            config = ConfigManager.load()
            trash = config.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})
            
            if name in trash_prompts:
                # 恢复提示词
                config.setdefault('custom_prompts', {})[name] = trash_prompts[name]
                
                # 从回收站删除
                del trash_prompts[name]
                
                # 清理空的回收站结构
                if not trash_prompts:
                    del trash['custom_prompts']
                    if not trash:
                        del config['trash']
                
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站恢复提示词失败: {e}")
            return False
    
    @staticmethod
    def permanent_delete_from_trash(name):
        """从回收站永久删除提示词"""
        try:
            config = ConfigManager.load()
            trash = config.get('trash', {})
            trash_prompts = trash.get('custom_prompts', {})
            
            if name in trash_prompts:
                # 永久删除
                del trash_prompts[name]
                
                # 清理空的回收站结构
                if not trash_prompts:
                    del trash['custom_prompts']
                    if not trash:
                        del config['trash']
                
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站永久删除提示词失败: {e}")
            return False

class ProviderManager:
    """AI提供商管理类"""
    
    @staticmethod
    def load():
        """加载所有AI提供商"""
        config = ConfigManager.load()
        providers_list = config.get('providers', [])
        
        # 转换为字典格式
        providers_dict = {}
        for provider in providers_list:
            if 'name' in provider:
                providers_dict[provider['name']] = provider
        
        return providers_dict
    
    @staticmethod
    def save(name, base_url, api_key="", models=None):
        """保存AI提供商"""
        try:
            config = ConfigManager.load()
            config.setdefault('providers', [])
            
            # 检查是否存在该提供商
            existing_index = -1
            for i, provider in enumerate(config['providers']):
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
                config['providers'][existing_index] = new_provider
            else:
                config['providers'].append(new_provider)
            
            return ConfigManager.save(config)
        except Exception as e:
            debug_print('ERROR', f"保存AI提供商失败: {e}")
            return False
    
    @staticmethod
    def get_api_key(provider_name):
        """获取提供商的API密钥"""
        config = ConfigManager.load()
        providers_list = config.get('providers', [])
        
        for provider in providers_list:
            if provider.get('name') == provider_name:
                api_key = provider.get('api_key', '')
                if not api_key:
                    debug_print('WARNING', f"提供商 '{provider_name}' 的API密钥未配置")
                return api_key
        
        debug_print('WARNING', f"提供商 '{provider_name}' 未找到")
        return ''
    
    @staticmethod
    def save_api_key(provider_name, api_key):
        """保存提供商的API密钥"""
        try:
            config = ConfigManager.load()
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
            
            return ConfigManager.save(config)
        except Exception as e:
            debug_print('ERROR', f"保存提供商API密钥失败: {e}")
            return False
    
    @staticmethod
    def move_to_trash(name):
        """移动提供商到回收站"""
        try:
            config = ConfigManager.load()
            providers_list = config.get('providers', [])
            
            # 找到并移除提供商
            provider_to_move = None
            for i, provider in enumerate(providers_list):
                if provider.get('name') == name:
                    provider_to_move = provider
                    providers_list.pop(i)
                    break
            
            if provider_to_move:
                # 保存到回收站
                config.setdefault('trash', {}).setdefault('providers', {})[name] = provider_to_move
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"移动提供商到回收站失败: {e}")
            return False
    
    @staticmethod
    def restore_from_trash(name):
        """从回收站恢复提供商"""
        try:
            config = ConfigManager.load()
            trash = config.get('trash', {})
            trash_providers = trash.get('providers', {})
            
            if name in trash_providers:
                # 恢复提供商
                config.setdefault('providers', []).append(trash_providers[name])
                
                # 从回收站删除
                del trash_providers[name]
                
                # 清理空的回收站结构
                if not trash_providers:
                    del trash['providers']
                    if not trash:
                        del config['trash']
                
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站恢复提供商失败: {e}")
            return False
    
    @staticmethod
    def permanent_delete_from_trash(name):
        """从回收站永久删除提供商"""
        try:
            config = ConfigManager.load()
            trash = config.get('trash', {})
            trash_providers = trash.get('providers', {})
            
            if name in trash_providers:
                # 永久删除
                del trash_providers[name]
                
                # 清理空的回收站结构
                if not trash_providers:
                    del trash['providers']
                    if not trash:
                        del config['trash']
                
                return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"从回收站永久删除提供商失败: {e}")
            return False
    
    @staticmethod
    def delete_model(provider_name, model_name):
        """从提供商中删除模型"""
        try:
            config = ConfigManager.load()
            providers_list = config.get('providers', [])
            
            for provider in providers_list:
                if provider.get('name') == provider_name and 'models' in provider:
                    if model_name in provider['models']:
                        del provider['models'][model_name]
                        return ConfigManager.save(config)
            return False
        except Exception as e:
            debug_print('ERROR', f"从提供商删除模型失败: {e}")
            return False

class UserPreferencesManager:
    """用户偏好管理类"""
    
    @staticmethod
    def save(preferences):
        """保存用户偏好"""
        try:
            config = ConfigManager.load()
            config.setdefault('user_preferences', {}).update(preferences)
            return ConfigManager.save(config)
        except Exception as e:
            debug_print('ERROR', f"保存用户偏好失败: {e}")
            return False
    
    @staticmethod
    def load():
        """加载用户偏好"""
        try:
            config = ConfigManager.load()
            return config.get('user_preferences', {})
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
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ai_call_start_time = time.time()
            
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': content}
                ],
                stream=False
            )
            
            response_content = completion.choices[0].message.content
            ai_call_duration = time.time() - ai_call_start_time
            
            debug_file = os.path.basename(file_path)
            debug_print('INFO', f"处理文件 {debug_file} 耗时 {ai_call_duration:.2f}秒")
            return response_content
        except Exception as e:
            error_msg = f"处理文件 '{os.path.basename(file_path)}' 时出错: {str(e).splitlines()[0]}"
            debug_print('ERROR', error_msg)
            return error_msg
    
    @staticmethod
    def save_response(file_path, response):
        """保存响应为md文件"""
        try:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            md_filename = filename.replace('.txt', '.md')
            md_path = os.path.join(directory, md_filename)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(response)
            
            debug_print('INFO', f"保存响应到 {md_path}")
            return md_path
        except Exception as e:
            error_msg = f"保存结果到 {md_path} 时出错: {str(e)}"
            debug_print('ERROR', error_msg)
            return error_msg

# 向后兼容的函数别名
def load_config():
    """加载配置文件（向后兼容）"""
    return ConfigManager.load()

def save_config(config):
    """保存配置文件（向后兼容）"""
    return ConfigManager.save(config)

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
        config = ConfigManager.load()
        if 'custom_prompts' in config and prompt_name in config['custom_prompts']:
            del config['custom_prompts'][prompt_name]
            return ConfigManager.save(config)
        return False
    except Exception as e:
        debug_print('ERROR', f"删除自定义提示词失败: {e}")
        return False

def get_trash_items():
    """获取回收站项目（向后兼容）"""
    try:
        config = ConfigManager.load()
        return config.get('trash', {})
    except Exception as e:
        debug_print('ERROR', f"获取回收站项目失败: {e}")
        return {}