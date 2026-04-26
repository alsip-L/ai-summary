# ===== 阶段1: 安装 Python 依赖 (Alpine, 预编译 wheel) =====
FROM python:3.11-alpine AS deps-build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir --only-binary=:all: -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# ===== 阶段2: 运行时镜像 (Alpine) =====
FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0

WORKDIR /app

# 从依赖阶段复制已安装的 Python 包
COPY --from=deps-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps-build /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app/ ./app/
COPY core/ ./core/
COPY templates/ ./templates/
COPY config.json ./
COPY run.py ./

# 从本地前端产物复制（需先在本地构建: cd frontend-vue && npm run build）
COPY frontend-vue/dist ./frontend-vue/dist

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs

EXPOSE 5000

CMD ["python", "run.py"]
