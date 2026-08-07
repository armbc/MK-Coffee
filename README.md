<!--
================================================================
  MK-Coffee ☕
  WeChat Mini Program for Suzhou Maike Coffee Co., Ltd.
================================================================
-->

<p align="center">
  <h1 align="center">☕ MK-Coffee</h1>
  <p align="center">
    WeChat Mini Program &amp; Backend API for <strong>Suzhou Maike Coffee</strong>
    <br/>
    Online ordering · Product catalog · Coupons · Store locator
  </p>
</p>

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Mini Program | WeChat Native (WXML + WXSS + JS) |
| Backend API | Django 5.1 + Django REST Framework 3.15 |
| Auth | `djangorestframework-simplejwt` (WeChat `jscode2session`) |
| Database | MySQL 8.0 |
| Deployment | Docker + docker-compose (db / backend / nginx) |
| Reverse Proxy | Nginx (Alpine) with Let's Encrypt SSL |

## ✨ Features

- **WeChat Login** — `wx.login` → `jscode2session` → JWT authentication
- **Product Catalog** — Categories (coffee beans, brewing equipment), specs, pricing
- **Shopping Cart** — Add / edit quantity / remove / select, auto-merge same SKU
- **Order System** — Checkout → simulated payment → status lifecycle (pending → paid → shipped → done)
- **Coupons** — Issue, redeem, expiration handling
- **Store Map** — WeChat Map component, store location display
- **Addresses** — CRUD with phone validation
- **Responsive UI** — Phone / tablet / desktop breakpoints, warm coffee-brown theme
- **Unified API Response** — Every endpoint returns `{ code: 0, data: {...}, msg: "ok" }`

## 📁 Project Structure

```
MK-Coffee/
├── backend/                  # Django REST API
│   ├── mkcoffee/             # Project settings (dev / production split)
│   ├── users/                # WeChat login, user profiles, addresses
│   ├── products/             # Categories, products, specs, seed command
│   ├── orders/               # Cart, orders, order items, mock payment
│   ├── coupons/              # Coupon models, issuance, redemption
│   ├── manage.py
│   └── requirements.txt
├── miniapp/                  # WeChat Mini Program
│   ├── app.js / app.json / app.wxss
│   ├── utils/
│   │   ├── api.js            # Request wrapper (auth, error handling)
│   │   └── swipe-tab.js      # Tab swipe gesture helper
│   └── pages/
│       ├── index/            # Home — banner, categories, featured
│       ├── product/          # Product detail — carousel, spec selector
│       ├── cart/             # Shopping cart
│       ├── order/            # Order list & detail
│       ├── user/             # Profile / login
│       ├── store/            # Store map
│       ├── coupons/          # My coupons
│       └── addresses/        # Shipping addresses
├── deploy/                   # Docker deployment config
│   ├── docker-entrypoint.sh  # Wait DB → migrate → collectstatic → gunicorn
│   └── nginx/conf.d/
│       ├── default.conf               # HTTP only (pre-certificate)
│       └── default-ssl.conf.example   # HTTP + HTTPS (post-certificate)
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

## 🚀 Quick Start (Docker)

```bash
# 1. Clone
git clone <repo-url> && cd MK-Coffee

# 2. Create environment file
cp backend/.env.example backend/.env
# Edit backend/.env — fill in SECRET_KEY, DB_PASSWORD, WX_APP_ID, WX_APP_SECRET

# 3. Start
docker compose up -d

# 4. Verify
curl http://localhost/api/
```

The stack starts three services:
- **db** — MySQL 8.0 (health-checked, port 3306)
- **backend** — Django + Gunicorn (auto-migrate on startup, port 8000 internal)
- **nginx** — Reverse proxy (port 80, static file serving)

## 💻 Local Development (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env with DB_HOST=127.0.0.1 and DB_SOCKET pointing to your MySQL socket
cp .env.example .env

python manage.py migrate
python manage.py runserver
```

## 🔌 API Endpoints

All endpoints are prefixed with `/api/`. Authenticated requests require `Authorization: Bearer <token>`.

| Module | Endpoint | Auth |
|--------|----------|------|
| **Auth** | `POST /auth/wx-login/` | — |
| **Users** | `GET /users/me/` | Bearer |
| **Products** | `GET /products/` | — |
| | `GET /products/{id}/` | — |
| **Cart** | `GET /cart/` | Bearer |
| | `POST /cart/` | Bearer |
| | `POST /cart/{id}/update-qty/` | Bearer |
| | `POST /cart/{id}/remove/` | Bearer |
| **Orders** | `GET /orders/` | Bearer |
| | `POST /orders/` | Bearer |
| | `POST /orders/{id}/cancel/` | Bearer |
| | `POST /orders/{id}/pay/` | Bearer |
| **Coupons** | `GET /coupons/` | — |
| | `POST /coupons/{id}/claim/` | Bearer |
| **Addresses** | `GET /addresses/` | Bearer |
| | `POST /addresses/` | Bearer |

### Response Format

```json
{
  "code": 0,
  "data": { ... },
  "msg": "ok"
}
```

## 🔐 Environment Variables

See `backend/.env.example` for the complete template. Key variables:

| Variable | Description | Docker Default |
|----------|-------------|----------------|
| `DJANGO_ENV` | `dev` or `production` | `dev` |
| `SECRET_KEY` | Django secret key | — |
| `DB_HOST` | MySQL host | `db` |
| `DB_NAME` | Database name | `mkcoffee` |
| `DB_PASSWORD` | MySQL root password | — |
| `DB_SOCKET` | Unix socket path (leave empty for Docker) | — |
| `WX_APP_ID` | WeChat Mini Program AppID | — |
| `WX_APP_SECRET` | WeChat Mini Program AppSecret | — |
| `DJANGO_ALLOWED_HOSTS` | Production host list (comma-separated) | `api.mk-coffee.com` |

## 📱 Mini Program Setup

1. Open [WeChat DevTools](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html), import the `miniapp/` directory
2. Fill in your AppID (obtain from [mp.weixin.qq.com](https://mp.weixin.qq.com))
3. Update `apiBase` in `app.js` to point to your backend
4. During development, disable domain validation (DevTools → Settings → uncheck "Verify domain")

> Base library version requirement: ≥ 2.18.0

## 🧪 Testing

```bash
cd backend
python manage.py test
```

Current status: **66 / 66 tests passing** (users, products, orders, coupons, addresses).

## 📄 License

Proprietary — Suzhou Maike Coffee Co., Ltd.
