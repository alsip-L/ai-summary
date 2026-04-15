#!/bin/sh

# AI摘要应用 - 完全清理脚本

set -e

echo "=== AI摘要应用完全清理脚本 ==="
echo "⚠️  这将删除容器、镜像和相关文件"
echo "时间: $(date)"
echo

# 确认操作
echo "确定要完全清理所有AI摘要应用相关资源吗？"
echo "这将删除："
echo "  - 容器 ai-summary-container"
echo "  - 镜像 ai-summary-app:latest 和 ai-summary-app:alpine"
echo "  - 数据目录 (data/, output/, temp/)"
echo "  - docker-compose.alpine.yml 资源"
echo
echo "请输入 'YES' 确认操作: "
read -r confirmation

if [ "$confirmation" != "YES" ]; then
    echo "❌ 操作已取消"
    exit 0
fi

echo "🔄 开始清理..."

# 停止并移除容器
if docker ps -a | grep -q ai-summary-container; then
    echo "🛑 停止容器..."
    docker stop ai-summary-container 2>/dev/null || true
    
    echo "🗑️  移除容器..."
    docker rm ai-summary-container 2>/dev/null || true
    
    echo "✅ 容器已清理"
else
    echo "ℹ️  容器不存在"
fi

# 移除镜像
echo "🖼️  清理镜像..."
docker rmi ai-summary-app:latest 2>/dev/null || echo "ℹ️  镜像 ai-summary-app:latest 不存在"
docker rmi ai-summary-app:alpine 2>/dev/null || echo "ℹ️  镜像 ai-summary-app:alpine 不存在"

echo "✅ 镜像已清理"

# 清理docker-compose资源
echo "📋 清理docker-compose资源..."
docker-compose -f docker-compose.alpine.yml down --volumes --remove-orphans 2>/dev/null || true

# 清理数据目录
echo "📁 清理数据目录..."
for dir in data output temp; do
    if [ -d "$dir" ]; then
        echo "  删除目录: $dir/"
        rm -rf "$dir"
    fi
done

# 清理构建缓存
echo "🧹 清理构建缓存..."
docker system prune -f

echo
echo "✅ 清理完成！"
echo
echo "🔄 如果需要重新开始，请运行:"
echo "   ./build-alpine.sh    # 构建镜像"
echo "   ./run-alpine.sh      # 运行应用"
echo "   ./run-compose-alpine.sh # 使用docker-compose运行"