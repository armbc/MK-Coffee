# 苏州迈科咖啡 · 微信小程序开发计划

> 创建日期：2026-08-05 | 版本：v0.2

---

## 项目概述

为苏州迈科咖啡有限公司开发微信小程序，实现线上商品展示、下单购买、优惠券管理、门店定位等功能。

## 技术栈

| 层 | 选择 | 说明 |
|---|------|------|
| 小程序前端 | 微信原生（WXML + WXSS + JS） | 仅微信单端，性能最优 |
| 后端 API | Django + Django REST Framework | 已有技术积累，Admin 开箱即用 |
| 数据库 | MySQL 8.0.44 | 个人云已有服务 |
| 部署 | Docker + docker-compose | 个人云联调 → 云服务器上线 + ICP 备案 |

## 项目结构

```
Django/MK-Coffee/
├── backend/                  # Django REST API
│   ├── manage.py
│   ├── mkcoffee/            # Django 配置
│   ├── users/               # 用户模块（微信登录）
│   ├── products/            # 商品模块
│   ├── orders/              # 订单模块
│   ├── coupons/             # 优惠券模块
│   ├── locations/           # 门店模块
│   └── requirements.txt
├── deploy/                  # Docker 部署配置
│   ├── docker-entrypoint.sh # 入口脚本（等待 DB → migrate → gunicorn）
│   └── nginx/conf.d/
│       ├── default.conf      # HTTP only（证书申请前）
│       └── default-ssl.conf.example  # HTTPS 完整版（证书后启用）
├── Dockerfile               # Django + Gunicorn 镜像
├── docker-compose.yml       # db + backend + nginx 三服务编排
├── .dockerignore
├── miniapp/                  # 微信小程序前端
│   ├── app.js / app.json / app.wxss
│   └── pages/
│       ├── index/           # 首页
│       ├── product/         # 商品详情
│       ├── cart/            # 购物车
│       ├── order/           # 订单
│       ├── user/            # 个人中心
│       └── store/           # 门店地图
└── PLAN.md                   # 本文件
```

## 微信平台关键约束

出自微信官方文档（developers.weixin.qq.com）：

- **协议**：`wx.request` / `wx.uploadFile` / `wx.downloadFile` 必须 HTTPS
- **WebSocket**：`wx.connectSocket` 必须 WSS
- **域名白名单**：需在小程序后台配置，必须 ICP 备案，不能用 IP
- **并发上限**：`wx.request` 最多 10 个，超时默认 60s
- **证书**：服务器 HTTPS 证书强校验
- **开发阶段**：可在开发者工具中跳过校验，方便调试
- **微信登录**：后端实现 `jscode2session`，换取 `openid` 和 `session_key`
- **AppSecret**：绝对不可出现在前端代码中

## 开发阶段

### 阶段 1：项目初始化
- [x] 创建 Django 项目骨架
- [x] 配置虚拟环境（`backend/.venv/`）
- [x] 配置 MySQL 数据库
- [x] 安装依赖：Django、DRF、django-cors-headers、PyMySQL、requests、cryptography
- [x] 小程序项目初始化（微信开发者工具创建）

### 阶段 2：用户模块
- [x] 微信登录 API（jscode2session → openid → JWT）
- [x] 用户信息存储（头像、昵称、手机号）
- [x] 小程序端 wx.login 集成

### 阶段 3：商品模块
- [x] 分类管理（袋装咖啡豆、罐装咖啡豆、定制烘焙咖啡豆、咖啡器皿）
- [x] 商品 CRUD（名称、图片、描述、规格、价格）
- [x] Django Admin 后台管理
- [x] 小程序商品列表 / 详情页

### 阶段 4：订单模块
- [x] 购物车（加入/修改数量/删除/清空，自动叠加同品同规格）
- [x] 下单 API（从购物车生成订单，库存校验与扣减，事务保护）
- [x] 订单状态机（待支付 → 已支付 → 已发货 → 已完成 → 已取消）
- [x] 取消订单（恢复库存）
- [x] 模拟支付（占位实现，待接入微信支付）
- [ ] 微信支付集成（统一下单、支付回调）

### 阶段 5：小程序页面
- [x] 首页（轮播、推荐商品、分类入口）
- [x] 商品详情页（图片轮播、规格选择、加入购物车）
- [x] 购物车页
- [x] 订单列表 / 详情页
- [x] 个人中心（登录、订单、地址）

### 阶段 6：辅助功能
- [x] 优惠券模块（领取、使用、过期）
- [x] 门店定位（微信地图组件）
- [x] 收货地址管理

### 阶段 7：联调测试 🔄 进行中
- [x] Docker 部署方案（Dockerfile + docker-compose + nginx + entrypoint）
- [x] 小程序 apiBase 改为 `https://api.mk-coffee.com/api`
- [x] base.py unix_socket 条件化（兼容 Docker / 宿主机）
- [ ] 个人云 Docker 联调（`docker compose up -d`，开发者工具跳过域名校验）
- [ ] 购买云服务器 + ICP 备案（用户自助，约 15-20 工作日）
- [ ] HTTPS 证书申请（certbot + Let's Encrypt，备案通过后在云服务器执行）
- [ ] 域名白名单配置（微信小程序后台）
- [ ] 真机测试

### 阶段 8：部署上线
- [ ] 代码迁移至云服务器（scp + docker compose up -d）
- [ ] 启用 HTTPS 完整配置（nginx default-ssl.conf）
- [ ] 小程序提交审核
- [ ] 监控与日志

## Docker 部署架构

```
docker-compose.yml
├── db (MySQL 8.0)
│   └── volume: mysql_data → /var/lib/mysql
├── backend (Django 5.1 + Gunicorn)
│   ├── env_file: backend/.env
│   ├── environment: DB_HOST=db, DB_SOCKET=
│   └── volume: static_volume → /app/staticfiles
├── nginx (Alpine)
│   ├── ports: 80[:443]
│   ├── config: deploy/nginx/conf.d/default.conf
│   └── volumes: static_volume, certbot_www, certbot_conf
└── certbot（按需宿主机运行）
    └── volumes: certbot_www, certbot_conf
```

### 两阶段部署流程

| 阶段 | nginx 配置 | 说明 |
|------|-----------|------|
| 证书申请前 | `default.conf`（HTTP only） | 个人云联调 / certbot webroot 验证 |
| 证书申请后 | `default-ssl.conf.example` → `default-ssl.conf` | HTTP→HTTPS 重定向 + 443 端口 |

### ICP 备案 + 证书申请步骤（用户自助）

1. **购买云服务器**（阿里云/腾讯云轻量，2核4G 起，约 ¥68/月）
2. **提交 ICP 备案**（云服务商备案系统，约 15-20 工作日）
3. **DNS 解析**：Cloudflare 添加 A 记录 `api.mk-coffee.com` → 云服务器 IP（关闭代理，DNS only）
4. **安装 Docker**：`curl -fsSL https://get.docker.com | sh`
5. **启动服务**：`docker compose up -d`（HTTP 模式）
6. **申请证书**：`certbot certonly --webroot -w /var/lib/docker/volumes/.../_data -d api.mk-coffee.com`
7. **启用 HTTPS**：切换 nginx 配置 → `docker compose restart nginx`

## 数据库设计（初步）

```
users          — 用户（openid, nickname, avatar, phone, created_at）
products       — 商品（name, category, description, image, price, stock, status）
categories     — 分类（name, icon, sort_order）
specs          — 规格（product_id, name, price, stock）
carts          — 购物车（user_id, product_id, spec_id, quantity）
orders         — 订单（user_id, order_no, total, status, created_at）
order_items    — 订单明细（order_id, product_id, spec_id, quantity, price）
coupons        — 优惠券（name, type, value, min_amount, start_date, end_date）
user_coupons   — 用户优惠券（user_id, coupon_id, status, used_at）
addresses      — 收货地址（user_id, name, phone, province, city, district, detail）
```

## 设计系统 v2（年轻化）

| Token | 值 | 说明 |
|---|---|---|
| 主色 primary | #5c3d2e → #7a5a47 | 温暖咖啡棕渐变 |
| 辅色 accent | #e8873a → #f0a060 | 活泼暖橙渐变 |
| 背景 bg | #fefaf6 | 明亮奶油色 |
| 卡片 bg-card | #ffffff | 纯白 |
| 文字 text | #2c2416 | 深棕 |
| 次要文字 text-secondary | #8c7b6e | 中棕 |
| 边框 border | #f0ebe3 | 柔和米色 |

### 响应式断点

| 类型 | 宽度 | 商品列数 | 页面最大宽 |
|---|---|---|---|
| 手机 phone | < 420px | 2 | 全宽 |
| 平板 tablet | 420~768px | 3 | 全宽 |
| 桌面 desktop | > 768px | 4 | 960px 居中 |

## 变更日志

### 2026-08-06（全天综合修复 + 审计）

#### 购物车模块
- **修复**：勾选对勾不显示（根因：setData 对象 key 字符串/数字类型不一致，改为 `item.isSelected` + 路径标记 `items[n].isSelected`）
- **修复**：数量修改 405（根因：微信 wx.request 对 PUT 丢 Authorization header，后端新增 `POST /cart/{id}/update-qty/`）
- **修复**：删除 401（同根因，后端新增 `POST /cart/{id}/remove/`）
- **修复**：Promise uncaught — 补 `.catch().finally()` + 登录检查前置

#### 收货地址模块
- **修复**：输入框文字纵向被裁（`.form-input` 缺 `line-height`/`height`）
- **修复**：新增表单预填默认值（江苏省/苏州市/工业园区）
- **修复**：删除 500（`users/views.py` 缺 `from django.shortcuts import get_object_or_404`）
- **修复**：编辑匹配失败（`a.id === dataset.id` 类型陷阱 → `Number()`）
- **新增**：手机号校验（前端 `^1[3-9]\d{9}$` + 后端 `validate_phone`）
- **后端**：AddressViewSet 新增 `update`/`remove` POST 端点（替换 PUT/DELETE）

#### 全局修复
- **新增**：Tab 左右滑动循环切换（`utils/swipe-tab.js`，4 个 tab 页面，阈值 60px）
- **修复**：`api.js` 移除 401 toast（退出登录后不弹"登录已过期"）
- **修复**：cart/order/coupons 未登录时跳过 API 请求，避免调试器红色 401
- **审计**：全项目扫描，修复 4 个 dataset 类型陷阱 + 6 个文件 14 处缺 `.catch()`

#### 涉及文件（今日改动 >30 个文件）
- 后端：`orders/views.py`, `users/views.py`, `users/serializers.py`
- 前端工具：`utils/api.js`, `utils/swipe-tab.js`（新增）
- 前端页面：`index`, `product`, `cart`, `order`, `user`, `coupons`, `addresses` 的 JS/WXML/WXSS

### 2026-08-07 · Docker 化部署（阶段 7-8）

- **域名**：Cloudflare 域名 mk-coffee.com，API 子域 `api.mk-coffee.com`
- **架构切换**：从 bare-metal（nginx + gunicorn + systemd）改为 Docker Compose 三服务编排
- **新增**：`Dockerfile`（Python 3.12-slim + Gunicorn，非 root 用户）
- **新增**：`docker-compose.yml`（db + backend + nginx，带 healthcheck）
- **新增**：`deploy/docker-entrypoint.sh`（等待 MySQL → migrate → collectstatic → 启动）
- **新增**：`deploy/nginx/conf.d/default.conf`（HTTP only，证书申请前）
- **新增**：`deploy/nginx/conf.d/default-ssl.conf.example`（HTTP + HTTPS，证书后启用）
- **新增**：`.dockerignore`
- **新增**：`backend/.env.example`（含 Docker / 宿主机双模式注释）
- **修改**：`base.py` unix_socket 条件化（DB_SOCKET 为空时跳过，兼容 Docker 网络）
- **修改**：`miniapp/app.js` apiBase 改为 `https://api.mk-coffee.com/api`
- **修改**：`requirements.txt` 添加 `gunicorn==23.0.0`
- **移除**：裸机部署文件（deploy/gunicorn.conf.py、deploy/mk-coffee-api.service、deploy/nginx/mk-coffee-api.conf）
- **下一步**：个人云 Docker 联调 → 购买云服务器 + ICP 备案 → 证书申请 → 微信白名单

### 2026-08-07 · 腾服 HTTPS 上线

- **服务器**：腾讯云上海 2核2G（腾服），Ubuntu 24.04，IP `124.220.108.118`
- **SSH**：个人云 → 腾服免密登录已配置
- **Docker**：已安装 v29.7.2，配置腾讯云镜像加速
- **Dockerfile 优化**：apt 源改用清华镜像，pip 源改用清华镜像
- **权限修复**：移除 `USER appuser`，entrypoint 以 root 运行 collectstatic 后 `su appuser` 启动 gunicorn
- **密码修复**：`base.py` 新增非 ASCII 数据库密码 bytes 编码（PyMySQL SHA2 认证兼容）
- **部署**：`docker compose up -d` 三服务（db + backend + nginx）运行正常
- **证书**：Let's Encrypt 申请成功，有效期至 2026-11-05
- **HTTPS**：`default.conf` 切换为 HTTP→HTTPS 301 + 443 SSL（TLS 1.2/1.3, HSTS）
- **自动续期**：crontab 每月 1 号凌晨 3 点 `certbot renew` + `docker compose restart nginx`
- **代码**：已 commit push（`6f80ded`）
- **API 验证**：`https://api.mk-coffee.com/api/` 正常返回

#### 涉及文件
- 新增：`deploy/nginx/conf.d/default-ssl.conf.example`
- 修改：`Dockerfile`、`docker-compose.yml`、`deploy/docker-entrypoint.sh`、`deploy/nginx/conf.d/default.conf`、`backend/mkcoffee/settings/base.py`、`PLAN.md`

## 当前状态

- **后端**：users + products + orders + coupons + addresses 模块全部完成（66/66 测试通过）
- **小程序**：8 页全功能完成（首页、商品详情、购物车、订单、个人中心、优惠券、收货地址、门店地图），年轻化风格 + 响应式适配
- **域名**：mk-coffee.com（Cloudflare），API 子域 `api.mk-coffee.com`，前端 apiBase 已改为 HTTPS
- **部署方案**：Docker + docker-compose（Dockerfile、docker-compose.yml、nginx conf.d、entrypoint 已就绪）
- **服务器**：腾讯云上海 2核2G（腾服），IP `124.220.108.118`，Docker 三服务运行中
- **HTTPS**：Let's Encrypt 证书已申请，`https://api.mk-coffee.com/api/` 正常
- **下一步**：微信小程序后台域名白名单 ← 真机测试 ← 提交审核

### 2026-08-08 · 微信支付 V3 集成

- **新增**：`backend/payments/` 支付模块（PaymentRecord 模型、WXPayClient、统一下单、回调解密、签名验证）
- **架构**：有商户凭证走真实 JSAPI 支付，无凭证自动降级为模拟支付
- **新增 API**：`POST /api/payments/callback/` 微信支付回调通知
- **修改 API**：`POST /api/orders/{id}/pay/` 返回 `{method, pay_params?}` 自适应格式
- **小程序适配**：order.js onPay 支持 mock / wechat_jsapi 双路径；cart.js 下单后自动打开订单详情
- **配置**：`backend/.env` 新增 WXPAY_* 环境变量（全可选，空则降级模拟支付）
- **测试**：全部 66/66 通过（含 payments 迁移）
- **下一步**：备案通过 + 商户号到手后填入 WXPAY_* 即可启用真实支付
