# AI摘要应用 - Alpine Linux Docker部署指南

本指南专门为 **aarch64架构的Alpine Linux** 系统提供Docker部署方案。

## 📋 系统要求

- **系统**: Linux (aarch64架构)
- **发行版**: Alpine Linux
- **内核版本**: 6.9.1-postmarketos-qcom (支持)
- **Docker**: 20.0+
- **内存**: 最少256MB，推荐512MB
- **存储**: 至少1GB可用空间

## 🚀 快速开始

### 方法一：使用脚本（推荐）

1. **构建镜像**
   ```bash
   # Linux/macOS
   ./build-alpine.sh
   
   # Windows
   build-alpine.bat
   ```

2. **运行应用**
   ```bash
   # 使用docker run
   ./run-alpine.sh
   
   # 或使用docker-compose
   ./run-compose-alpine.sh
   ```

3. **访问应用**
   打开浏览器访问: `http://localhost:5000`

### 方法二：手动构建

1. **构建镜像**
   ```bash
   docker build --file Dockerfile.alpine --tag ai-summary-app:latest .
   ```

2. **运行容器**
   ```bash
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
   ```

### 方法三：使用Docker Compose

```bash
# 构建并启动
docker-compose -f docker-compose.alpine.yml up -d

# 查看状态
docker-compose -f docker-compose.alpine.yml ps

# 查看日志
docker-compose -f docker-compose.alpine.yml logs -f
```

## 📁 文件说明

### 核心文件

| 文件名 | 用途 | 平台 |
|--------|------|------|
| `Dockerfile.alpine` | Alpine专用的Docker构建文件 | aarch64/Alpine |
| `.dockerignore.alpine` | Alpine构建时忽略的文件列表 | aarch64/Alpine |
| `docker-compose.alpine.yml` | Alpine专用的compose配置 | aarch64/Alpine |

### 构建脚本

| 脚本名 | 平台 | 功能 |
|--------|------|------|
| `build-alpine.sh` | Linux/macOS | 构建Docker镜像 |
| `build-alpine.bat` | Windows | 构建Docker镜像 |
| `run-alpine.sh` | Linux/macOS | 运行容器 |
| `run-compose-alpine.sh` | 跨平台 | 使用compose运行 |
| `stop-alpine.sh` | Linux/macOS | 停止容器 |
| `cleanup-alpine.sh` | Linux/macOS | 完全清理 |

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | production | Flask运行环境 |
| `PYTHONUNBUFFERED` | 1 | Python输出缓冲设置 |
| `DEBUG_LEVEL` | INFO | 调试级别 |

### 数据卷

| 容器路径 | 主机路径 | 说明 |
|----------|----------|------|
| `/app/config.json` | `./config.json` | 配置文件（只读） |
| `/app/data` | `./data` | 数据目录 |
| `/app/output` | `./output` | 输出目录 |
| `/app/temp` | `./temp` | 临时目录 |

## 🔍 常用命令

### 容器管理

```bash
# 查看容器状态
docker ps --filter name=ai-summary-container

# 查看实时日志
docker logs -f ai-summary-container

# 重启容器
docker restart ai-summary-container

# 停止容器
docker stop ai-summary-container

# 进入容器
docker exec -it ai-summary-container sh

# 完全清理
./cleanup-alpine.sh
```

### Docker Compose管理

```bash
# 启动服务
docker-compose -f docker-compose.alpine.yml up -d

# 停止服务
docker-compose -f docker-compose.alpine.yml down

# 重启服务
docker-compose -f docker-compose.alpine.yml restart

# 查看日志
docker-compose -f docker-compose.alpine.yml logs -f

# 查看状态
docker-compose -f docker-compose.alpine.yml ps
```

## 🐛 故障排除

### 构建失败

1. **检查Docker是否安装**
   ```bash
   docker --version
   ```

2. **检查Docker服务是否运行**
   ```bash
   docker info
   ```

3. **检查系统架构**
   ```bash
   uname -m
   # 应该输出: aarch64
   ```

### 容器启动失败

1. **查看容器日志**
   ```bash
   docker logs ai-summary-container
   ```

2. **检查端口占用**
   ```bash
   netstat -tlnp | grep 5000
   ```

3. **检查配置文件**
   ```bash
   # 确保config.json存在且格式正确
   cat config.json
   ```

### 应用无法访问

1. **检查容器状态**
   ```bash
   docker ps
   ```

2. **检查防火墙**
   ```bash
   # Alpine Linux
   iptables -L -n | grep 5000
   ```

3. **测试容器连通性**
   ```bash
   docker exec ai-summary-container curl -f http://localhost:5000/
   ```

## 📊 性能优化

### 资源限制

可以在docker-compose.alpine.yml中调整资源限制：

```yaml
deploy:
  resources:
    limits:
      memory: 512M      # 最大内存
      cpus: '0.5'       # 最大CPU
    reservations:
      memory: 256M      # 保留内存
      cpus: '0.25'      # 保留CPU
```

### 日志配置

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"     # 单个日志文件最大10MB
    max-file: "3"       # 保留3个日志文件
```

## 🔐 安全建议

1. **修改默认密钥**
   ```bash
   # 在运行容器时设置
   -e FLASK_SECRET_KEY="your-secret-key-here"
   ```

2. **定期更新镜像**
   ```bash
   # 重新构建镜像
   ./build-alpine.sh
   ```

3. **监控资源使用**
   ```bash
   docker stats ai-summary-container
   ```

## 📈 监控和健康检查

### 健康检查

Dockerfile中已配置健康检查：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1
```

### 监控命令

```bash
# 检查容器健康状态
docker inspect ai-summary-container --format='{{.State.Health.Status}}'

# 查看资源使用情况
docker stats ai-summary-container --no-stream
```

## 💾 备份和恢复

### 备份数据

```bash
# 备份配置文件
cp config.json config.json.backup

# 备份数据目录
tar -czf data-backup.tar.gz data/ output/ temp/
```

### 恢复数据

```bash
# 恢复配置文件
cp config.json.backup config.json

# 恢复数据目录
tar -xzf data-backup.tar.gz
```

## 🎯 生产环境建议

1. **使用外部数据库**（如果需要）
2. **配置反向代理**（如Nginx）
3. **设置监控和告警**
4. **定期备份数据**
5. **更新安全补丁**

---

**注意**: 本配置专门针对aarch64架构的Alpine Linux系统优化。如在其他平台上使用，可能需要调整相关配置。