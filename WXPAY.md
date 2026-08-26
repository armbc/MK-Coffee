# 微信支付接入指南 💳

> **用途**：迈科咖啡小程序从「模拟支付」切换到「微信支付 V3」的完整操作手册。
> **状态**：模拟支付运行中（`WXPAY_ENABLED=false`）｜商户号待申请
> 最后更新：2026-08-26

---

## 一、为什么需要商户号

当前小程序支付走的是**模拟支付**（点支付直接成功），仅用于开发/验收。正式上线前必须切换到真实微信支付，否则用户可以「免费下单」。

后端已内置 fail-closed 保护：**配置了 `WXPAY_ENABLED=true` 但参数缺失/错误时，下单会直接报错**，绝不会静默降级回模拟支付（安全审查 #1 的修复）。

---

## 二、申请商户号（公司主体，预计 1~7 个工作日）

### 申请入口

1. 打开 [pay.weixin.qq.com](https://pay.weixin.qq.com) → 「成为商家」/「注册商户号」
2. 主体类型选**企业**（苏州迈科咖啡有限公司），按页面引导提交

### 需要准备的材料

| 材料 | 说明 |
|------|------|
| 营业执照 | 原件照片/扫描件，经营范围需含食品/咖啡销售 |
| 法人身份证 | 正反面照片 |
| 对公银行账户 | 用于结算，开户名须与营业执照一致 |
| 超级管理员 | 建议填陈东（法人），需本人微信扫码确认 |
| 结算费率/周期 | 默认费率 0.6%（可谈），T+1 结算 |

### 申请完成后确认 4 项

商户平台 →「账户中心」逐项核对，**全齐了再配置**：

| # | 项目 | 获取位置 | 对应变量 |
|---|------|---------|---------|
| 1 | 商户号（10 位数字） | 账户中心 → 商户信息 | `WXPAY_MCH_ID` |
| 2 | APIv3 密钥（32 位） | 账户中心 → API 安全 → 设置 APIv3 密钥 | `WXPAY_API_V3_KEY` |
| 3 | 商户 API 证书序列号 | 账户中心 → API 安全 → 申请证书（需安装微信支付证书工具，生成后序列号在证书详情） | `WXPAY_SERIAL_NO` |
| 4 | 商户私钥 | 申请证书时工具生成的 `apiclient_key.pem` 文件内容 | `WXPAY_PRIVATE_KEY` |

### 商户号与小程序绑定（必须）

1. 小程序后台 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 微信支付 → 关联商户号（用商户号 + 超级管理员微信确认）
2. 商户平台 → 产品中心 → AppID 账号管理 → 确认已关联小程序的 AppID（`WX_APP_ID`）
3. 商户平台 → 产品中心 → 开发配置 → JSAPI 支付 → 支付目录填 `https://api.mk-coffee.cn/`

> 绑定和支付目录配置是真实支付能调起的关键，漏了会报「商户号与 AppID 不匹配」。

---

## 三、配置步骤（拿到 4 项后，约 5 分钟）

### 1. 登录腾服，编辑 `.env`

```bash
ssh dserver 'ssh ubuntu@124.220.108.118 "cd ~/MK-Coffee && vi backend/.env"'
```

找到微信支付段，改成：

```bash
WXPAY_ENABLED=true
WXPAY_MCH_ID=你的10位商户号
WXPAY_API_V3_KEY=你的32位APIv3密钥
WXPAY_SERIAL_NO=你的证书序列号
# 私钥两种填法（推荐路径方式，避免 .env 多行转义问题）：
# 方式一：PEM 原文（含 BEGIN/END 行，用 \n 转义换行）
WXPAY_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
# 方式二：文件路径（把 apiclient_key.pem 放到 backend/wxpay/ 后填下面的路径，容器已挂载该目录）
# WXPAY_PRIVATE_KEY=/app/wxpay/apiclient_key.pem
# 以下两项已配好，不要动：
# WXPAY_NOTIFY_URL=https://api.mk-coffee.cn/api/payments/callback/
# WX_APP_ID=wx...（已在文件中）
```

> ⚠️ **私钥格式**：代码同时支持 PEM 原文和文件路径两种方式。`.env` 文件格式不支持多行值，PEM 原文需用 `\n` 转义；**推荐方式二**——把 `apiclient_key.pem` 放到腾服 `~/MK-Coffee/backend/wxpay/` 目录（docker-compose 已挂载到容器 `/app/wxpay/`，该目录在 `.gitignore` 中，不会入库），`WXPAY_PRIVATE_KEY` 填 `/app/wxpay/apiclient_key.pem` 即可。

### 2. 重启 backend 使配置生效

```bash
cd ~/MK-Coffee && docker compose restart backend
```

### 3. 验证配置加载成功

```bash
docker compose logs backend --tail 30
```

- 看到 `微信支付已启用` 或启动无 `WXPayError` → 配置成功
- 看到 `WXPAY_ENABLED=true 但配置缺失: xxx` → 有变量没填对，按提示补齐（fail-closed 会阻止下单，不会出「免费单」）

---

## 四、验证真实支付（真机，必须）

> ⚠️ **微信开发者工具不支持拉起真实微信支付**（模拟器无微信支付环境），必须用**真机**验证。

1. 真机打开体验版（或开发者工具「预览」扫码）
2. 登录 → 加购 → 下单 → 点「立即支付」
3. 预期弹起微信支付收银台（指纹/密码），支付成功
4. 支付成功后核对：
   - 订单状态变「已支付」
   - 企业微信群收到订单通知（金额 = 实付金额，含优惠券抵扣）
   - 后台：`https://api.mk-coffee.cn/admin/` → 支付记录（PaymentRecord）有真实流水

### 验证失败排查

| 现象 | 可能原因 |
|------|---------|
| 下单 500，日志有 `配置缺失` | .env 变量没填全（fail-closed 生效，正常） |
| 报 `商户号与AppID不匹配` | 商户号未与小程序 AppID 绑定（见二-4） |
| 报 `支付目录不正确` | JSAPI 支付目录没配 `https://api.mk-coffee.cn/` |
| 收银台没弹起，页面卡住 | 真机网络/白名单问题，或未用真机（开发者工具模拟器不支持） |
| 支付成功但订单未变已支付 | 回调没到——检查 `WXPAY_NOTIFY_URL` 是否为 `.cn` 且公网可访问 |
| 企业微信没收到通知 | `WECOM_WEBHOOK_URL` 未配置或失效（通知失败静默跳过，不影响支付） |

### 回滚到模拟支付

```bash
# .env 里改 WXPAY_ENABLED=false 后
docker compose restart backend
```

---

## 五、常见问题

1. **平台证书**：V3 首次调用会自动下载微信平台证书并缓存在临时目录（可用 `WXPAY_CERT_PATH` 指定持久化路径，避免容器重建后重新下载）。密钥轮换后需清掉缓存重新下载。
2. **回调地址必须 `.cn`**：`api.mk-coffee.com` 未备案被运营商 SNI 阻断，回调会失败。已统一为 `https://api.mk-coffee.cn/api/payments/callback/`。
3. **私钥填法**：代码支持两种——① PEM 原文（`.env` 里用 `\n` 转义换行，易错）；② **文件路径（推荐）**：把 `apiclient_key.pem` 放到腾服 `~/MK-Coffee/backend/wxpay/`，填 `WXPAY_PRIVATE_KEY=/app/wxpay/apiclient_key.pem`（docker-compose 已挂载该目录为只读，`.gitignore` 已排除）。路径错误会报「商户私钥文件读取失败」，不会静默降级。
4. **测试支付**：真实支付不可「只测不发钱」。小额测试（如 0.01 元商品）可临时改商品价格，测完恢复；正式运营前记得清掉测试订单（`clear_test_data`）。
5. **退款**：当前后端未实现退款接口。若运营需要（如取消已支付订单），需在 payments 模块补 `refund` API（V3 退款接口 + 回调），列入后续迭代。

---

## 六、相关文件

| 文件 | 作用 |
|------|------|
| `backend/payments/wxpay.py` | V3 客户端：签名、统一下单、回调验签解密、平台证书 |
| `backend/payments/views.py` | `POST /api/payments/callback/` 回调处理 |
| `backend/.env.example` | 变量模板（`WXPAY_NOTIFY_URL` 已为 `.cn`） |
| `miniapp/pages/order/order.js` | 前端支付：`method=mock` 直接成功 / `wechat_jsapi` 调 `wx.requestPayment` |

---

## 更新记录

- **2026-08-26**：创建。商户号未申请，模拟支付运行中；`.env.example` 回调地址已从 `.com` 修正为 `.cn`。
