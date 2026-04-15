#!/bin/bash

echo "================================"
echo "Docker 配置验证脚本"
echo "================================"
echo

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装Docker"
    exit 1
fi

echo "✅ Docker 已安装: $(docker --version)"
echo

# 检查Docker Compose是否安装
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose 已安装: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose 已安装 (Docker插件版本)"
else
    echo "⚠️ Docker Compose 未安装，某些功能可能不可用"
fi
echo

# 检查项目文件
echo "检查项目文件..."
files=("Dockerfile" "docker-compose.yml" "requirements.txt" "app.py" "config.json")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
    fi
done
echo

echo "================================"
echo "验证完成！"
echo "================================"
echo
echo "运行应用："
echo "  Windows: run-docker.bat"
echo "  Linux/Mac: ./run-docker.sh"
echo "  或使用: docker-compose up -d"
echo