# Docker 部署指南

使用 Docker 快速部署 AI Summary 应用。

## 快速开始

### 方法一：Docker Compose（推荐）

```bash
docker-compose up -d
```

### 方法二：手动构建

```bash
# 构建镜像
docker build -t ai-summary-app .

# 运行容器
docker run -d \
  --name ai-summary \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  ai-summary-app
```

访问 http://localhost:5000

## 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/config.json` | 配置文件 |
| `/app/data` | 数据目录 |

## 配置管理

所有配置通过 `config.json` 管理，无需环境变量。修改日志级别即时生效，修改端口/地址需重启容器：

```bash
docker restart ai-summary
```

## 常用命令

```bash
# 查看日志
docker logs -f ai-summary

# 重启
docker restart ai-summary

# 健康检查
docker inspect ai-summary --format='{{.State.Health.Status}}'

# 进入容器调试
docker exec -it ai-summary /bin/bash
```

## 故障排除

**端口被占用**
```bash
netstat -tulpn | grep :5000
# 或更换端口: -p 8080:5000
```

**构建失败**
```bash
docker build --no-cache -t ai-summary-app .
```

**容器启动失败**
```bash
docker logs ai-summary
```

## 技术栈

- **基础镜像**: python:3.11-slim
- **ASGI 服务器**: Uvicorn
- **Web 框架**: FastAPI
- **AI 集成**: OpenAI 兼容接口
