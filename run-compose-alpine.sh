#!/bin/sh

# AI摘要应用 - Docker Compose运行脚本 (Alpine版本)

set -e

echo "=== AI摘要应用 Docker Compose 运行脚本 ==="
echo "目标平台: aarch64 (Alpine Linux)"
echo "时间: $(date)"
echo

# 检查Docker和docker-compose是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 错误: Docker 未安装"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ 错误: docker-compose 未安装"
    echo "请安装docker-compose或使用较新版本的Docker (内置compose插件)"
    exit 1
fi

echo "✅ Docker 和 docker-compose 已就绪"

# 检查镜像是否存在
if ! docker images ai-summary-app:latest | grep -q ai-summary-app; then
    echo "⚠️  未找到镜像 ai-summary-app:latest"
    echo "正在构建镜像..."
    ./build-alpine.sh
fi

# 检查compose文件是否存在
if [ ! -f "docker-compose.alpine.yml" ]; then
    echo "❌ 错误: 找不到 docker-compose.alpine.yml"
    exit 1
fi

echo "✅ 找到配置文件: docker-compose.alpine.yml"

# 检查是否已有容器运行
if docker-compose -f docker-compose.alpine.yml ps | grep -q "Up"; then
    echo "⚠️  检测到服务已在运行"
    echo "当前状态:"
    docker-compose -f docker-compose.alpine.yml ps
    echo
    echo "选择操作:"
    echo "1. 重启服务 (r)"
    echo "2. 查看日志 (l)"
    echo "3. 退出 (q)"
    read -p "请选择 (1/r/l/q): " -r response
    
    case "$response" in
        1|[Rr])
            echo "🔄 重启服务..."
            docker-compose -f docker-compose.alpine.yml restart
            ;;
        [Ll])
            echo "📋 查看日志:"
            docker-compose -f docker-compose.alpine.yml logs -f
            exit 0
            ;;
        [Qq]|"")
            echo "操作取消"
            exit 0
            ;;
    esac
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data output temp

echo "🚀 启动服务..."
docker-compose -f docker-compose.alpine.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 服务状态:"
docker-compose -f docker-compose.alpine.yml ps

# 测试应用响应
echo "🔍 测试应用响应..."
MAX_RETRIES=15
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/ >/dev/null 2>&1; then
        echo "✅ 应用已成功启动并响应!"
        echo "🌐 访问地址: http://localhost:5000"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ 等待应用启动... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  应用可能启动较慢，请稍后访问 http://localhost:5000"
fi

echo
echo "🔧 常用命令:"
echo "  查看日志:    docker-compose -f docker-compose.alpine.yml logs -f"
echo "  停止服务:    docker-compose -f docker-compose.alpine.yml down"
echo "  重启服务:    docker-compose -f docker-compose.alpine.yml restart"
echo "  进入容器:    docker-compose -f docker-compose.alpine.yml exec ai-summary-app sh"