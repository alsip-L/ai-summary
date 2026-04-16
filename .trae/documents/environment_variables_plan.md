# 环境变量使用情况检查与处理计划

## 检查结果

### 环境变量使用情况

| 环境变量 | 定义位置 | 实际使用情况 |
|----------|----------|-------------|
| `DEBUG_LEVEL` | utils.py:14, core/logger.py:36 | ✅ **已使用** - 控制日志级别 |
| `FLASK_SECRET_KEY` | app.py:152 | ✅ **已使用** - Flask session 密钥 |
| `FLASK_ENV` | dockerfile:7, docker-compose.yml:12 | ❌ **未使用** - 代码中未读取 |
| `HOST` | run.py:15 | ✅ **已使用** - 服务主机地址 |
| `PORT` | run.py:16 | ✅ **已使用** - 服务端口 |
| `DEBUG` | run.py:17 | ✅ **已使用** - Flask debug 模式 |
| `PYTHONUNBUFFERED` | dockerfile:4, docker-compose.yml:14 | ✅ **已使用** - Docker 环境配置 |

### 问题分析

**FLASK_ENV 未被代码使用**：
- `dockerfile` 和 `docker-compose.yml` 中设置了 `FLASK_ENV=production`
- 但 `app.py` 中没有读取或使用这个环境变量
- `app.py:708` 直接从 `DEBUG_LEVEL` 环境变量读取，而不是使用 Flask 的 `FLASK_ENV`

## 处理方案

### 方案 A：在代码中实现 FLASK_ENV 支持（推荐）

修改 `app.py`，使其：
1. 读取 `FLASK_ENV` 环境变量
2. 当 `FLASK_ENV=production` 时，自动设置 `DEBUG=False`
3. 当 `FLASK_ENV=development` 时，自动设置 `DEBUG=True`
4. 保持向后兼容：`DEBUG_LEVEL` 仍然可以独立控制日志级别

### 方案 B：从文档中移除 FLASK_ENV 说明

如果不需要这个功能，可以从 README 中移除 `FLASK_ENV` 的说明。

## 实施计划（采用方案 A）

1. **修改 app.py**
   - 在 `app.py` 开头添加读取 `FLASK_ENV` 的逻辑
   - 当 `FLASK_ENV=development` 时启用 Flask debug 模式
   - 当 `FLASK_ENV=production` 时禁用 debug 模式
   - 保持 `DEBUG_LEVEL` 继续控制日志级别

2. **更新 README.md**
   - 修正环境变量说明表格
   - 明确说明 `FLASK_ENV` 的实际作用
   - 说明与 `DEBUG` 参数的关系

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app.py` | 编辑 | 添加 FLASK_ENV 支持 |
| `README.md` | 编辑 | 更新环境变量说明 |
