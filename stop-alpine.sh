#!/bin/sh

# AI摘要应用 - 停止和清理脚本

set -e

echo "=== AI摘要应用停止脚本 ==="
echo "时间: $(date)"
echo

# 检查容器是否存在
if ! docker ps -a | grep -q ai-summary-container; then
    echo "ℹ️  容器 ai-summary-container 不存在"
    exit 0
fi

# 获取当前容器状态
CONTAINER_STATUS=$(docker inspect ai-summary-container --format='{{.State.Status}}' 2>/dev/null || echo "not_found")

echo "📊 当前容器状态: $CONTAINER_STATUS"

case "$CONTAINER_STATUS" in
    "running")
        echo "🔄 正在停止容器..."
        docker stop ai-summary-container
        echo "✅ 容器已停止"
        ;;
    "exited")
        echo "✅ 容器已停止"
        ;;
    "not_found")
        echo "ℹ️  容器不存在"
        exit 0
        ;;
    *)
        echo "⚠️  容器状态异常: $CONTAINER_STATUS"
        ;;
esac

echo
echo "🔧 可选操作:"
echo "1. 查看日志: docker logs ai-summary-container"
echo "2. 重新启动: ./run-alpine.sh"
echo "3. 完全清理: ./cleanup-alpine.sh"
echo

# 询问是否要清理
echo "是否要完全移除容器和镜像? (y/N)"
read -r response
case "$response" in
    [Yy]|[Yy][Ee][Ss]|[Yy][Ee])
        echo "🧹 开始清理..."
        ./cleanup-alpine.sh
        ;;
    *)
        echo "操作完成"
        ;;
esac