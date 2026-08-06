"""
环境路由：根据 DJANGO_ENV 加载 dev / production 配置。
默认使用 dev。
"""
import os
from dotenv import load_dotenv

# 加载 .env 到系统环境变量
load_dotenv()

env = os.getenv("DJANGO_ENV", "dev")

if env == "production":
    from .production import *  # noqa: F401, F403
else:
    from .dev import *  # noqa: F401, F403
