#!/bin/sh

# AI摘要应用 - Alpine Linux Docker构建脚本
# 适用于 aarch64 架构

set -e

echo "=== AI摘要应用 Docker 构建脚本 ==="
echo "目标平台: aarch64 (Alpine Linux)"
echo "时间: $(date)"
echo

# 检查Docker是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 错误: Docker 未安装或不在PATH中"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误: Docker服务未运行"
    echo "请启动Docker服务"
    exit 1
fi

echo "✅ Docker 已安装并运行"

# 检查架构
ARCH=$(uname -m)
echo "检测到系统架构: $ARCH"

if [ "$ARCH" != "aarch64" ]; then
    echo "⚠️  警告: 当前架构为 $ARCH，但目标部署平台为 aarch64"
    echo "如果在x86_64上构建，可能需要模拟运行"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data output temp

# 构建镜像
echo "🔨 开始构建Docker镜像..."
echo "使用的Dockerfile: Dockerfile.alpine"
echo "忽略文件: .dockerignore.alpine"

# 使用alpine专用的构建参数
docker build \
    --file Dockerfile.alpine \
    --tag ai-summary-app:latest \
    --tag ai-summary-app:alpine \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功!"
    echo
    echo "📊 镜像信息:"
    docker images ai-summary-app:latest
    echo
    echo "🚀 可以使用以下命令运行容器:"
    echo "   ./run-alpine.sh"
    echo
    echo "🔍 或者使用docker-compose:"
    echo "   docker-compose -f docker-compose.alpine.yml up -d"
else
    echo "❌ 镜像构建失败"
    exit 1
fi