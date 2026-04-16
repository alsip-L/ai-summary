# Docker部署指南

本指南将帮助您使用Docker快速部署AI文档摘要处理应用。

## 项目结构

```
ai-summary-docker1/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置
├── .dockerignore          # Docker忽略文件
├── run-docker.bat         # Windows运行脚本
├── run-docker.sh          # Linux/Mac运行脚本
├── requirements.txt       # Python依赖
├── app.py                # Flask主应用
├── utils.py              # 工具函数
├── config.json           # 配置文件
├── templates/            # HTML模板
└── static/              # 静态文件
```

## 快速开始

### 方法一：使用运行脚本（推荐）

#### Windows用户
1. 双击运行 `run-docker.bat`
2. 按照提示完成部署

#### Linux/Mac用户
```bash
chmod +x run-docker.sh
./run-docker.sh
```

### 方法二：使用Docker Compose（推荐）

```bash
# 构建并启动应用
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止应用
docker-compose down
```

### 方法三：手动Docker命令

```bash
# 1. 构建镜像
docker build -t ai-summary-app .

# 2. 创建目录
mkdir data logs

# 3. 运行容器
docker run -d \
  --name ai-summary-container \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e FLASK_ENV=production \
  -e FLASK_APP=app.py \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  ai-summary-app
```

## 访问应用

部署成功后，在浏览器中访问：**http://localhost:5000**

## 常用Docker命令

### 容器管理
```bash
# 查看容器状态
docker ps

# 查看容器日志
docker logs ai-summary-container

# 实时查看日志
docker logs -f ai-summary-container

# 重启容器
docker restart ai-summary-container

# 停止容器
docker stop ai-summary-container

# 删除容器
docker rm -f ai-summary-container
```

### 镜像管理
```bash
# 查看镜像
docker images

# 删除镜像
docker rmi ai-summary-app

# 重新构建镜像
docker build -t ai-summary-app .
```

### 数据持久化
- **配置数据**: `config.json` 文件会被挂载到容器内，支持热更新
- **处理结果**: `data/` 目录存储生成的markdown文件
- **日志文件**: `logs/` 目录存储应用日志

## 配置管理

所有配置均通过 `config.json` 文件或 Web 界面管理，无需使用环境变量。在 Web 界面的 **系统设置** 面板中可以修改日志级别、Flask密钥、监听地址和端口等。

### 日志级别
在 Web 界面的系统设置中选择日志级别，修改后即时生效，无需重启容器。

### 端口和地址
如需修改监听端口或地址，在 Web 界面的系统设置中修改后，需要重启容器：
```bash
docker restart ai-summary-container
```

或直接修改 `docker-compose.yml` 中的端口映射。

## 网络和端口配置

- **默认端口**: 5000
- **容器端口**: 5000
- **主机端口**: 5000

如需更改端口，修改运行命令中的 `-p` 参数：
```bash
-p 8080:5000  # 访问时使用 http://localhost:8080
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tulpn | grep :5000
   
   # 停止占用端口的进程或更换端口
   ```

2. **权限问题**
   ```bash
   # Linux/Mac设置脚本权限
   chmod +x run-docker.sh
   
   # 检查文件权限
   ls -la
   ```

3. **Docker构建失败**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   
   # 重新构建
   docker build --no-cache -t ai-summary-app .
   ```

4. **容器启动失败**
   ```bash
   # 查看详细错误日志
   docker logs ai-summary-container
   
   # 进入容器调试
   docker exec -it ai-summary-container /bin/bash
   ```

### 调试命令

```bash
# 检查容器健康状态
docker inspect ai-summary-container

# 进入容器内部
docker exec -it ai-summary-container /bin/bash

# 查看容器资源使用
docker stats ai-summary-container

# 查看容器网络
docker network ls
docker network inspect bridge
```

## 生产环境部署建议

1. **安全配置**
   - 修改默认Flask密钥
   - 使用HTTPS
   - 配置防火墙规则

2. **性能优化**
   - 调整worker进程数量
   - 配置负载均衡
   - 使用Redis等缓存

3. **监控和日志**
   - 配置日志聚合
   - 设置监控告警
   - 定期备份数据

4. **资源限制**
   ```bash
   # 限制内存使用
   docker run --memory=512m ...
   
   # 限制CPU使用
   docker run --cpus=1.0 ...
   ```

## 技术栈说明

- **基础镜像**: Python 3.11 slim
- **Web框架**: Flask
- **WSGI服务器**: Gunicorn
- **AI集成**: OpenAI兼容接口
- **部署方式**: Docker容器化

## 支持的AI提供商

根据config.json配置，支持多种AI提供商：
- 阿里通义
- DeepSeek
- 智谱AI
- 硅基流动
- 腾讯混元
- 更多OpenAI兼容接口

## 更新和维护

### 应用更新
1. 停止容器
2. 更新代码
3. 重新构建镜像
4. 启动新容器

### 配置更新
直接编辑 `config.json` 文件，容器会自动加载新配置（部分配置需要重启生效）。

---

如有问题，请检查Docker日志或联系技术支持。