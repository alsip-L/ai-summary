# AI Summary 项目 - 重新生成 Windows 启动与 Linux Docker Compose 部署计划

## 目标

重新生成项目的 Windows 启动脚本和 Linux Docker Compose 部署文件。

***

## 重新生成内容

### 1. Windows 本地启动脚本

**文件**: `start.bat`

创建 Windows 本地启动脚本（不使用 Docker）：

```batch
@echo off
chcp 65001 >nul
echo ================================
echo AI Summary 本地启动脚本
echo ================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误：未检测到 Python，请先安装 Python 3.11 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 已安装
python --version
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 发现虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo 未找到虚拟环境，使用系统 Python
)

REM 检查依赖
echo.
echo 检查依赖...
pip show flask >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 依赖未安装，正在安装...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
    echo 依赖安装完成
) else (
    echo 依赖已安装
)

REM 创建必要目录
echo.
echo 创建必要目录...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "output" mkdir output
echo 目录创建完成

REM 检查配置文件
echo.
echo 检查配置文件...
if not exist "config.json" (
    echo 配置文件不存在，创建默认配置...
    echo {"providers":[],"current_provider":{},"custom_prompts":{},"current_prompt":"","file_paths":{"input":"","output":""},"trash":{"providers":[],"custom_prompts":{}}} > config.json
    echo 默认配置已创建
) else (
    echo 配置文件已存在
)

REM 启动应用
echo.
echo ================================
echo 启动 AI Summary 应用...
echo ================================
echo.
echo 访问地址：http://localhost:5000
echo 按 Ctrl+C 停止应用
echo.

python run.py

REM 退出时暂停
echo.
echo 应用已停止
echo.
pause
```

***

### 2. Linux Docker Compose 部署

#### 更新 docker-compose.yml

**文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  ai-summary-app:
    build:
      context: .
      dockerfile: dockerfile
    container_name: ai-summary-container
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app.py
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=5000
    volumes:
      - ./config.json:/app/config.json
      - ./data:/app/data
      - ./logs:/app/logs
      - ./output:/app/output
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ai-summary-network

networks:
  ai-summary-network:
    driver: bridge
```

#### 更新 dockerfile

**文件**: `dockerfile`

添加 curl 用于健康检查，创建 logs 目录：

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    FLASK_APP=app.py \
    FLASK_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs /app/output

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

#### 创建 Linux 启动脚本

**文件**: `start.sh`

```bash
#!/bin/bash

export LANG=en_US.UTF-8

echo "================================"
echo "AI Summary Docker Compose 启动脚本"
echo "================================"
echo

# 检查 Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "错误：未检测到 Docker Compose"
    exit 1
fi

echo "Docker Compose 已安装"
echo

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data logs output
echo "目录创建完成"
echo

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "配置文件不存在，创建默认配置..."
    echo '{"providers":[],"current_provider":{},"custom_prompts":{},"current_prompt":"","file_paths":{"input":"","output":""},"trash":{"providers":[],"custom_prompts":{}}}' > config.json
    echo "默认配置已创建"
    echo
fi

# 启动服务
echo "启动 Docker Compose 服务..."
$COMPOSE_CMD up -d --build
if [ $? -ne 0 ]; then
    echo "服务启动失败"
    exit 1
fi

echo "服务启动成功"
echo
echo "================================"
echo "应用已成功启动！"
echo "================================"
echo
echo "应用访问地址：http://localhost:5000"
echo
echo "常用命令："
echo "  查看日志：$COMPOSE_CMD logs -f"
echo "  停止服务：$COMPOSE_CMD down"
echo "  重启服务：$COMPOSE_CMD restart"
echo
```

***

## 文件变更清单

### 新增/更新文件

* `start.bat` - Windows 本地启动脚本（新增）

* `docker-compose.yml` - Linux Docker Compose 配置（更新）

* `dockerfile` - Docker 构建文件（更新）

* `start.sh` - Linux Docker Compose 启动脚本（新增）

### 使用方式

**Windows 本地启动：**

```batch
start.bat
```

**Linux Docker Compose 部署：**

```bash
./start.sh
```

或手动
