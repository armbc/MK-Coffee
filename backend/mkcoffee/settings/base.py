"""
迈科咖啡 · Django 基础配置（所有环境共用）
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY 必须配置（backend/.env）")

# ========== 应用注册 ==========
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "users",
    "products",
    "orders",
    "coupons",
    "payments",
]

# ========== 中间件 ==========
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # 尽可能靠前
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "mkcoffee.middleware.ApiResponseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mkcoffee.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mkcoffee.wsgi.application"

# ========== 数据库（MySQL） ==========
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "NAME": os.getenv("DB_NAME", "mkcoffee"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# -- Docker 环境下不需要 unix socket，仅在宿主机直连时启用 --
_db_socket = os.getenv("DB_SOCKET")
if _db_socket:
    DATABASES["default"]["OPTIONS"]["unix_socket"] = _db_socket

# -- 修复非 ASCII 数据库密码（PyMySQL MySQL 8.0 SHA2 认证兼容） --
# 传 bytes 而非 str，避免 PyMySQL 内部 latin-1 编码失败
if "PASSWORD" in DATABASES["default"]:
    _pwd = DATABASES["default"]["PASSWORD"]
    if isinstance(_pwd, str):
        try:
            _pwd.encode("latin-1")
        except UnicodeEncodeError:
            DATABASES["default"]["PASSWORD"] = _pwd.encode()

# ========== 密码验证 ==========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== 国际化 ==========
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ========== 静态文件 ==========
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ========== 媒体文件（用户上传） ==========
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========== 默认主键 ==========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== DRF 配置 ==========
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # 统一返回格式
    "EXCEPTION_HANDLER": "mkcoffee.utils.exceptions.custom_exception_handler",
}

# ========== JWT 配置 ==========
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
}

# ========== CORS 配置 ==========
# 具体白名单由 dev.py / production.py 覆写
CORS_ALLOW_CREDENTIALS = True

# ========== 微信小程序配置 ==========
WX_APP_ID = os.getenv("WX_APP_ID", "")
WX_APP_SECRET = os.getenv("WX_APP_SECRET", "")
AUTH_USER_MODEL = "users.User"

if not WX_APP_SECRET:
    import warnings
    warnings.warn("WX_APP_SECRET 未配置，微信登录将不可用", RuntimeWarning)

# ========== 微信支付 V3 配置 ==========
# 以下全部可选 —— 未配置时自动降级为模拟支付
WXPAY_ENABLED = os.getenv("WXPAY_ENABLED", "false").lower() == "true"
WXPAY_MCH_ID = os.getenv("WXPAY_MCH_ID", "")
WXPAY_API_V3_KEY = os.getenv("WXPAY_API_V3_KEY", "")
WXPAY_SERIAL_NO = os.getenv("WXPAY_SERIAL_NO", "")
WXPAY_PRIVATE_KEY = os.getenv("WXPAY_PRIVATE_KEY", "")
WXPAY_NOTIFY_URL = os.getenv("WXPAY_NOTIFY_URL", "")

# 微信支付公钥模式（2024 起新商户无平台证书，改用公钥验签）
# WXPAY_PUBLIC_KEY：商户平台 → API 安全 → 微信支付公钥（PEM 原文）
# WXPAY_PUBLIC_KEY_ID：同一页面上的公钥 ID（验签时校验 Wechatpay-Serial）
WXPAY_PUBLIC_KEY = os.getenv("WXPAY_PUBLIC_KEY", "")
WXPAY_PUBLIC_KEY_ID = os.getenv("WXPAY_PUBLIC_KEY_ID", "")

# 企业微信群机器人 webhook（订单支付成功通知；留空则不推送）
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")
WXPAY_CERT_PATH = os.getenv("WXPAY_CERT_PATH", "")
