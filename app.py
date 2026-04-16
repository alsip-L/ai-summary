# -*- coding: utf-8 -*-
import sys
import codecs

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    # Windows控制台编码设置
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except Exception:
        pass

# 重定向输出到UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        pass
# app.py - 优化版本
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
import time
import traceback
import threading
from openai import OpenAI
import urllib.parse
from utils import (
    load_config, load_custom_prompts,
    scan_txt_files, process_file, save_response, load_providers,
    get_provider_api_key, save_config, save_custom_prompts, save_provider, save_provider_api_key,
    delete_custom_prompt, delete_model_from_provider, add_model_to_provider,
    move_provider_to_trash, move_prompt_to_trash, restore_provider_from_trash,
    restore_prompt_from_trash, permanent_delete_provider_from_trash,
    permanent_delete_prompt_from_trash, get_trash_items, save_user_preferences, load_user_preferences
)
from services.state_service import ProcessingState

# 使用 core/logger.py 统一日志管理
from core.logger import get_logger
logger = get_logger()

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

def safe_url_decode(value):
    """安全的URL解码，支持多种编码"""
    if value is None:
        return None
    
    # 尝试多种解码方式
    for encoding in ['utf-8', 'gbk', 'gb2312']:
        try:
            return urllib.parse.unquote(value, encoding=encoding, errors='strict')
        except (UnicodeDecodeError, ValueError):
            continue
    
    # 如果所有编码都失败，使用replace错误处理
    debug_print('WARNING', f"URL decode failed for '{value}', using original value")
    return value

def safe_url_decode_form(form_data, fields):
    """批量安全URL解码表单数据"""
    decoded_data = {}
    for field in fields:
        decoded_data[field] = safe_url_decode(form_data.get(field, ''))
    return decoded_data

def set_session_message(session, message_type, message):
    """统一的session消息设置"""
    session[f'last_{message_type}'] = message

# 业务逻辑函数
class ProviderManager:
    """AI提供商管理类"""
    
    @staticmethod
    def get_all_providers():
        """获取所有提供商"""
        return load_providers()
    
    @staticmethod
    def get_default_provider(all_providers):
        """获取默认提供商"""
        if all_providers:
            return list(all_providers.keys())[0]
        return ''
    
    @staticmethod
    def get_provider_models(provider_name, all_providers):
        """获取提供商的模型列表"""
        provider = all_providers.get(provider_name, {})
        return provider.get('models', {})

class PromptManager:
    """Prompt管理类"""
    
    @staticmethod
    def get_all_prompts():
        """获取所有提示词"""
        return load_custom_prompts()
    
    @staticmethod
    def get_default_prompt(all_prompts):
        """获取默认提示词"""
        if all_prompts:
            return list(all_prompts.keys())[0]
        return ''

class SelectionManager:
    """选择管理类"""

    @staticmethod
    def get_selection_from_sources(session, user_preferences, all_providers, all_prompts, default_provider, default_model, default_prompt):
        """从多个来源获取选择（优先级：session > 用户偏好 > 默认值）

        如果选择的项目已不存在（如被删除到回收站），会自动回退到默认值
        """
        provider_names = list(all_providers.keys()) if all_providers else []
        prompt_names = list(all_prompts.keys()) if all_prompts else []

        selected_provider = session.get('selected_provider') or user_preferences.get('selected_provider')
        if selected_provider and selected_provider not in provider_names:
            selected_provider = default_provider

        selected_model = session.get('selected_model') or user_preferences.get('selected_model')

        selected_prompt = session.get('selected_prompt') or user_preferences.get('selected_prompt')
        if selected_prompt and selected_prompt not in prompt_names:
            selected_prompt = default_prompt

        if not selected_provider and default_provider:
            selected_provider = default_provider
        if not selected_prompt and default_prompt:
            selected_prompt = default_prompt

        return selected_provider, selected_model, selected_prompt

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-dev-secret-key-please-change-in-prod-or-env')

def _check_cancelled(state):
    """检查是否被取消，如果已取消则更新状态并返回True"""
    if state.is_cancelled():
        debug_print('INFO', '处理被用户取消')
        state.cancel()
        return True
    return False

def run_processing_task(directory, selected_provider_name, selected_model_key, api_key, selected_prompt_name):
    """异步处理任务（线程安全）"""
    state = ProcessingState()
    
    debug_print('INFO', '=== run_processing_task 开始执行 ===')
    debug_print('INFO', f'目录: {directory}')
    debug_print('INFO', f'提供商: {selected_provider_name}')
    debug_print('INFO', f'模型: {selected_model_key}')
    debug_print('INFO', f'Prompt: {selected_prompt_name}')
    debug_print('INFO', f'API Key: {"已配置" if api_key else "未配置"}')
    
    # 初始化处理状态
    state.start()
    debug_print('INFO', '处理状态已初始化为 scanning')
    
    try:
        if _check_cancelled(state):
            return
        
        # 验证配置
        debug_print('INFO', '开始验证AI提供商配置')
        current_all_providers = ProviderManager.get_all_providers()
        debug_print('INFO', f'可用提供商: {list(current_all_providers.keys())}')
        
        if _check_cancelled(state):
            return
        
        if selected_provider_name not in current_all_providers:
            raise ValueError(f"AI提供者 '{selected_provider_name}' 未找到。")
        
        provider_config = current_all_providers[selected_provider_name]
        debug_print('INFO', f'提供商配置: {provider_config}')
        
        if 'models' not in provider_config or selected_model_key not in provider_config['models']:
            raise ValueError(f"模型 '{selected_model_key}' 在提供者 '{selected_provider_name}' 中未找到。")

        # 初始化AI客户端
        debug_print('INFO', '初始化AI客户端')
        client = OpenAI(api_key=api_key, base_url=provider_config["base_url"])
        model_id = provider_config["models"][selected_model_key]
        debug_print('INFO', f'模型ID: {model_id}')
        
        if _check_cancelled(state):
            return
        
        # 验证提示词
        debug_print('INFO', '验证Prompt配置')
        current_all_prompts = PromptManager.get_all_prompts()
        debug_print('INFO', f'可用Prompts: {list(current_all_prompts.keys())}')
        
        if _check_cancelled(state):
            return
        
        if selected_prompt_name not in current_all_prompts:
            raise ValueError(f"Prompt '{selected_prompt_name}' 未找到。")
        system_prompt = current_all_prompts[selected_prompt_name]
        debug_print('INFO', f'Prompt内容长度: {len(system_prompt) if system_prompt else 0}')
        
        # 扫描文件
        debug_print('INFO', f'开始扫描目录: {directory}')
        txt_files = scan_txt_files(directory)
        debug_print('INFO', f'扫描结果: 找到 {len(txt_files)} 个txt文件')
        
        if _check_cancelled(state):
            return
        
        if not txt_files:
            raise ValueError("未找到txt文件。")
        
        # 开始处理
        state.start_processing(len(txt_files))
        debug_print('INFO', f'状态更新为 processing，开始处理 {len(txt_files)} 个文件')
        
        # 处理文件
        for i, file_path in enumerate(txt_files):
            if _check_cancelled(state):
                return
                
            debug_print('INFO', f'处理文件 {i+1}/{len(txt_files)}: {os.path.basename(file_path)}')
            state.update_progress(i, os.path.basename(file_path))
            
            debug_print('INFO', f'开始处理文件 {i+1}/{len(txt_files)}, 当前已处理: {i}')
            
            # 实际处理文件
            try:
                response = process_file(file_path, client, system_prompt, model_id)
                md_path = save_response(file_path, response)
                
                progress = 100 if i == len(txt_files) - 1 else int(((i + 1) / len(txt_files) * 100))
                state.update_progress(i + 1, None, progress)
                state.add_result(file_path, md_path)
                
                debug_print('INFO', f'文件 {os.path.basename(file_path)} 处理完成，进度: {progress}%')
                
            except Exception as file_error:
                debug_print('ERROR', f'文件处理失败: {file_error}')
                state.update_progress(i + 1)
                state.add_result(file_path, None, str(file_error))
                debug_print('INFO', f'文件 {os.path.basename(file_path)} 处理失败')
        
        # 处理完成
        state.complete()
        debug_print('INFO', f"任务完成：处理了 {len(txt_files)} 个文件")
        
    except Exception as e:
        error_message = str(e)
        debug_print('ERROR', f"处理任务失败: {error_message}")
        state.set_error(f"处理失败: {error_message.splitlines()[0]}")
    
    debug_print('INFO', '=== run_processing_task 执行结束 ===')

def handle_config_selection(session, user_preferences, form_data, all_providers, auto_save=False):
    """处理配置选择的通用逻辑"""
    # 批量解码表单数据
    decoded_data = safe_url_decode_form(form_data, ['selected_provider', 'selected_model', 'selected_prompt', 'directory_path'])
    
    new_provider = decoded_data['selected_provider']
    new_model = decoded_data['selected_model']
    new_prompt = decoded_data['selected_prompt']
    new_directory = decoded_data['directory_path']
    
    # 模型自动对应逻辑
    if new_provider and new_provider in all_providers:
        provider_models = ProviderManager.get_provider_models(new_provider, all_providers)
        if provider_models:
            if not new_model or new_model not in provider_models:
                new_model = list(provider_models.keys())[0]
                debug_print('INFO', f"自动选择模型: {new_model} (提供商: {new_provider})")
    
    # 统一保存逻辑
    selections = {
        'selected_provider': new_provider,
        'selected_model': new_model,
        'selected_prompt': new_prompt,
        'directory_path': new_directory
    }
    
    # 更新session
    session.update(selections)
    
    # 保存到持久化存储
    if save_user_preferences(selections):
        if not auto_save:
            set_session_message(session, 'message', "✅ 配置选择已自动保存")
    else:
        if not auto_save:
            set_session_message(session, 'error', "⚠️ 配置保存失败")

@app.route('/', methods=['GET', 'POST'])
def index():
    """主页路由"""
    # 获取所有配置
    all_providers = ProviderManager.get_all_providers()
    all_prompts = PromptManager.get_all_prompts()
    user_preferences = load_user_preferences()
    
    # 边界情况处理
    if not all_providers and not all_prompts:
        set_session_message(session, 'error', "AI提供者和Prompt配置均为空。请检查config.json。")
    
    # 获取默认值
    default_provider = ProviderManager.get_default_provider(all_providers)
    default_prompt = PromptManager.get_default_prompt(all_prompts)
    
    provider_models = ProviderManager.get_provider_models(default_provider, all_providers)
    default_model = list(provider_models.keys())[0] if provider_models else ''
    
    # 获取选择（从session、用户偏好或默认值，如果选择的项目已不存在则回退到默认值）
    selected_provider, selected_model, selected_prompt = SelectionManager.get_selection_from_sources(
        session, user_preferences, all_providers, all_prompts, default_provider, default_model, default_prompt
    )
    
    directory_path = session.get('directory_path') or user_preferences.get('directory_path') or ''
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        try:
            if form_type == 'config_selection_form':
                handle_config_selection(
                    session, user_preferences, request.form, 
                    all_providers, auto_save=(request.form.get('auto_save') == 'true')
                )
                # AJAX请求返回JSON，包含新服务商的API Key等信息
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    new_provider = session.get('selected_provider', '')
                    new_api_key = get_provider_api_key(new_provider) if new_provider else ''
                    new_model = session.get('selected_model', '')
                    return jsonify({
                        'success': True,
                        'selected_provider': new_provider,
                        'selected_model': new_model,
                        'api_key': new_api_key
                    })
                return redirect(url_for('index'))
            
            elif form_type == 'save_provider_form':
                decoded_data = safe_url_decode_form(
                    request.form, ['provider_name', 'base_url', 'api_key_for_save', 'models']
                )
                
                try:
                    models = json.loads(decoded_data['models']) if decoded_data['models'] else {}
                    if save_provider(decoded_data['provider_name'], decoded_data['base_url'], 
                                   decoded_data['api_key_for_save'], models):
                        session['selected_provider'] = decoded_data['provider_name']
                        if models:
                            session['selected_model'] = list(models.keys())[0]
                        set_session_message(session, 'message', f"AI提供者 '{decoded_data['provider_name']}' 保存成功")
                except json.JSONDecodeError:
                    set_session_message(session, 'error', "模型配置格式错误")
                
                return redirect(url_for('index'))
            
            elif form_type == 'save_prompt_form':
                prompt_name = safe_url_decode(request.form.get('prompt_name', ''))
                prompt_content = request.form.get('prompt_content', '')
                
                all_prompts = PromptManager.get_all_prompts()
                all_prompts[prompt_name] = prompt_content
                
                if save_custom_prompts(all_prompts):
                    set_session_message(session, 'message', f"Prompt '{prompt_name}' 保存成功")
                else:
                    set_session_message(session, 'error', f"保存Prompt '{prompt_name}' 失败")
                
                return redirect(url_for('index'))
            
            elif form_type == 'save_api_key_form':
                provider_name = safe_url_decode(request.form.get('provider_name_for_key', ''))
                api_key = request.form.get('api_key_for_save', '')

                if save_provider_api_key(provider_name, api_key):
                    set_session_message(session, 'message', f"API Key for '{provider_name}' 保存成功")
                else:
                    set_session_message(session, 'error', f"保存API Key for '{provider_name}' 失败")

                return redirect(url_for('index'))

            elif form_type == 'add_model_form':
                provider_name = safe_url_decode(request.form.get('provider_name_for_model', ''))
                model_display_name = request.form.get('model_display_name', '')
                model_id = request.form.get('model_id', '')

                if add_model_to_provider(provider_name, model_display_name, model_id):
                    set_session_message(session, 'message', f"模型 '{model_display_name}' 添加成功")
                else:
                    set_session_message(session, 'error', f"添加模型失败：{model_display_name}")

                return redirect(url_for('index'))

            elif form_type == 'delete_model_form':
                provider_name = safe_url_decode(request.form.get('provider_name_for_model_delete', ''))
                model_name = safe_url_decode(request.form.get('model_name_to_delete', ''))

                if delete_model_from_provider(provider_name, model_name):
                    set_session_message(session, 'message', f"模型 '{model_name}' 删除成功")
                else:
                    set_session_message(session, 'error', f"删除模型失败：{model_name}")

                return redirect(url_for('index'))

            elif form_type == 'delete_provider_form':
                provider_name = safe_url_decode(request.form.get('provider_name_to_delete', ''))
                if move_provider_to_trash(provider_name):
                    set_session_message(session, 'message', f"AI提供者 '{provider_name}' 已移动到回收站")
                else:
                    set_session_message(session, 'error', f"移动到回收站失败：{provider_name}")
                return redirect(url_for('index'))
            
            elif form_type == 'delete_prompt_form':
                prompt_name = safe_url_decode(request.form.get('prompt_name_to_delete', ''))
                if move_prompt_to_trash(prompt_name):
                    set_session_message(session, 'message', f"Prompt '{prompt_name}' 已移动到回收站")
                else:
                    set_session_message(session, 'error', f"移动到回收站失败：{prompt_name}")
                return redirect(url_for('index'))
            
            elif form_type == 'restore_provider_form':
                provider_name = safe_url_decode(request.form.get('provider_name_to_restore', ''))
                if restore_provider_from_trash(provider_name):
                    set_session_message(session, 'message', f"AI提供者 '{provider_name}' 恢复成功")
                else:
                    set_session_message(session, 'error', f"恢复AI提供者 '{provider_name}' 失败")
                return redirect(url_for('index'))
            
            elif form_type == 'restore_prompt_form':
                prompt_name = safe_url_decode(request.form.get('prompt_name_to_restore', ''))
                if restore_prompt_from_trash(prompt_name):
                    set_session_message(session, 'message', f"Prompt '{prompt_name}' 恢复成功")
                else:
                    set_session_message(session, 'error', f"恢复Prompt '{prompt_name}' 失败")
                return redirect(url_for('index'))
            
            elif form_type == 'permanent_delete_provider_form':
                provider_name = safe_url_decode(request.form.get('provider_name_to_permanent_delete', ''))
                if permanent_delete_provider_from_trash(provider_name):
                    set_session_message(session, 'message', f"AI提供者 '{provider_name}' 已永久删除")
                else:
                    set_session_message(session, 'error', f"永久删除AI提供者 '{provider_name}' 失败")
                return redirect(url_for('index'))
            
            elif form_type == 'permanent_delete_prompt_form':
                prompt_name = safe_url_decode(request.form.get('prompt_name_to_permanent_delete', ''))
                if permanent_delete_prompt_from_trash(prompt_name):
                    set_session_message(session, 'message', f"Prompt '{prompt_name}' 已永久删除")
                else:
                    set_session_message(session, 'error', f"永久删除Prompt '{prompt_name}' 失败")
                return redirect(url_for('index'))
        
        except Exception as e:
            debug_print('ERROR', f"处理表单 {form_type} 时出错: {e}")
            set_session_message(session, 'error', f"操作失败: {e}")
            return redirect(url_for('index'))
    
    # GET请求处理
    current_api_key = get_provider_api_key(selected_provider) if selected_provider else ''
    
    # 清理session消息
    last_message = session.pop('last_message', None)
    last_error = session.pop('last_error', None)
    
    # 获取回收站数据
    trash_data = get_trash_items()
    
    return render_template('index.html',
        all_providers=all_providers,
        selected_provider_name=selected_provider,
        provider_config=all_providers.get(selected_provider, {'models': {}}),
        selected_model_key=selected_model,
        all_prompts=all_prompts,
        selected_prompt_name=selected_prompt,
        current_api_key=current_api_key,
        directory_path=directory_path,
        trash_data=trash_data,
        last_message=last_message,
        last_error=last_error
    )

@app.route('/start_processing', methods=['POST'])
def start_processing():
    """启动处理任务"""
    debug_print('INFO', '=== start_processing 开始执行 ===')
    
    selected_provider_name = request.form.get('selected_provider')
    selected_model_key = request.form.get('selected_model')
    api_key = request.form.get('api_key')
    selected_prompt_name = request.form.get('selected_prompt')
    directory = request.form.get('directory_path')

    debug_print('INFO', f'接收到参数 - Provider: {selected_provider_name}, Model: {selected_model_key}, Prompt: {selected_prompt_name}, Directory: {directory}')
    debug_print('INFO', f'API Key状态: {"已配置" if api_key else "未配置"}')
    debug_print('INFO', f'目录状态: {directory} (存在: {os.path.exists(directory) if directory else "N/A"})')

    # 参数验证
    if not api_key:
        debug_print('ERROR', 'API Key 未配置')
        return jsonify({'status': 'error', 'message': 'API Key 未配置'}), 400
    if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
        debug_print('ERROR', f'目录路径无效: {directory}')
        return jsonify({'status': 'error', 'message': '请提供有效的目录路径'}), 400

    debug_print('INFO', '参数验证通过，启动异步处理任务')
    
    # 异步执行处理任务
    processing_thread = threading.Thread(
        target=run_processing_task,
        args=(directory, selected_provider_name, selected_model_key, api_key, selected_prompt_name)
    )
    processing_thread.daemon = True
    processing_thread.start()
    
    debug_print('INFO', f'处理线程已启动，线程ID: {processing_thread.ident}')
    
    return jsonify({'status': 'started', 'message': '处理已启动'})

@app.route('/get_processing_status', methods=['GET'])
def get_processing_status():
    """获取处理状态"""
    state = ProcessingState()
    state_dict = state.get_dict()
    debug_print('INFO', f'当前处理状态: {state_dict["status"]}, 进度: {state_dict["progress"]}%')
    return jsonify(state_dict)

@app.route('/cancel_processing', methods=['POST'])
def cancel_processing():
    """取消处理任务"""
    state = ProcessingState()
    
    debug_print('INFO', '=== cancel_processing 开始执行 ===')
    
    # 检查当前状态
    state_dict = state.get_dict()
    if state_dict['status'] not in ['processing', 'scanning', 'started', 'idle']:
        debug_print('INFO', f'当前状态为 {state_dict["status"]}，不需要取消')
        return jsonify({'status': 'error', 'message': '当前没有正在进行的处理任务'}), 400
    
    # 设置取消标志并更新状态
    state.set_cancelled()
    if state.is_running():
        state.cancel()
        debug_print('INFO', '处理状态已更新为 cancelled')
    
    debug_print('INFO', '已设置取消标志')
    return jsonify({'status': 'cancelled', 'message': '处理已取消'})
@app.route('/clear_session')
def clear_session():
    """清理会话"""
    session.clear()
    return "Session cleared! <a href='/'>返回主页</a>"

@app.route('/get_available_drives', methods=['GET'])
def get_available_drives():
    """获取可用的驱动器列表（Windows）或根目录（Linux）"""
    try:
        drives = []
        if sys.platform == 'win32':
            # Windows 系统：获取所有驱动器
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if bitmask & 1:
                    drives.append(f'{letter}:\\')
                bitmask >>= 1
        else:
            # Linux/Mac 系统：使用根目录
            drives.append('/')
        
        return jsonify({
            'success': True,
            'drives': drives
        })
    except Exception as e:
        debug_print('ERROR', f'获取驱动器列表失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get_directory_contents', methods=['GET'])
def get_directory_contents():
    """获取指定目录下的子目录列表"""
    try:
        path = request.args.get('path', '')
        
        # 如果路径为空，返回根目录/驱动器列表
        if not path:
            return get_available_drives()
        
        # 安全检查：确保路径存在且是目录
        if not os.path.exists(path):
            return jsonify({
                'success': False,
                'error': '路径不存在'
            }), 400
        
        if not os.path.isdir(path):
            return jsonify({
                'success': False,
                'error': '不是一个目录'
            }), 400
        
        # 获取父目录
        parent = os.path.dirname(path)
        # 处理根目录的情况
        if sys.platform == 'win32' and parent == '':
            parent = None
        elif parent == path:
            parent = None
        
        # 获取子目录列表
        directories = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    # 跳过隐藏目录（可选）
                    if not item.startswith('.'):
                        directories.append({
                            'name': item,
                            'path': item_path
                        })
        except PermissionError:
            pass
        
        # 按名称排序
        directories.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            'success': True,
            'path': path,
            'parent': parent,
            'directories': directories
        })
    except Exception as e:
        debug_print('ERROR', f'获取目录内容失败: {e}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/view_result', methods=['GET'])
def view_result():
    """查看处理结果文件"""
    file_path = request.args.get('path', '')
    
    if not file_path:
        return jsonify({'error': '未提供文件路径'}), 400
    
    # 安全检查：确保文件路径在允许的范围内
    # 防止目录遍历攻击
    real_path = os.path.realpath(file_path)
    
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 只允许查看 .md 和 .txt 文件
    if not real_path.endswith(('.md', '.txt')):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    try:
        with open(real_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'success': True,
            'file_path': file_path,
            'file_name': os.path.basename(real_path),
            'content': content
        })
    except UnicodeDecodeError:
        try:
            with open(real_path, 'r', encoding='gbk') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'file_path': file_path,
                'file_name': os.path.basename(real_path),
                'content': content
            })
        except Exception as e:
            return jsonify({'error': f'文件读取失败: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'文件读取失败: {e}'}), 500

if __name__ == '__main__':
    debug_level = os.environ.get('DEBUG_LEVEL', 'ERROR').upper()
    app.run(debug=(debug_level == 'DEBUG'), host='0.0.0.0', port=5000)