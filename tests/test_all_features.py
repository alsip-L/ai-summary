# -*- coding: utf-8 -*-
"""完整功能测试脚本"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_homepage():
    """测试主页加载"""
    print("\n" + "="*50)
    print("测试1: 主页加载")
    print("="*50)
    response = requests.get(BASE_URL + "/")
    print(f"状态码: {response.status_code}")
    print(f"页面长度: {len(response.text)} 字节")
    assert response.status_code == 200, "主页加载失败"
    # 检查页面包含关键元素
    assert 'AI批量总结' in response.text or 'AI Summary' in response.text, "主页内容不正确"
    print("✅ 主页加载成功")
    return True

def test_processing_status():
    """测试处理状态API"""
    print("\n" + "="*50)
    print("测试2: 处理状态API")
    print("="*50)
    response = requests.get(BASE_URL + "/get_processing_status")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应数据: {data}")
    assert response.status_code == 200, "处理状态API失败"
    print("✅ 处理状态API成功")
    return True

def test_add_provider():
    """测试新增服务商"""
    print("\n" + "="*50)
    print("测试3: 新增服务商")
    print("="*50)

    # 生成唯一的名称
    timestamp = int(time.time())
    provider_name = f"TestProvider_{timestamp}"

    data = {
        "form_type": "save_provider_form",
        "provider_name": provider_name,
        "base_url": "https://api.test.com/v1",
        "api_key_for_save": "sk-test-key-12345",
        "models": json.dumps({"测试模型": "test-model-001"})
    }

    response = requests.post(BASE_URL + "/", data=data, allow_redirects=False)
    print(f"状态码: {response.status_code}")
    print(f"重定向: {response.headers.get('Location', 'None')}")

    assert response.status_code == 302, f"新增服务商失败，状态码: {response.status_code}"
    print(f"✅ 新增服务商 '{provider_name}' 成功")

    # 验证配置已更新
    response = requests.get(BASE_URL + "/")
    assert provider_name in response.text, "服务商未出现在下拉列表中"
    print(f"✅ 服务商 '{provider_name}' 出现在主页中")
    return True

def test_add_prompt():
    """测试新增提示词"""
    print("\n" + "="*50)
    print("测试4: 新增提示词")
    print("="*50)

    timestamp = int(time.time())
    prompt_name = f"测试提示词_{timestamp}"
    prompt_content = "请总结以下文本的内容，提取关键信息。"

    data = {
        "form_type": "save_prompt_form",  # 注意：这里用 save_prompt_form
        "prompt_name": prompt_name,
        "prompt_content": prompt_content
    }

    response = requests.post(BASE_URL + "/", data=data, allow_redirects=False)
    print(f"状态码: {response.status_code}")
    print(f"重定向: {response.headers.get('Location', 'None')}")

    assert response.status_code == 302, f"新增提示词失败，状态码: {response.status_code}"
    print(f"✅ 新增提示词 '{prompt_name}' 成功")
    return True

def test_delete_provider():
    """测试删除服务商"""
    print("\n" + "="*50)
    print("测试5: 删除服务商")
    print("="*50)

    # 先添加一个待删除的服务商
    timestamp = int(time.time())
    provider_name = f"ToDelete_{timestamp}"

    # 添加
    add_data = {
        "form_type": "save_provider_form",
        "provider_name": provider_name,
        "base_url": "https://api.delete.com",
        "api_key_for_save": "sk-delete",
        "models": json.dumps({"删除模型": "del-model"})
    }
    response = requests.post(BASE_URL + "/", data=add_data, allow_redirects=False)
    print(f"添加服务商状态码: {response.status_code}")

    # 删除
    delete_data = {
        "form_type": "delete_provider_form",
        "provider_name_to_delete": provider_name
    }
    response = requests.post(BASE_URL + "/", data=delete_data, allow_redirects=False)
    print(f"删除服务商状态码: {response.status_code}")
    print(f"重定向: {response.headers.get('Location', 'None')}")

    assert response.status_code == 302, f"删除服务商失败，状态码: {response.status_code}"
    print(f"✅ 删除服务商 '{provider_name}' 成功")
    return True

def test_config_selection():
    """测试配置选择（保存目录路径等）"""
    print("\n" + "="*50)
    print("测试6: 配置选择保存")
    print("="*50)

    data = {
        "form_type": "config_selection_form",
        "selected_provider": "Test",
        "selected_model": "默认模型",
        "selected_prompt": "",
        "directory_path": "C:/Test/TxtFiles",
        "auto_save": "true"
    }

    response = requests.post(BASE_URL + "/", data=data, allow_redirects=False)
    print(f"状态码: {response.status_code}")
    print(f"重定向: {response.headers.get('Location', 'None')}")

    assert response.status_code == 302, f"配置选择保存失败，状态码: {response.status_code}"
    print("✅ 配置选择保存成功")
    return True

def test_static_files():
    """测试静态文件"""
    print("\n" + "="*50)
    print("测试7: 静态文件")
    print("="*50)

    # 测试 CSS
    response = requests.get(BASE_URL + "/static/style.css")
    print(f"CSS 状态码: {response.status_code}")
    assert response.status_code == 200, "CSS加载失败"

    # 测试 JS
    response = requests.get(BASE_URL + "/static/script.js")
    print(f"JS 状态码: {response.status_code}")
    assert response.status_code == 200, "JS加载失败"

    print("✅ 静态文件加载成功")
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print(" AI Summary 完整功能测试")
    print("="*60)

    tests = [
        ("主页加载", test_homepage),
        ("处理状态API", test_processing_status),
        ("新增服务商", test_add_provider),
        ("新增提示词", test_add_prompt),
        ("删除服务商", test_delete_provider),
        ("配置选择保存", test_config_selection),
        ("静态文件", test_static_files),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ 通过" if result else "❌ 失败"))
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            results.append((name, f"❌ 错误: {e}"))

    # 打印总结
    print("\n" + "="*60)
    print(" 测试结果总结")
    print("="*60)
    for name, result in results:
        print(f"{name}: {result}")

    passed = sum(1 for _, r in results if "通过" in r)
    total = len(results)
    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")

if __name__ == "__main__":
    run_all_tests()
