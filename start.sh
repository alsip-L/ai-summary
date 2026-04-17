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
    echo '{"providers":[],"custom_prompts":{},"current_prompt":"","trash":{"providers":{},"custom_prompts":{}},"user_preferences":{},"system_settings":{"debug_level":"ERROR","flask_secret_key":"default-dev-secret-key-please-change-in-prod","host":"0.0.0.0","port":5000,"debug":false}}' > config.json
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
