# 苏州迈科咖啡 · 微信小程序开发计划

> 创建日期：2026-08-05 | 版本：v0.1

---

## 项目概述

为苏州迈科咖啡有限公司开发微信小程序，实现线上商品展示、下单购买、优惠券管理、门店定位等功能。

## 技术栈

| 层 | 选择 | 说明 |
|---|------|------|
| 小程序前端 | 微信原生（WXML + WXSS + JS） | 仅微信单端，性能最优 |
| 后端 API | Django + Django REST Framework | 已有技术积累，Admin 开箱即用 |
| 数据库 | MySQL 8.0.44 | 个人云已有服务 |
| 部署 | 个人云自建 | HTTPS + 域名白名单 + ICP 备案 |

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

### 阶段 7：联调测试
- [ ] HTTPS 证书申请与配置
- [ ] 域名白名单配置
- [ ] 真机测试

### 阶段 8：部署上线
- [ ] 小程序提交审核
- [ ] 后端生产环境部署
- [ ] 监控与日志

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

## 当前状态

- **后端**：users + products + orders + coupons + addresses 模块全部完成（66/66 测试通过）
- **小程序**：8 页全功能完成（首页、商品详情、购物车、订单、个人中心、优惠券、收货地址、门店地图），年轻化风格 + 响应式适配
- **域名/证书**：待申请
- **下一步**：阶段 7 联调测试（HTTPS + 域名白名单 + 真机测试）→ 阶段 8 部署上线
