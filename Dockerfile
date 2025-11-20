FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装 UV
RUN pip install uv

# 安装 Python 依赖
RUN uv pip install --system \
    httpx[http2]>=0.24.0 \
    playwright>=1.40.0 \
    python-dotenv>=1.0.0 \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    apscheduler>=3.10.0 \
    cryptography>=41.0.0

# 安装 Playwright 浏览器
RUN playwright install chromium && \
    playwright install-deps chromium

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8080

# 启动脚本
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
