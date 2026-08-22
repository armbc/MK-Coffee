# 🙋 接下来做什么

> 迈科咖啡 · 当前待办  
> 更新：2026-08-22

---

## 已完成 ✅

| # | 事项 | 日期 |
|---|------|------|
| 1 | 购买腾讯云服务器（腾服） | 8/7 前 |
| 2 | DNS `api.mk-coffee.cn` 解析到 `124.220.108.118` | 8/7 前 |
| 3 | 腾服安装 Docker + 克隆项目 | 8/7 |
| 4 | 腾服部署三服务（db + backend + nginx） | 8/7 |
| 5 | HTTPS 证书申请（Let's Encrypt，到期 2026-11-06） | 8/7 |
| 6 | `https://api.mk-coffee.cn/api/` 验证通过 | 8/7 |
| 7 | 个人云 → 腾服 SSH 免密 | 8/7 |
| 8 | `DEPLOY.md` 部署文档 | 8/7 |
| 9 | 微信支付 V3 后端（统一下单 + 回调 + 签名 + 降级模拟支付） | 8/8 |
| 10 | 小程序支付流程适配（onPay 双路径 + 下单即付） | 8/8 |
| 11 | **ICP 备案通过**（mk-coffee.cn，苏州迈科咖啡有限公司） | 8/22 |
| 12 | 腾服部署最新代码（`4c5157d → 801bac8`），三服务全部 healthy | 8/22 |
| 13 | 域名决策：**弃 `.com` 用 `.cn`**（`.com` 未备案被 SNI 阻断） | 8/22 |
| 14 | 商品图接入：8 张 750×750 占位图 + 前端渲染 + 后端 image URL | 8/22 |
| 15 | `TESTING.md` 真机测试清单 | 8/22 |
| 16 | 后端 84/84 测试通过；MySQL 已托管 systemd 用户服务并自启 | 8/22 |

---

## 接下来要做（按顺序）

### 第一步：微信小程序域名白名单 🔴（现在就能做）

登录 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 开发管理 → 服务器域名，三个类型都填：

| 类型 | 域名 |
|------|------|
| request 合法域名 | `https://api.mk-coffee.cn` |
| uploadFile 合法域名 | `https://api.mk-coffee.cn` |
| downloadFile 合法域名 | `https://api.mk-coffee.cn` |

> ⚠️ **必须用 `.cn`**。`api.mk-coffee.com` 未备案、被运营商 SNI 阻断，填了真机也连不上。

### 第二步：真机测试

微信开发者工具 → 预览 → 手机扫码，按 **`TESTING.md`** 清单逐项勾选：

- [ ] 登录（授权、登录态保持、退出）
- [ ] 首页（轮播、分类、商品卡片带图）
- [ ] 商品详情（大图、规格价格联动、加购）
- [ ] 购物车（勾选、数量、删除、合并）
- [ ] 下单 → 支付（模拟支付直接成功）
- [ ] 订单（状态流转、取消恢复库存）
- [ ] 优惠券（领取、我的券、重复领取拦截）
- [ ] 收货地址（CRUD、默认地址、手机号校验）
- [ ] 门店地图（坐标、导航）
- [ ] 边界（未登录引导、弱网、连续点击）

测试后跑数据核对（预期：用户 ≥1、订单/支付流水 = 测试下单数）：

```bash
ssh dserver 'ssh ubuntu@124.220.108.118 "cd ~/MK-Coffee && docker compose exec backend python manage.py shell -c \"
from users.models import User; from orders.models import Order
from payments.models import PaymentRecord
print(User.objects.count(), Order.objects.count(), PaymentRecord.objects.count())
\""'
```

### 第三步：申请微信支付商户号

登录 [pay.weixin.qq.com](https://pay.weixin.qq.com)，以公司主体申请。  
拿到商户号后在腾服 `backend/.env` 填入 6 个 `WXPAY_*` 变量，重启 backend 即切换到真实支付（配置错误会明确报错 fail-closed）。

### 第四步：提交小程序审核

小程序后台 → 版本管理 → 提交审核。审核前确认：商品图是真实图（非占位）、门店地址真实、无测试数据。

### 第五步：公安联网备案 🔴（2026-09-21 前）

ICP 备案通过后 **30 天内**完成公安联网备案（www.beian.gov.cn），按管局要求操作。

---

## 腾服运维速查

```bash
# SSH 登录（个人云跳板）
ssh dserver 'ssh ubuntu@124.220.108.118 "..."'

# 查看服务状态
cd ~/MK-Coffee && docker compose ps

# 查看日志
docker compose logs -f

# 更新代码（注意：必须 rebuild，compose exec 跑的是旧镜像）
git pull && docker compose up -d --build

# 证书续期测试
docker run --rm \
  -v mk-coffee_certbot_www:/var/www/certbot:rw \
  -v mk-coffee_certbot_conf:/etc/letsencrypt:rw \
  certbot/certbot renew --dry-run
```

详细文档：`DEPLOY.md`（项目根目录）

---

## 注意事项

| # | 事项 | 级别 |
|---|------|------|
| 1 | 白名单必须用 `api.mk-coffee.cn`；`.com` 被 SNI 阻断已弃用 | 🔴 |
| 2 | 公安联网备案需在 2026-09-21 前完成（备案通过后 30 天内） | 🔴 |
| 3 | 证书 2026-11-06 到期，已配 cron 自动续期 | 🟡 |
| 4 | 微信域名白名单每月只能改 5 次 | 🟡 |
| 5 | 个人云 VPN 开着时到腾服 SSH 会超时（绕美国），连腾服前先关 VPN | 🟡 |
| 6 | 腾服 `git pull` 后必须 `docker compose up -d --build` 重建镜像才生效 | 🟡 |
| 7 | 微信支付默认走模拟支付，商户号到手后填 `WXPAY_*` 一行切换 | 🟢 |
| 8 | 商品图当前为占位图，提交审核前换成真实拍摄图 | 🟢 |
