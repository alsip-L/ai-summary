#!/bin/sh

# AI摘要应用 - Alpine Linux Docker运行脚本
# 适用于 aarch64 架构

set -e

echo "=== AI摘要应用 Docker 运行脚本 ==="
echo "目标平台: aarch64 (Alpine Linux)"
echo "时间: $(date)"
echo

# 检查Docker是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 错误: Docker 未安装或不在PATH中"
    exit 1
fi

# 检查镜像是否存在
if ! docker images ai-summary-app:latest | grep -q ai-summary-app; then
    echo "❌ 错误: 未找到镜像 ai-summary-app:latest"
    echo "请先运行构建脚本: ./build-alpine.sh"
    exit 1
fi

echo "✅ 找到镜像 ai-summary-app:latest"

# 检查是否已经有容器在运行
if docker ps | grep -q ai-summary-container; then
    echo "⚠️  检测到容器 ai-summary-container 已在运行"
    echo "是否要重启容器? (y/N)"
    read -r response
    case "$response" in
        [Yy]|[Yy][Ee][Ss]|[Yy][Ee])
            echo "🔄 重启容器..."
            docker restart ai-summary-container
            ;;
        *)
            echo "保持现有容器运行"
            ;;
    esac
fi

# 检查容器是否已存在但未运行
if docker ps -a | grep -q ai-summary-container; then
    echo "🔄 启动现有容器..."
    docker start ai-summary-container
else
    echo "🚀 创建并启动新容器..."
    
    # 创建必要的目录
    mkdir -p data output temp
    
    # 运行容器
    echo "运行命令:"
    echo "docker run -d \\"
    echo "  --name ai-summary-container \\"
    echo "  --restart unless-stopped \\"
    echo "  -p 5000:5000 \\"
    echo "  -v \\$(pwd)/config.json:/app/config.json:ro \\"
    echo "  -v \\$(pwd)/data:/app/data \\"
    echo "  -v \\$(pwd)/output:/app/output \\"
    echo "  -v \\$(pwd)/temp:/app/temp \\"
    echo "  -e FLASK_ENV=production \\"
    echo "  -e PYTHONUNBUFFERED=1 \\"
    echo "  ai-summary-app:latest"
    echo
    
    docker run -d \
        --name ai-summary-container \
        --restart unless-stopped \
        -p 5000:5000 \
        -v "$(pwd)/config.json:/app/config.json:ro" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/temp:/app/temp" \
        -e FLASK_ENV=production \
        -e PYTHONUNBUFFERED=1 \
        ai-summary-app:latest
fi

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 5

# 检查容器状态
echo "📊 容器状态:"
docker ps --filter name=ai-summary-container --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 检查应用是否正常响应
echo "🔍 测试应用响应..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/ >/dev/null 2>&1; then
        echo "✅ 应用已成功启动并响应!"
        echo "🌐 访问地址: http://localhost:5000"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ 等待应用启动... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  应用可能启动较慢，请稍后访问 http://localhost:5000"
    echo "💡 查看日志: docker logs ai-summary-container"
fi

echo
echo "🔧 常用命令:"
echo "  查看日志:    docker logs -f ai-summary-container"
echo "  停止容器:    docker stop ai-summary-container"
echo "  重启容器:    docker restart ai-summary-container"
echo "  进入容器:    docker exec -it ai-summary-container sh"
echo "  移除容器:    docker rm -f ai-summary-container"