# -*- coding: utf-8 -*-
"""完整功能测试脚本 v2"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:5000"

def test_all():
    """运行所有测试"""
    print("\n" + "="*60)
    print(" AI Summary 完整功能测试 v2")
    print("="*60)

    results = []

    # ===== 1. 主页和基础 =====
    print("\n【1. 主页和基础功能】")

    # 1.1 主页加载
    print("  1.1 主页加载...")
    try:
        r = requests.get(BASE_URL + "/", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        assert 'AI' in r.text, "页面内容异常"
        print("    ✅ 主页加载成功")
        results.append(("主页加载", True))
    except Exception as e:
        print(f"    ❌ 主页加载失败: {e}")
        results.append(("主页加载", False))

    # 1.2 静态资源
    print("  1.2 静态资源(CSS/JS)...")
    try:
        r_css = requests.get(BASE_URL + "/static/style.css", timeout=5)
        r_js = requests.get(BASE_URL + "/static/script.js", timeout=5)
        assert r_css.status_code == 200, f"CSS状态码{r_css.status_code}"
        assert r_js.status_code == 200, f"JS状态码{r_js.status_code}"
        print("    ✅ 静态资源加载成功")
        results.append(("静态资源", True))
    except Exception as e:
        print(f"    ❌ 静态资源失败: {e}")
        results.append(("静态资源", False))

    # ===== 2. 服务商管理 =====
    print("\n【2. 服务商管理】")

    # 2.1 新增服务商
    print("  2.1 新增服务商...")
    try:
        ts = int(time.time())
        name = f"Provider_{ts}"
        data = {
            "form_type": "save_provider_form",
            "provider_name": name,
            "base_url": "https://api.test.com",
            "api_key_for_save": "sk-key-123",
            "models": json.dumps({"模型A": "model-a"})
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        print(f"    ✅ 新增服务商 '{name}' 成功")
        results.append(("新增服务商", True))
    except Exception as e:
        print(f"    ❌ 新增服务商失败: {e}")
        results.append(("新增服务商", False))

    # 2.2 更新API Key
    print("  2.2 更新API Key...")
    try:
        data = {
            "form_type": "save_api_key_form",
            "provider_name_for_key": name,
            "api_key_for_save": "sk-new-key-456"
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        print("    ✅ API Key更新成功")
        results.append(("更新API Key", True))
    except Exception as e:
        print(f"    ❌ API Key更新失败: {e}")
        results.append(("更新API Key", False))

    # 2.3 删除服务商
    print("  2.3 删除服务商...")
    try:
        data = {
            "form_type": "delete_provider_form",
            "provider_name_to_delete": name
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        print(f"    ✅ 删除服务商 '{name}' 成功")
        results.append(("删除服务商", True))
    except Exception as e:
        print(f"    ❌ 删除服务商失败: {e}")
        results.append(("删除服务商", False))

    # ===== 3. Prompt管理 =====
    print("\n【3. Prompt管理】")

    # 3.1 新增Prompt
    print("  3.1 新增Prompt...")
    try:
        ts = int(time.time())
        pname = f"Prompt_{ts}"
        data = {
            "form_type": "save_prompt_form",
            "prompt_name": pname,
            "prompt_content": "请总结以下内容"
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        print(f"    ✅ 新增Prompt '{pname}' 成功")
        results.append(("新增Prompt", True))
    except Exception as e:
        print(f"    ❌ 新增Prompt失败: {e}")
        results.append(("新增Prompt", False))

    # 3.2 删除Prompt
    print("  3.2 删除Prompt...")
    try:
        data = {
            "form_type": "delete_prompt_form",
            "prompt_name_to_delete": pname
        }
        r = requests.post(BASE_URL + "/", data=data, allow_redirects=False, timeout=5)
        assert r.status_code == 302, f"状态码{r.status_code}"
        print(f"    ✅ 删除Prompt '{pname}' 成功")
        results.append(("删除Prompt", True))
    except Exception as e:
        print(f"    ❌ 删除Prompt失败: {e}")
        results.append(("删除Prompt", False))

    # ===== 4. 配置选择 =====
    print("\n【4. 配置选择】")

    # 4.1 保存配置选择
    print("  4.1 保存配置选择...")
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
        print("    ✅ 配置选择保存成功")
        results.append(("保存配置选择", True))
    except Exception as e:
        print(f"    ❌ 配置选择保存失败: {e}")
        results.append(("保存配置选择", False))

    # ===== 5. 处理状态API =====
    print("\n【5. 处理状态API】")

    # 5.1 获取处理状态
    print("  5.1 获取处理状态...")
    try:
        r = requests.get(BASE_URL + "/get_processing_status", timeout=5)
        assert r.status_code == 200, f"状态码{r.status_code}"
        data = r.json()
        assert 'status' in data, "响应数据异常"
        print(f"    ✅ 状态: {data.get('status')}")
        results.append(("获取处理状态", True))
    except Exception as e:
        print(f"    ❌ 获取处理状态失败: {e}")
        results.append(("获取处理状态", False))

    # 5.2 取消处理（空闲状态）
    print("  5.2 取消处理...")
    try:
        r = requests.post(BASE_URL + "/cancel_processing", timeout=5)
        # 空闲状态取消会返回400，但请求成功
        assert r.status_code in [200, 400], f"状态码{r.status_code}"
        print(f"    ✅ 取消请求已处理 (状态码:{r.status_code})")
        results.append(("取消处理", True))
    except Exception as e:
        print(f"    ❌ 取消处理失败: {e}")
        results.append(("取消处理", False))

    # ===== 6. 文件和目录 =====
    print("\n【6. 文件和目录】")

    # 6.1 创建测试目录和文件
    print("  6.1 创建测试目录和文件...")
    try:
        test_dir = "C:/TestTxt"
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("这是测试文件内容。")
        print(f"    ✅ 创建测试目录和文件: {test_file}")
        results.append(("创建测试文件", True))
    except Exception as e:
        print(f"    ❌ 创建测试文件失败: {e}")
        results.append(("创建测试文件", False))

    # ===== 7. 清理测试数据 =====
    print("\n【7. 清理测试数据】")
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)
        print("    ✅ 清理测试数据成功")
        results.append(("清理测试数据", True))
    except Exception as e:
        print(f"    ❌ 清理测试数据失败: {e}")
        results.append(("清理测试数据", False))

    # ===== 总结 =====
    print("\n" + "="*60)
    print(" 测试结果总结")
    print("="*60)

    passed = 0
    failed = 0
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {name}: {status}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n通过: {passed}/{len(results)}")
    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {failed} 个测试失败")

    return failed == 0

if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
