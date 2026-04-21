# AI Summary SDK

AI Summary 服务的 Python SDK 客户端，提供类型安全的 API 调用接口。

## 安装

```bash
pip install ai-summary-sdk
```

## 快速入门

### 同步客户端

```python
from ai_summary_sdk import AISummaryClient

# 创建客户端
with AISummaryClient(base_url="http://localhost:5000") as client:
    # 列出所有提供商
    providers = client.providers.list()

    # 创建提供商
    client.providers.create(
        name="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-xxx",
        models_map={"GPT-4": "gpt-4"},
    )

    # 创建提示词
    client.prompts.create(name="摘要生成", content="请对以下文本生成摘要。")

    # 启动处理任务
    client.tasks.start(
        provider="openai",
        model="gpt-4",
        api_key="sk-xxx",
        prompt="摘要生成",
        directory="C:/data/texts",
    )

    # 查询任务状态
    status = client.tasks.status()
    print(status)
```

### 异步客户端

```python
import asyncio
from ai_summary_sdk import AsyncAISummaryClient

async def main():
    async with AsyncAISummaryClient(base_url="http://localhost:5000") as client:
        providers = await client.providers.list()
        status = await client.tasks.status()
        print(providers, status)

asyncio.run(main())
```

### 环境变量配置

```bash
export AI_SUMMARY_BASE_URL="http://localhost:5000"
export AI_SUMMARY_API_KEY="your-api-key"
```

设置环境变量后，可无参创建客户端：

```python
from ai_summary_sdk import AISummaryClient

with AISummaryClient() as client:
    providers = client.providers.list()
```

## API 参考

### 提供商 (providers)

| 方法 | 说明 |
|------|------|
| `client.providers.list()` | 列出所有活跃提供商 |
| `client.providers.create(name, base_url, api_key, models_map, is_active)` | 创建提供商 |
| `client.providers.delete(name)` | 删除提供商（移入回收站） |
| `client.providers.update_api_key(name, api_key)` | 更新 API Key |
| `client.providers.add_model(name, display_name, model_id)` | 添加模型 |
| `client.providers.delete_model(name, model_name)` | 删除模型 |

### 提示词 (prompts)

| 方法 | 说明 |
|------|------|
| `client.prompts.list()` | 列出所有提示词 |
| `client.prompts.create(name, content)` | 创建提示词 |
| `client.prompts.delete(name)` | 删除提示词（移入回收站） |

### 任务 (tasks)

| 方法 | 说明 |
|------|------|
| `client.tasks.start(provider, model, api_key, prompt, directory, skip_existing)` | 启动处理任务 |
| `client.tasks.status()` | 获取当前任务状态 |
| `client.tasks.cancel()` | 取消当前任务 |
| `client.tasks.get_failed()` | 获取失败记录 |
| `client.tasks.clear_failed()` | 清除失败记录 |
| `client.tasks.retry_failed(provider, model, api_key, prompt)` | 重试失败记录 |

### 文件 (files)

| 方法 | 说明 |
|------|------|
| `client.files.drives()` | 获取可用驱动器 |
| `client.files.directory(path)` | 获取目录内容 |
| `client.files.result(path)` | 查看处理结果 |

### 回收站 (trash)

| 方法 | 说明 |
|------|------|
| `client.trash.list()` | 获取回收站内容 |
| `client.trash.restore_provider(name)` | 恢复提供商 |
| `client.trash.restore_prompt(name)` | 恢复提示词 |
| `client.trash.delete_provider(name)` | 永久删除提供商 |
| `client.trash.delete_prompt(name)` | 永久删除提示词 |

### 设置 (settings)

| 方法 | 说明 |
|------|------|
| `client.settings.get_preferences()` | 获取用户偏好 |
| `client.settings.update_preferences(**kwargs)` | 更新用户偏好 |

## 错误处理

SDK 提供统一的异常层次结构：

```python
from ai_summary_sdk import AISummaryClient, APIError, ValidationError, NotFoundError

with AISummaryClient(base_url="http://localhost:5000") as client:
    try:
        client.providers.delete("non-existent")
    except NotFoundError as e:
        print(f"资源不存在: {e.message}")
    except ValidationError as e:
        print(f"参数错误: {e.message}, 字段: {e.field}")
    except APIError as e:
        print(f"API 错误: HTTP {e.status_code}, 可重试: {e.retryable}")
```

### 异常类型

| 异常 | 说明 |
|------|------|
| `AISummarySDKError` | SDK 基础异常 |
| `ConnectionError` | 服务不可达或网络异常 |
| `AuthenticationError` | API Key 无效或缺失 |
| `ValidationError` | 请求参数不合法或响应校验失败 |
| `APIError` | 服务端返回非 2xx 状态码 |
| `NotFoundError` | 资源不存在 (HTTP 404) |

## 重试配置

```python
from ai_summary_sdk import AISummaryClient

# 自定义重试配置
with AISummaryClient(
    base_url="http://localhost:5000",
    max_retries=5,      # 最大重试次数
    retry_delay=2.0,    # 基础退避延迟（秒）
) as client:
    providers = client.providers.list()
```

SDK 对可重试错误（HTTP 503、网络超时）自动进行指数退避重试。
