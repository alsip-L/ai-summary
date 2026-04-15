#!/bin/bash

echo "================================"
echo "AI Summary Docker 运行脚本"
echo "================================"
echo

echo "1. 构建Docker镜像..."
docker build -t ai-summary-app .

echo
echo "2. 创建必要的目录..."
mkdir -p data logs

echo
echo "3. 停止并删除现有容器（如果存在）..."
docker stop ai-summary-container 2>/dev/null || true
docker rm ai-summary-container 2>/dev/null || true

echo
echo "4. 运行Docker容器..."
docker run -d \
  --name ai-summary-container \
  -p 5000:5000 \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  -e FLASK_ENV=production \
  -e FLASK_APP=app.py \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  ai-summary-app

echo
echo "5. 检查容器状态..."
docker ps | grep ai-summary-container

echo
if [ $? -eq 0 ]; then
    echo "================================"
    echo "🎉 应用已成功启动！"
    echo "================================"
    echo
    echo "应用访问地址：http://localhost:5000"
    echo
    echo "常用命令："
    echo "  查看日志：docker logs ai-summary-container"
    echo "  停止应用：docker stop ai-summary-container"
    echo "  删除应用：docker rm -f ai-summary-container"
    echo "  重新构建：docker build -t ai-summary-app ."
    echo
else
    echo "❌ 应用启动失败！"
    echo "请检查错误信息并重试。"
    echo
    echo "查看错误日志："
    echo "docker logs ai-summary-container"
fi