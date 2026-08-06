"""
迈科咖啡 · 开发环境配置
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# 开发环境放宽 CORS
CORS_ALLOW_ALL_ORIGINS = True
