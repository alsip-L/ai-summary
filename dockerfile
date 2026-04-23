FROM node:20-slim AS frontend-build
WORKDIR /app/frontend-vue
COPY frontend-vue/package.json frontend-vue/package-lock.json* ./
RUN npm install
COPY frontend-vue/ .
RUN npm run build

FROM python:3.11-slim AS deps-build
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y gcc g++ && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps-build /usr/local/bin /usr/local/bin

COPY . .
COPY --from=frontend-build /app/frontend-vue/dist ./frontend-vue/dist

RUN mkdir -p /app/data

EXPOSE 5000

# 健康检查端口通过 PORT 环境变量配置，默认 5000
ENV PORT=5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

CMD ["python", "run.py"]
