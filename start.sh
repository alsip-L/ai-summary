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
    if [ -f "config.example.json" ]; then
        echo "配置文件不存在，从 config.example.json 复制..."
        cp config.example.json config.json
        echo "已从示例创建配置 - 请编辑 config.json 填入实际设置"
    else
        echo "配置文件不存在，创建默认配置..."
        echo '{"system_settings":{"debug_level":"ERROR","secret_key":"default-dev-secret-key-please-change-in-prod","host":"0.0.0.0","port":5000,"debug":false}}' > config.json
        echo "默认配置已创建"
    fi
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

# 等待健康检查通过
echo "等待服务就绪..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' ai-summary-container 2>/dev/null)
    if [ "$STATUS" = "healthy" ]; then
        echo "服务已就绪 (耗时 ${WAITED}s)"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "警告：服务未在 ${MAX_WAIT}s 内就绪，请检查日志：$COMPOSE_CMD logs -f"
fi

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
echo "  查看状态：docker inspect --format='{{.State.Health.Status}}' ai-summary-container"
echo
