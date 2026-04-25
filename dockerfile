# ===== 阶段1: 构建前端 =====
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend-vue
COPY frontend-vue/package.json frontend-vue/package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com && \
    npm install --ignore-scripts && \
    npm cache clean --force
COPY frontend-vue/ .
RUN npm run build && rm -rf node_modules

# ===== 阶段2: 安装 Python 依赖 (Alpine) =====
FROM python:3.11-alpine AS deps-build
WORKDIR /app
COPY requirements.txt .

# 分步安装编译工具和依赖，避免单层磁盘 I/O 压力过大
# 步骤1: 安装编译工具链
RUN apk add --no-cache gcc g++ musl-dev

# 步骤2: 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 步骤3: 清理编译工具链（仅保留编译产物在 site-packages 中）
RUN apk del gcc g++ musl-dev

# ===== 阶段3: 运行时镜像 (Alpine) =====
FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0

WORKDIR /app

# 从依赖阶段复制已安装的 Python 包
COPY --from=deps-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps-build /usr/local/bin /usr/local/bin

# 复制应用代码（排除 SDK，运行时不使用）
COPY app/ ./app/
COPY core/ ./core/
COPY templates/ ./templates/
COPY config.json ./
COPY run.py ./

# 从前端构建阶段复制产物
COPY --from=frontend-build /app/frontend-vue/dist ./frontend-vue/dist

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs

EXPOSE 5000

CMD ["python", "run.py"]
