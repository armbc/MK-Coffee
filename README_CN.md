<!--
================================================================
  MK-Coffee ☕
  苏州迈科咖啡有限公司 · 微信小程序
================================================================
-->

<p align="center">
  <h1 align="center">☕ 迈科咖啡 MK-Coffee</h1>
  <p align="center">
    <strong>苏州迈科咖啡有限公司</strong> · 微信小程序 + 后端 API
    <br/>
    在线下单 · 商品展示 · 优惠券 · 门店定位
  </p>
</p>

---

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 小程序前端 | 微信原生框架（WXML + WXSS + JS） |
| 后端 API | Django 5.1 + Django REST Framework 3.15 |
| 鉴权 | `djangorestframework-simplejwt`（微信 `jscode2session` 登录） |
| 数据库 | MySQL 8.0 |
| 部署 | Docker + docker-compose（db / backend / nginx 三服务编排） |
| 反向代理 | Nginx Alpine + Let's Encrypt SSL |

## ✨ 功能

- **微信登录** — `wx.login` → `jscode2session` → JWT 鉴权，自动 session_key 维护
- **商品展示** — 分类浏览（袋装/罐装咖啡豆、定制烘焙、器皿）、多规格、价格 | 首页轮播 + 推荐商品
- **购物车** — 加入/修改数量/删除/勾选，同品同规格自动叠加 | 未登录友好提示
- **订单系统** — 购物车生成订单 → 模拟支付 → 状态流转（待支付→已支付→已发货→已完成→已取消）| 库存校验 + 事务保护
- **优惠券** — 领取、使用判断（最低金额/有效期）、过期处理
- **门店地图** — 微信 Map 组件，门店位置展示
- **收货地址** — 新增/编辑/删除，手机号前后端双重校验 | 默认预填苏州工业园
- **响应式 UI** — 手机/平板/桌面三端适配，温暖咖啡棕 + 明亮奶油色主题 | 表格左右滑动切换

## 📁 项目结构

```
MK-Coffee/
├── backend/                  # Django REST API
│   ├── mkcoffee/             # Django 配置（dev / production 分环境）
│   │   ├── settings/         # base.py / dev.py / production.py
│   │   ├── middleware.py     # 统一 API 响应格式
│   │   └── utils/exceptions.py
│   ├── users/                # 用户模块（微信登录、个人资料、收货地址）
│   ├── products/             # 商品模块（分类、商品、规格、seed 命令）
│   ├── orders/               # 订单模块（购物车、订单、订单明细、模拟支付）
│   ├── coupons/              # 优惠券模块（模型、领取、核销）
│   ├── manage.py
│   └── requirements.txt
├── miniapp/                  # 微信小程序
│   ├── app.js                # 入口（设备检测、登录态恢复）
│   ├── app.json              # 页面路由 + 底部 TabBar
│   ├── app.wxss              # 全局样式 | 设计 Token
│   ├── utils/
│   │   ├── api.js            # 请求封装（Bearer 注入、401 处理、统一 toast）
│   │   └── swipe-tab.js      # Tab 左右滑动切换组件
│   └── pages/
│       ├── index/            # 首页（轮播、分类入口、推荐商品）
│       ├── product/          # 商品详情（图片轮播、规格选择、加购）
│       ├── cart/             # 购物车（勾选、改数量、结算）
│       ├── order/            # 订单列表 & 详情（状态跟踪、取消、支付）
│       ├── user/             # 个人中心（登录、订单、地址、优惠券入口）
│       ├── store/            # 门店地图
│       ├── coupons/          # 我的优惠券
│       └── addresses/        # 收货地址管理
├── deploy/                   # Docker 部署配置
│   ├── docker-entrypoint.sh  # 入口脚本（等 MySQL → migrate → collectstatic → 启动）
│   └── nginx/conf.d/
│       ├── default.conf               # HTTP 模式（证书申请前）
│       └── default-ssl.conf.example   # HTTP + HTTPS 完整版（证书申请后）
├── Dockerfile                # Python 3.12-slim + Gunicorn
├── docker-compose.yml        # db + backend + nginx 编排
└── .dockerignore
```

## 🚀 快速启动（Docker）

```bash
# 1. 克隆项目
git clone <仓库地址> && cd MK-Coffee

# 2. 创建环境变量文件
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 SECRET_KEY、DB_PASSWORD、WX_APP_ID、WX_APP_SECRET

# 3. 启动
docker compose up -d

# 4. 验证
curl http://localhost/api/
```

启动后自动运行三个服务：
- **db** — MySQL 8.0（healthcheck 健康检测，端口 3306）
- **backend** — Django + Gunicorn（启动时自动 migrate + collectstatic，内网端口 8000）
- **nginx** — 反向代理（端口 80，静态文件服务，ACME 验证路径就绪）

## 💻 本地开发（不使用 Docker）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 创建 .env，设置 DB_HOST=127.0.0.1，DB_SOCKET 指向本地 MySQL socket
cp .env.example .env

python manage.py migrate
python manage.py runserver
```

## 🔌 API 接口

所有接口以 `/api/` 为前缀，需鉴权的接口携带 `Authorization: Bearer <token>`。

| 模块 | 接口 | 鉴权 |
|------|------|------|
| **登录** | `POST /auth/wx-login/` | — |
| **用户** | `GET /users/me/` | Bearer |
| **商品** | `GET /products/` | — |
| | `GET /products/{id}/` | — |
| **购物车** | `GET /cart/` | Bearer |
| | `POST /cart/` | Bearer |
| | `POST /cart/{id}/update-qty/` | Bearer |
| | `POST /cart/{id}/remove/` | Bearer |
| **订单** | `GET /orders/` | Bearer |
| | `POST /orders/` | Bearer |
| | `POST /orders/{id}/cancel/` | Bearer |
| | `POST /orders/{id}/pay/` | Bearer |
| **优惠券** | `GET /coupons/` | — |
| | `POST /coupons/{id}/claim/` | Bearer |
| **收货地址** | `GET /addresses/` | Bearer |
| | `POST /addresses/` | Bearer |

### 统一响应格式

```json
{
  "code": 0,
  "data": { ... },
  "msg": "ok"
}
```

> `code=0` 表示成功，非 0 表示业务异常。HTTP 状态码与业务码分离，前端统一处理。

## 🔐 环境变量

详见 `backend/.env.example`，核心变量：

| 变量 | 说明 | Docker 默认值 |
|------|------|---------------|
| `DJANGO_ENV` | `dev` 或 `production` | `dev` |
| `SECRET_KEY` | Django 密钥（生产务必使用强随机字符串） | — |
| `DB_HOST` | MySQL 地址 | `db` |
| `DB_NAME` | 数据库名 | `mkcoffee` |
| `DB_PASSWORD` | MySQL root 密码 | — |
| `DB_SOCKET` | Unix socket 路径（Docker 环境留空） | — |
| `WX_APP_ID` | 微信小程序 AppID | — |
| `WX_APP_SECRET` | 微信小程序 AppSecret | — |
| `DJANGO_ALLOWED_HOSTS` | 生产 ALLOWED_HOSTS（逗号分隔） | `api.mk-coffee.com` |

## 📱 小程序配置

1. 打开[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)，导入 `miniapp/` 目录
2. 填入 AppID（在 [mp.weixin.qq.com](https://mp.weixin.qq.com) 获取）
3. 在 `app.js` 中修改 `apiBase` 指向后端地址
4. 开发阶段：开发者工具 → 设置 → 取消勾选「不校验合法域名」

> 基础库版本要求：≥ 2.18.0

## 🧪 测试

```bash
cd backend
python manage.py test
```

当前状态：**66 / 66 测试全部通过**（覆盖 users、products、orders、coupons、addresses 五个模块）。

## 🚢 部署

项目采用 Docker Compose 编排，两阶段部署：

1. **HTTP 阶段**（证书申请前）：`deploy/nginx/conf.d/default.conf`
2. **HTTPS 阶段**（证书申请后）：复制 `default-ssl.conf.example` → `default-ssl.conf`，取消 `docker-compose.yml` 中 443 端口注释

HTTPS 证书通过 Let's Encrypt (certbot) 免费获取，自动续期。

> 微信小程序正式上线必须使用已备案的 HTTPS 域名。

## 📄 许可证

专有软件 — 苏州迈科咖啡有限公司
