#!/bin/bash
# ============================================================
# 迈科咖啡 · Docker 入口脚本
# 等待 MySQL → migrate → collectstatic → 启动 gunicorn
# ============================================================
set -e

echo "⏳ 等待 MySQL 就绪 (${DB_HOST}:${DB_PORT:-3306})..."
while ! nc -z "${DB_HOST:-db}" "${DB_PORT:-3306}"; do
  sleep 2
done
echo "✅ MySQL 已就绪"

echo "📦 运行数据库迁移..."
python manage.py migrate --noinput

echo "📂 收集静态文件..."
python manage.py collectstatic --noinput

echo "🚀 启动 Gunicorn..."
exec gunicorn mkcoffee.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
