# -*- coding: utf-8 -*-
import sys
import codecs

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    # Windows控制台编码设置
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except:
        pass

# 重定向输出到UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
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
import shutil

# 生产环境调试级别控制 - 修改为DEBUG模式以便诊断
DEBUG_LEVEL = os.environ.get('DEBUG_LEVEL', 'DEBUG').upper()

def debug_print(level, message):
    """统一的调试输出函数，根据DEBUG_LEVEL控制输出"""
    if DEBUG_LEVEL in ['DEBUG', 'ALL'] or (DEBUG_LEVEL == 'ERROR' and level == 'ERROR'):
        try:
            # 安全地处理消息，确保能够输出任何字符
            if isinstance(message, str):
                # 对于字符串，使用replace错误处理
                safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
            else:
                # 对于其他类型（如字典、列表），先转换为字符串
                safe_message = str(message).encode('utf-8', errors='replace').decode('utf-8')
            
            # 添加flush确保输出立即显示
            print(f"{level}: {safe_message}", flush=True)
        except Exception as e:
            # 如果还是出错，使用最基本的方式
            try:
                print(f"{level}: [Message output failed]", flush=True)
            except:
                pass  # 静默忽略所有错误

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

# 全局处理状态
processing_state = {
    'status': 'idle',
    'progress': 0,
    'total_files': 0,
    'processed_files_count': 0,
    'current_file': '',
    'results': [],
    'error': None,
    'start_time': None,
    'end_time': None,
    'cancelled': False  # 添加取消标志
}

def run_processing_task(directory, selected_provider_name, selected_model_key, api_key, selected_prompt_name):
    """异步处理任务"""
    global processing_state
    
    debug_print('INFO', '=== run_processing_task 开始执行 ===')
    debug_print('INFO', f'目录: {directory}')
    debug_print('INFO', f'提供商: {selected_provider_name}')
    debug_print('INFO', f'模型: {selected_model_key}')
    debug_print('INFO', f'Prompt: {selected_prompt_name}')
    debug_print('INFO', f'API Key: {"已配置" if api_key else "未配置"}')
    
    # 初始化处理状态 - 重要：重置取消标志位
    processing_state.update({
        'status': 'scanning',
        'progress': 0,
        'total_files': 0,
        'processed_files_count': 0,
        'current_file': '',
        'results': [],
        'error': None,
        'start_time': time.time(),
        'end_time': None,
        'cancelled': False  # 关键修复：重置取消标志位，允许新的处理任务启动
    })
    
    debug_print('INFO', '处理状态已初始化为 scanning')
    
    try:
        # 检查是否被取消
        if processing_state.get('cancelled', False):
            debug_print('INFO', '处理被用户取消')
            processing_state.update({
                'status': 'cancelled',
                'error': '用户取消了处理',
                'current_file': '',
                'end_time': time.time()
            })
            return
        
        # 验证配置
        debug_print('INFO', '开始验证AI提供商配置')
        current_all_providers = ProviderManager.get_all_providers()
        debug_print('INFO', f'可用提供商: {list(current_all_providers.keys())}')
        
        # 检查是否被取消
        if processing_state.get('cancelled', False):
            debug_print('INFO', '处理被用户取消')
            processing_state.update({
                'status': 'cancelled',
                'error': '用户取消了处理',
                'current_file': '',
                'end_time': time.time()
            })
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
        
        # 检查是否被取消
        if processing_state.get('cancelled', False):
            debug_print('INFO', '处理被用户取消')
            processing_state.update({
                'status': 'cancelled',
                'error': '用户取消了处理',
                'current_file': '',
                'end_time': time.time()
            })
            return
        
        # 验证提示词
        debug_print('INFO', '验证Prompt配置')
        current_all_prompts = PromptManager.get_all_prompts()
        debug_print('INFO', f'可用Prompts: {list(current_all_prompts.keys())}')
        
        # 检查是否被取消
        if processing_state.get('cancelled', False):
            debug_print('INFO', '处理被用户取消')
            processing_state.update({
                'status': 'cancelled',
                'error': '用户取消了处理',
                'current_file': '',
                'end_time': time.time()
            })
            return
        
        if selected_prompt_name not in current_all_prompts:
            raise ValueError(f"Prompt '{selected_prompt_name}' 未找到。")
        system_prompt = current_all_prompts[selected_prompt_name]
        debug_print('INFO', f'Prompt内容长度: {len(system_prompt) if system_prompt else 0}')
        
        # 扫描文件
        debug_print('INFO', f'开始扫描目录: {directory}')
        txt_files = scan_txt_files(directory)
        debug_print('INFO', f'扫描结果: 找到 {len(txt_files)} 个txt文件')
        
        # 检查是否被取消
        if processing_state.get('cancelled', False):
            debug_print('INFO', '处理被用户取消')
            processing_state.update({
                'status': 'cancelled',
                'error': '用户取消了处理',
                'current_file': '',
                'end_time': time.time()
            })
            return
        
        if not txt_files:
            raise ValueError("未找到txt文件。")
        
        # 开始处理
        processing_state.update({
            'status': 'processing',
            'total_files': len(txt_files),
            'current_file': f'准备处理 {len(txt_files)} 个文件...'
        })
        
        debug_print('INFO', f'状态更新为 processing，开始处理 {len(txt_files)} 个文件')
        
        # 处理文件
        for i, file_path in enumerate(txt_files):
            # 检查是否被取消
            if processing_state.get('cancelled', False):
                debug_print('INFO', '处理被用户取消')
                processing_state.update({
                    'status': 'cancelled',
                    'error': '用户取消了处理',
                    'current_file': '',
                    'end_time': time.time()
                })
                return
                
            debug_print('INFO', f'处理文件 {i+1}/{len(txt_files)}: {os.path.basename(file_path)}')
            
            # 只更新当前文件名，不更新进度
            processing_state['current_file'] = os.path.basename(file_path)
            processing_state['processed_files_count'] = i  # 使用i而不是i+1，表示已完成的数量
            
            debug_print('INFO', f'开始处理文件 {i+1}/{len(txt_files)}, 当前已处理: {processing_state["processed_files_count"]}')
            
            # 实际处理文件
            try:
                response = process_file(file_path, client, system_prompt, model_id)
                md_path = save_response(file_path, response)
                
                # 文件处理完成后才更新完成计数
                processing_state['processed_files_count'] = i + 1
                processing_state['results'].append({
                    'source': file_path,
                    'output': md_path
                })
                
                # 如果是最后一个文件，完成后设置进度为100%
                if i == len(txt_files) - 1:
                    processing_state['progress'] = 100
                else:
                    # 对于非最后一个文件，进度 = (已处理数量 / 总数量) * 100
                    processing_state['progress'] = int(((i + 1) / len(txt_files) * 100))
                
                debug_print('INFO', f'文件 {os.path.basename(file_path)} 处理完成，进度: {processing_state["progress"]}%')
                
            except Exception as file_error:
                debug_print('ERROR', f'文件处理失败: {file_error}')
                # 即使单个文件失败，也更新完成计数以维持进度准确性
                processing_state['processed_files_count'] = i + 1
                processing_state['results'].append({
                    'source': file_path,
                    'output': None,
                    'error': str(file_error)
                })
                
                debug_print('INFO', f'文件 {os.path.basename(file_path)} 处理失败，已更新进度: {processing_state["progress"]}%')
        
        # 处理完成
        processing_state.update({
            'status': 'completed',
            'progress': 100,
            'processed_files_count': len(txt_files),
            'current_file': '',
            'end_time': time.time()
        })
        
        debug_print('INFO', f"任务完成：处理了 {len(txt_files)} 个文件")
        
    except Exception as e:
        error_message = str(e)
        debug_print('ERROR', f"处理任务失败: {error_message}")
        
        processing_state.update({
            'status': 'error',
            'error': f"处理失败: {error_message.splitlines()[0]}",
            'current_file': '',
            'end_time': time.time()
        })
    
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
    global processing_state
    
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
    debug_print('INFO', f'当前处理状态: {processing_state["status"]}, 进度: {processing_state["progress"]}%')
    debug_print('DEBUG', f'完整状态信息: {processing_state}')
    return jsonify(processing_state)

@app.route('/cancel_processing', methods=['POST'])
def cancel_processing():
    """取消处理任务"""
    global processing_state
    
    debug_print('INFO', '=== cancel_processing 开始执行 ===')
    
    # 检查当前状态 - 扩展取消范围
    if processing_state['status'] not in ['processing', 'scanning', 'started', 'idle']:
        debug_print('INFO', f'当前状态为 {processing_state["status"]}，不需要取消')
        return jsonify({'status': 'error', 'message': '当前没有正在进行的处理任务'}), 400
    
    # 总是设置取消标志
    processing_state['cancelled'] = True
    debug_print('INFO', '已设置取消标志')
    
    # 如果当前有处理在进行，更新状态为取消
    if processing_state['status'] in ['processing', 'scanning', 'started']:
        processing_state.update({
            'status': 'cancelled',
            'error': '用户取消了处理',
            'current_file': '',
            'end_time': time.time()
        })
        debug_print('INFO', '处理状态已更新为 cancelled')
    else:
        debug_print('INFO', '当前状态不需要更新')
    
    return jsonify({'status': 'cancelled', 'message': '处理已取消'})
@app.route('/clear_session')
def clear_session():
    """清理会话"""
    session.clear()
    return "Session cleared! <a href='/'>返回主页</a>"

@app.route('/simple_test')
def simple_test():
    """简单的JavaScript事件测试页面"""
    return render_template('simple_test.html')

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

if __name__ == '__main__':
    app.run(debug=DEBUG_LEVEL == 'DEBUG', host='0.0.0.0', port=5000)