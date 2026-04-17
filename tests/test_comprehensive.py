# -*- coding: utf-8 -*-
"""AI Summary 项目 - 全面测试脚本"""

import requests
import json
import time
import os
import re
import subprocess

BASE_URL = "http://127.0.0.1:5000"
PROJECT_ROOT = r"c:\Users\15832\Downloads\ai_summary\ai_summary"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name):
        self.passed += 1
        print(f"  ✅ {name}")

    def add_fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ {name}: {reason}")

    def summary(self):
        print("\n" + "="*60)
        print(" 测试结果总结")
        print("="*60)
        print(f"\n通过: {self.passed}/{self.passed + self.failed}")

        if self.errors:
            print("\n失败项目:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")

        if self.failed == 0:
            print("\n🎉 所有测试通过!")
        else:
            print(f"\n⚠️  {self.failed} 个测试失败")

        return self.failed == 0


def test_backend_basic(result):
    """测试后端基础功能"""
    print("\n【1. 后端基础功能】")

    # 1.1 主页加载
    try:
        r = requests.get(BASE_URL + "/", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        assert "AI" in r.text, "页面缺少AI内容"
        result.add_pass("主页加载")
    except Exception as e:
        result.add_fail("主页加载", str(e))

    # 1.2 CSS加载
    try:
        r = requests.get(BASE_URL + "/static/style.css", timeout=5)
        assert r.status_code == 200, f"CSS状态码{r.status_code}"
        result.add_pass("CSS加载")
    except Exception as e:
        result.add_fail("CSS加载", str(e))

    # 1.3 JS加载
    try:
        r = requests.get(BASE_URL + "/static/script.js", timeout=5)
        assert r.status_code == 200, f"JS状态码{r.status_code}"
        result.add_pass("JS加载")
    except Exception as e:
        result.add_fail("JS加载", str(e))

    # 1.4 测试页面
    try:
        r = requests.get(BASE_URL + "/simple_test", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        result.add_pass("测试页面加载")
    except Exception as e:
        result.add_fail("测试页面加载", str(e))


def test_provider_management(result):
    """测试服务商管理"""
    print("\n【2. 服务商管理】")

    timestamp = int(time.time())
    provider_name = f"TestProvider_{timestamp}"

    # 2.1 新增服务商
    try:
        data = {
            "form_type": "save_provider_form",
            "provider_name": provider_name,
            "base_url": "https://api.test.com",
            "api_key_for_save": "sk-key-123",
            "models": json.dumps({"模型A": "model-a"})
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("新增服务商")
    except Exception as e:
        result.add_fail("新增服务商", str(e))
        return

    # 2.2 更新API Key
    try:
        data = {
            "form_type": "save_api_key_form",
            "provider_name_for_key": provider_name,
            "api_key_for_save": "sk-new-key-456"
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("更新API Key")
    except Exception as e:
        result.add_fail("更新API Key", str(e))

    # 2.3 删除服务商到回收站
    try:
        data = {
            "form_type": "delete_provider_form",
            "provider_name_to_delete": provider_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("删除服务商到回收站")
    except Exception as e:
        result.add_fail("删除服务商到回收站", str(e))

    # 2.4 恢复服务商
    try:
        data = {
            "form_type": "restore_provider_form",
            "provider_name_to_restore": provider_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("恢复服务商")
    except Exception as e:
        result.add_fail("恢复服务商", str(e))

    # 2.5 永久删除服务商
    try:
        data = {
            "form_type": "permanent_delete_provider_form",
            "provider_name_to_permanent_delete": provider_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("永久删除服务商")
    except Exception as e:
        result.add_fail("永久删除服务商", str(e))


def test_prompt_management(result):
    """测试Prompt管理"""
    print("\n【3. Prompt管理】")

    timestamp = int(time.time())
    prompt_name = f"TestPrompt_{timestamp}"
    prompt_content = "请总结以下内容"

    # 3.1 新增Prompt
    try:
        data = {
            "form_type": "save_prompt_form",
            "prompt_name": prompt_name,
            "prompt_content": prompt_content
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("新增Prompt")
    except Exception as e:
        result.add_fail("新增Prompt", str(e))
        return

    # 3.2 删除Prompt到回收站
    try:
        data = {
            "form_type": "delete_prompt_form",
            "prompt_name_to_delete": prompt_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("删除Prompt到回收站")
    except Exception as e:
        result.add_fail("删除Prompt到回收站", str(e))

    # 3.3 恢复Prompt
    try:
        data = {
            "form_type": "restore_prompt_form",
            "prompt_name_to_restore": prompt_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("恢复Prompt")
    except Exception as e:
        result.add_fail("恢复Prompt", str(e))

    # 3.4 永久删除Prompt
    try:
        data = {
            "form_type": "permanent_delete_prompt_form",
            "prompt_name_to_permanent_delete": prompt_name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("永久删除Prompt")
    except Exception as e:
        result.add_fail("永久删除Prompt", str(e))


def test_config_selection(result):
    """测试配置选择"""
    print("\n【4. 配置选择】")

    try:
        data = {
            "form_type": "config_selection_form",
            "selected_provider": "Test",
            "selected_model": "默认模型",
            "selected_prompt": "",
            "directory_path": "C:/Test/Txt",
            "auto_save": "true"
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        result.add_pass("保存配置选择")
    except Exception as e:
        result.add_fail("保存配置选择", str(e))


def test_processing_status(result):
    """测试处理状态API"""
    print("\n【5. 处理状态API】")

    # 5.1 获取处理状态
    try:
        r = requests.get(BASE_URL + "/get_processing_status", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        data = r.json()
        assert "status" in data, "响应缺少status字段"
        result.add_pass("获取处理状态")
    except Exception as e:
        result.add_fail("获取处理状态", str(e))

    # 5.2 取消处理(空闲状态)
    try:
        r = requests.post(BASE_URL + "/cancel_processing", timeout=5)
        assert r.status_code in [200, 400], f"状态码{r.status_code}"
        result.add_pass("取消处理(空闲状态)")
    except Exception as e:
        result.add_fail("取消处理(空闲状态)", str(e))

    # 5.3 清理会话
    try:
        r = requests.get(BASE_URL + "/clear_session", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        result.add_pass("清理会话")
    except Exception as e:
        result.add_fail("清理会话", str(e))


def test_javascript(result):
    """测试JavaScript"""
    print("\n【6. JavaScript检查】")

    js_path = os.path.join(PROJECT_ROOT, "static", "script.js")

    # 6.1 JavaScript语法检查
    try:
        result_check = subprocess.run(
            ["node", "--check", js_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result_check.returncode == 0, f"语法错误: {result_check.stderr}"
        result.add_pass("JavaScript语法检查")
    except FileNotFoundError:
        result.add_fail("JavaScript语法检查", "Node.js未安装")
    except Exception as e:
        result.add_fail("JavaScript语法检查", str(e))

    # 6.2 检查prompt()调用
    try:
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找 prompt( 调用
        prompt_matches = re.findall(r'prompt\s*\(', content)

        # 过滤掉注释中的
        real_prompt_matches = []
        for i, line in enumerate(content.split('\n'), 1):
            if 'prompt(' in line and not line.strip().startswith('//') and not line.strip().startswith('*'):
                if '自定义对话框' not in line and 'input-dialog' not in line:
                    real_prompt_matches.append((i, line.strip()))

        if real_prompt_matches:
            msg = f"发现{len(real_prompt_matches)}处prompt()调用"
            result.add_fail("prompt()调用检查", msg)
        else:
            result.add_pass("prompt()调用检查(已清除)")
    except Exception as e:
        result.add_fail("prompt()调用检查", str(e))

    # 6.3 检查关键函数定义
    # 实际函数名映射
    functions_to_check = [
        ("handleProviderAddNew", r"window\.handleProviderAddNew\s*="),
        ("handlePromptAddNew", r"window\.handlePromptAddNew\s*="),
        ("selectProvider", r"window\.selectProvider\s*="),
        ("selectPrompt", r"window\.selectPrompt\s*="),
        ("deleteProvider", r"function\s+deleteProvider\s*\(|deleteProvider\s*=\s*function"),
        ("deletePrompt", r"function\s+deletePrompt\s*\(|deletePrompt\s*=\s*function"),
        ("startProcessing (ProcessingManager)", r"startProcessing\s*\(\s*\)"),
        ("updateUI (ProcessingManager)", r"updateUI\s*\(\s*status\s*\)"),
        ("showMessage (ProcessingManager)", r"showMessage\s*\(\s*message"),
        ("processingManager 实例", r"processingManager\s*=\s*new\s+ProcessingManager"),
    ]

    try:
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()

        for func_name, pattern in functions_to_check:
            if re.search(pattern, content):
                result.add_pass(f"函数{func_name}定义")
            else:
                result.add_fail(f"函数{func_name}定义", "未找到")
    except Exception as e:
        result.add_fail("函数定义检查", str(e))


def test_template(result):
    """测试模板"""
    print("\n【7. 模板检查】")

    template_path = os.path.join(PROJECT_ROOT, "templates", "index.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 7.1 检查关键元素
        elements = {
            "服务商下拉菜单": r"provider-dropdown|selectProvider",
            "模型下拉菜单": r"model-dropdown|selectModel",
            "Prompt下拉菜单": r"prompt-dropdown|selectPrompt",
            "目录输入框": r"directory-input|directory",
            "开始按钮": r"start-process-btn|startProcessing",
            "状态显示": r"processing-progress|status"
        }

        for name, pattern in elements.items():
            if re.search(pattern, content, re.IGNORECASE):
                result.add_pass(f"页面元素-{name}")
            else:
                result.add_fail(f"页面元素-{name}", "未找到")

        # 7.2 检查事件绑定
        bindings = {
            "handleProviderAddNew": r"handleProviderAddNew\s*\(",
            "handlePromptAddNew": r"handlePromptAddNew\s*\(",
            "开始按钮(onclick)": r"start-process-btn",
        }

        for name, pattern in bindings.items():
            if re.search(pattern, content):
                result.add_pass(f"事件绑定-{name}")
            else:
                result.add_fail(f"事件绑定-{name}", "未找到")

    except Exception as e:
        result.add_fail("模板检查", str(e))


def test_config_file(result):
    """测试配置文件"""
    print("\n【8. 配置文件检查】")

    config_path = os.path.join(PROJECT_ROOT, "config.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 8.1 检查必需字段
        required_fields = [
            "providers", "current_provider", "custom_prompts",
            "current_prompt", "file_paths", "trash", "user_preferences"
        ]

        for field in required_fields:
            if field in config:
                result.add_pass(f"配置字段-{field}")
            else:
                result.add_fail(f"配置字段-{field}", "缺少")

        # 8.2 检查providers结构
        if "providers" in config and len(config["providers"]) > 0:
            provider = config["providers"][0]
            provider_fields = ["name", "base_url", "api_key", "models"]
            for field in provider_fields:
                if field in provider:
                    result.add_pass(f"服务商结构-{field}")
                else:
                    result.add_fail(f"服务商结构-{field}", "缺少")

    except FileNotFoundError:
        result.add_fail("配置文件", "文件不存在")
    except json.JSONDecodeError as e:
        result.add_fail("配置文件", f"JSON格式错误: {e}")
    except Exception as e:
        result.add_fail("配置文件", str(e))


def test_utils_module(result):
    """测试utils模块"""
    print("\n【9. Utils模块检查】")

    utils_path = os.path.join(PROJECT_ROOT, "utils.py")

    try:
        with open(utils_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键函数定义
        functions = [
            "load_config", "save_config", "load_custom_prompts",
            "save_custom_prompts", "scan_txt_files", "process_file",
            "save_response", "load_providers", "save_provider"
        ]

        for func in functions:
            pattern = rf'^def\s+{func}\s*\(|^{func}\s*='
            if re.search(pattern, content, re.MULTILINE):
                result.add_pass(f"函数-{func}")
            else:
                result.add_fail(f"函数-{func}", "未定义")
    except FileNotFoundError:
        result.add_fail("utils模块", "文件不存在")
    except Exception as e:
        result.add_fail("utils模块", str(e))


def main():
    """主函数"""
    print("\n" + "="*60)
    print(" AI Summary 项目 - 全面测试")
    print("="*60)
    print(f"测试地址: {BASE_URL}")
    print(f"项目路径: {PROJECT_ROOT}")

    result = TestResult()

    # 执行所有测试
    test_backend_basic(result)
    test_provider_management(result)
    test_prompt_management(result)
    test_config_selection(result)
    test_processing_status(result)
    test_javascript(result)
    test_template(result)
    test_config_file(result)
    test_utils_module(result)

    # 打印总结
    success = result.summary()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
