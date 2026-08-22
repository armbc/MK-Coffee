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
| 17 | 白名单配置（request/uploadFile/downloadFile = `api.mk-coffee.cn`）+ IP 白名单（`124.220.108.118`）生效 | 8/22 |
| 18 | AppSecret 修复（占位符 → 真实密钥，腾服+本地同步，登录链路验证通过） | 8/22 |
| 19 | 体验版 `0.9.0` 已上传并设为体验版；同事加入项目成员参与验收 | 8/22 |

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

### 第二步：真机/体验版验收 🔄 进行中

- 开发者工具预览 + 体验版（0.9.0）双通道，按 **`TESTING.md`** 清单逐项勾选
- 注意：Mac 本地代码务必 `git pull` 到最新（旧代码 apiBase 是 .com 会导致首页无商品）
- 验收通过后：**清测试数据 → 过「提交审核前 Checklist」（TESTING.md 末尾）→ 提交审核**

### 第三步：申请微信支付商户号

登录 [pay.weixin.qq.com](https://pay.weixin.qq.com)，以公司主体申请。  
拿到商户号后在腾服 `backend/.env` 填入 6 个 `WXPAY_*` 变量，重启 backend 即切换到真实支付（配置错误会明确报错 fail-closed）。

### 第四步：提交小程序审核

按 **TESTING.md 末尾「提交审核前 Checklist」** 逐项过：

1. 清理测试数据（保留种子商品）
2. 商品图换真实图（至少 4 张主推）
3. 确认门店真实坐标
4. 配置《用户隐私保护指引》
5. 选对服务类目（咖啡/食品销售类，可能需要资质）
6. 「关于」页展示 ICP 备案号
7. 版本号 `1.0.0` 提交

后台 → 版本管理 → 提交审核。

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
