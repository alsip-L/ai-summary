@echo off
chcp 65001 >nul
title AI摘要应用 - Alpine Docker构建脚本 (Windows)

echo === AI摘要应用 Docker 构建脚本 (Windows) ===
echo 目标平台: aarch64 (Alpine Linux)
echo 时间: %DATE% %TIME%
echo.

REM 检查Docker是否安装
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误: Docker 未安装或不在PATH中
    echo 请先安装Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM 检查Docker服务是否运行
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误: Docker服务未运行
    echo 请启动Docker服务
    pause
    exit /b 1
)

echo ✅ Docker 已安装并运行

REM 检查架构
echo 检测到系统架构: %PROCESSOR_ARCHITECTURE%

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist data mkdir data
if not exist output mkdir output
if not exist temp mkdir temp

REM 构建镜像
echo 🔨 开始构建Docker镜像...
echo 使用的Dockerfile: Dockerfile.alpine
echo 忽略文件: .dockerignore.alpine

docker build ^
    --file Dockerfile.alpine ^
    --tag ai-summary-app:latest ^
    --tag ai-summary-app:alpine ^
    --build-arg BUILDKIT_INLINE_CACHE=1 ^
    .

if %ERRORLEVEL% equ 0 (
    echo ✅ 镜像构建成功!
    echo.
    echo 📊 镜像信息:
    docker images ai-summary-app:latest
    echo.
    echo 🚀 可以使用以下命令运行容器:
    echo    run-alpine.bat
    echo.
    echo 🔍 或者使用docker-compose:
    echo    docker-compose -f docker-compose.alpine.yml up -d
) else (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)

pause