# ============================================================
# 迈科咖啡 · Docker 镜像
# 构建： docker compose build
# ============================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -- 安装系统依赖（清华 Debian 镜像加速） --
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# -- 安装 Python 依赖 --
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# -- 复制源码 --
COPY backend/ .

# -- 创建非 root 用户 --
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

EXPOSE 8000

# -- 入口脚本：等待 MySQL → migrate → collectstatic → gunicorn --
COPY deploy/docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
