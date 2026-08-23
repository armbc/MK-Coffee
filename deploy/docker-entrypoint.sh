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

# -- 确保 staticfiles 目录权限正确（Docker volume 初始为 root） --
chown -R appuser:appuser /app/staticfiles 2>/dev/null || true
# -- media 目录（用户上传头像等），volume 初始为 root，必须授权给 appuser --
mkdir -p /app/media
chown -R appuser:appuser /app/media 2>/dev/null || true

# -- 根据 CPU 核心数动态设置 workers --
WORKERS=$(expr 2 \* $(nproc) + 1)

exec su -s /bin/bash appuser -c "gunicorn mkcoffee.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${WORKERS} \
    --access-logfile - \
    --error-logfile - \
    --log-level info"
