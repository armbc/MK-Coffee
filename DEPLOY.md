# 腾服部署说明

> 迈科咖啡微信小程序 · 腾讯云服务器部署文档  
> 最后更新：2026-08-23
>
> **术语约定**：本文档中「个人云」指 **HomePC**（`/home/mbcpc`，主机名 `HomePC`，用户 `mbcpc`）；
> 旧个人云服务器（Tailscale `100.105.53.87`，别名 `dserver`/`mserver`）已弃用。

---

## 服务器概况

| 项目 | 详情 |
|------|------|
| 简称 | **腾服** |
| 型号 | 锐驰型 2核2G |
| 系统 | Ubuntu Server 24.04 LTS 64bit |
| 磁盘 | 40GB SSD 云硬盘 |
| 带宽 | 200Mbps 峰值，无限流量 |
| 地域 | 上海 |
| IP | `124.220.108.118` |
| 域名 | `mk-coffee.cn`（官网，裸域，`www` 301 → 裸域）、`api.mk-coffee.cn`（主 API 域）、`api.mk-coffee.com`（旧别名，同一证书覆盖）；另有 `llm.` / `mft.mk-coffee.cn` 独立站点 |
| SSH | `ssh tengfu`（HomePC 已配免密，2026-08-23；等价 `ssh ubuntu@124.220.108.118`） |

---

## 环境清单

### Docker
- 版本：29.7.2
- 镜像加速：腾讯云 `mirror.ccs.tencentyun.com`
- 安装方式：`apt install docker-ce docker-compose-plugin`

### Docker Compose
- 插件方式：`docker compose`（V2）
- 项目目录：`~/MK-Coffee/`

### 服务端口
| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | nginx | HTTP，301 重定向到 HTTPS |
| 443 | nginx | HTTPS（TLS 1.2/1.3） |
| 3307 | MySQL | 仅监听 127.0.0.1（不对外，注意不是 3306） |
| 3100 | mkweb（Node） | 仅监听 `172.17.0.1`（Docker 网关），供 nginx 反代，不对外 |
| 8000 | Gunicorn | 容器内部，不对外 |

---

## 项目部署

### 首次部署

```bash
# 1. 克隆项目
git clone https://github.com/armbc/MK-Coffee.git
cd MK-Coffee

# 2. 配置环境变量
cp backend/.env.example backend/.env
vim backend/.env   # 填入 SECRET_KEY / DB_PASSWORD / WX_APP_SECRET 等

# 3. 创建根目录 .env（docker compose 解析 ${DB_ROOT_PASSWORD} 等用）
cp .env.example .env
vim .env           # 填入 DB_ROOT_PASSWORD / DB_USER / DB_PASSWORD

# 4. 服务器安全加固（首次部署后执行一次）
sudo bash deploy/harden-server.sh

# 5. 腾服可能预装宝塔等组件，清理占用 80 端口的进程
sudo fuser -k 80/tcp 2>/dev/null || true

# 6. 启动
docker compose up -d --build
```

### 日常更新

```bash
cd ~/MK-Coffee
git pull
docker compose up -d --build   # 仅变更的文件层会重建
```

### 查看状态

```bash
docker compose ps
docker compose logs -f          # 实时日志
docker compose logs backend     # 只看后端
```

---

## HTTPS 证书

### 证书信息
- 颁发机构：Let's Encrypt
- 有效期至：**2026-12-10**
- 证书路径：`/etc/letsencrypt/live/api.mk-coffee.com/`
- SAN 覆盖：`api.mk-coffee.cn`、`mk-coffee.cn`、`www.mk-coffee.cn`（`api.mk-coffee.com` 已于 2026-09-11 移出，该域名弃用）
- 验证方式：**webroot**（`/var/www/certbot`）——原为 standalone，会与 nginx 抢 80 端口（到期续期必失败），2026-09-11 扩展证书时一并修正；`certbot renew --dry-run` 已通过
- Docker volume：`mk-coffee_certbot_conf`

### 自动续期
crontab 已配置，每月 1 号凌晨 3 点执行：

```
0 3 1 * * docker run --rm -v mk-coffee_certbot_www:/var/www/certbot:rw -v mk-coffee_certbot_conf:/etc/letsencrypt:rw certbot/certbot renew --quiet && cd ~/MK-Coffee && docker compose restart nginx
```

### 手动续期测试

```bash
docker run --rm \
  -v mk-coffee_certbot_www:/var/www/certbot:rw \
  -v mk-coffee_certbot_conf:/etc/letsencrypt:rw \
  certbot/certbot renew --dry-run
```

---

## 官网（mk-coffee.cn）

用途：公司品牌官网，同时满足公安联网备案「网站须可访问并展示备案号」的要求。

**当前状态：✅ 已上线（2026-11-10）** —— `https://mk-coffee.cn` 200、`www` 301 → 裸域、HTTP 全量 301 到 HTTPS、证书链受信任。

### 架构（2026-11-10 起）

官网不再由 nginx 直接托管静态页，改为 **Node 应用 + nginx 反向代理**：

```
客户端 → nginx 容器（80/443）
           ├── HTTPS 主站 mk-coffee.cn → proxy_pass http://172.17.0.1:3100
           └── 其余域名（api / llm / mft）不受影响
                      ↓
         systemd 服务 mkweb（Node 22 + Hono）
           ├── 静态资源：dist/public（React 19 + Vite 构建产物）
           ├── tRPC API：/api/trpc（留言表单 leads.create）
           └── MySQL：mkweb 库（复用 mk-coffee-db-1 容器，端口 127.0.0.1:3307）
```

关键点：

- 服务单元 `mkweb.service`，`User=ubuntu`，`MemoryMax=384M`，开机自启
- 监听地址由 `HOST` 控制，生产固定 `172.17.0.1`（Docker bridge 网关）——**不监听公网接口**，外部只能经 nginx 访问
- 静态资源带内容哈希，nginx 对 `/assets/` 设一年 immutable 缓存，`/img/` 与 `/beian.png` 设 30 天
- 压缩在 nginx 侧完成（上游 Hono 不压缩）；`.js` 的实际 MIME 是 `text/javascript`，`gzip_types` 必须包含它
- 数据库账号 `mkweb` 使用 `mysql_native_password`（`caching_sha2_password` 与 mysql2 的非 TLS 连接不兼容）

### 文件组成

| 位置 | 作用 |
|------|------|
| `/home/ubuntu/mkweb/` | 应用根目录（`dist/`、`package.json`、`.env`） |
| `/home/ubuntu/mkweb/.env` | 生产环境变量（`PORT=3100`、`HOST=172.17.0.1`、`DATABASE_URL`），权限 600 |
| `/etc/systemd/system/mkweb.service` | 服务单元 |
| `deploy/nginx/conf.d/mk-coffee.cn.conf` | **生产配置**：HTTP 跳转 + 反代 Node（依赖已签发证书） |
| `deploy/nginx/conf.d/mk-coffee.cn.conf.bak-20261110` | 切换前备份（静态落地页版本） |
| `deploy/nginx/conf.d/mk-coffee.cn-http.conf.example` | 备选：仅 HTTP（全新部署、证书未就绪时顶替） |
| `deploy/site/index.html` | 旧静态备案落地页（已不再对外提供，保留备查） |

> ⚠️ `mk-coffee.cn.conf` 依赖 `/etc/letsencrypt/live/api.mk-coffee.com/` 下的证书，证书不存在会让 nginx 启动失败：全新部署请先用 `mk-coffee.cn-http.conf.example` 顶替，签好证书再换回。

### 日常更新官网

```bash
# 1. 本地构建（Node 22）
cd <web 项目>
npm run build          # = vite build + esbuild api/boot.ts → dist/boot.js

# 2. 上传产物（只传 dist 与 package.json，无需 node_modules）
tar czf /tmp/mkweb-dist.tar.gz dist package.json
scp /tmp/mkweb-dist.tar.gz tengfu:/tmp/
ssh tengfu 'tar xzf /tmp/mkweb-dist.tar.gz -C ~/mkweb && sudo systemctl restart mkweb'

# 3. 验证
curl -s -o /dev/null -w '%{http_code}\n' https://mk-coffee.cn/
systemctl status mkweb --no-pager
journalctl -u mkweb -n 50 --no-pager
```

> `dist/boot.js` 是 esbuild 自包含 bundle（含 mysql2 / drizzle / hono / tRPC），服务器**不需要** `node_modules`。

### 企业微信留言通知

留言入库后服务端会 POST 到企业微信群机器人（`api/queries/leads.ts` → `notifyWecom`）。

- Webhook 地址只从环境变量 `WECOM_WEBHOOK` 读取，**源码里不再硬编码**
- 未配置时：留言照常入库，日志记一条 `WECOM_WEBHOOK 未配置，跳过企业微信通知` 的 warn
- 通知失败不影响留言入库与接口返回，但会记 `企业微信通知失败 / 通知异常` 的 error 日志
- **必须是 `await notifyWecom(data)`**：早先是 `void notifyWecom(data)`（fire-and-forget），
  进程重启或退出时未完成的 fetch 被直接丢弃——留言进库了但群里没有任何提醒，
  2026-11-10 首次部署的测试留言就是这样丢的
- fetch 带 `AbortSignal.timeout(8000)`，避免企业微信慢响应拖死表单提交

自检：

```bash
# 1. 直接验 webhook（无响应体返回 errcode:0 即正常）
curl -s -X POST "$WECOM_WEBHOOK" -H 'Content-Type: application/json' \
  -d '{"msgtype":"text","text":{"content":"webhook 测试"}}'

# 2. 走完整链路（应返回 {"result":{"data":{"json":{"id":N}}}}）
curl -s -X POST https://mk-coffee.cn/api/trpc/leads.create \
  -H 'Content-Type: application/json' \
  -d '{"json":{"name":"测试","phone":"13800000000","intent":"other"}}'

# 3. 看是否报错
journalctl -u mkweb --since "5 minutes ago" --no-pager | grep -i "企业微信"
```

### 数据库

| 项 | 值 |
|----|----|
| 库名 | `mkweb` |
| 用户 | `mkweb`@`localhost` / `mkweb`@`%`（密码见 `~/mkweb/.env` 的 `DATABASE_URL`） |
| 表 | `leads`（合作咨询留言，`id/name/company/phone/intent/message/created_at`） |
| 连接 | 宿主机 `127.0.0.1:3307`，容器内 `db:3306` |

建表 SQL（如需重建）：

```sql
CREATE TABLE IF NOT EXISTS leads (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  company VARCHAR(128) NULL,
  phone VARCHAR(32) NOT NULL,
  intent ENUM('soe','commercial','beans','gift','other') NOT NULL,
  message TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 备案合规

- 备案号必须出现在**首屏 HTML 源码**中（不执行 JS 的核验方也能读到）：`index.html` 的 `<noscript>` 块内置 `苏ICP备2026059759号-1` 与 `苏公网安备32058302006935号`
- React 渲染后的 `<footer>` 同样展示两个备案号并链接到 `beian.miit.gov.cn` / `beian.mps.gov.cn`
- 修改页脚或 `index.html` 后务必回归检查这两处

### 历史：静态备案落地页（2026-09-11 → 2026-11-10）

最初用途是公安联网备案「新办网站」核验——要求裸域可直接打开并展示 ICP 备案号；此前裸域与 www 均无 DNS 解析、nginx 也无对应站点。

1）DNSPod 添加解析（备案填报的网站访问地址是裸域）：

```
@    A    124.220.108.118
www  A    124.220.108.118
```

2）部署静态站点：`docker compose up -d --force-recreate nginx`

3）签发/扩展证书（webroot，扩展后 SAN = api.mk-coffee.cn + mk-coffee.cn + www.mk-coffee.cn）：

```bash
docker run --rm \
  -v mk-coffee_certbot_www:/var/www/certbot:rw \
  -v mk-coffee_certbot_conf:/etc/letsencrypt:rw \
  certbot/certbot certonly --webroot -w /var/www/certbot \
    --cert-name api.mk-coffee.com \
    -d api.mk-coffee.cn -d mk-coffee.cn -d www.mk-coffee.cn
```

4）`docker compose restart nginx` 生效 HTTPS 配置

5）验证：公网 `https://mk-coffee.cn` 200（证书链受信任）、`http://mk-coffee.cn` 与 `http://www.mk-coffee.cn` 均 301 → HTTPS、`api.mk-coffee.cn` 回归 200、`certbot renew --dry-run` 通过

6）公安备案号下发（`苏公网安备32058302006935号`，2026-09-15）后补入 footer 并重新部署

7）2026-11-10 切换为品牌官网，静态页归档为 `deploy/site/index.html`，不再对外提供

---

## Docker Compose 架构

```
docker compose (~/MK-Coffee/)
├── db (mysql:8.0)
│   ├── volume: mysql_data → /var/lib/mysql
│   └── port: 127.0.0.1:3306
├── backend (mk-coffee-backend, Python 3.12 + Gunicorn)
│   ├── env_file: backend/.env
│   ├── environment: DB_HOST=db
│   └── volume: static_volume → /app/staticfiles
└── nginx (nginx:alpine)
    ├── ports: 80:80, 443:443
    ├── config: deploy/nginx/conf.d/default.conf
    └── volumes: static_volume, certbot_www, certbot_conf
```

---

## 关键问题的修复记录

### Dockerfile 镜像加速
- apt 源 → 清华 `mirrors.tuna.tsinghua.edu.cn`
- pip 源 → 清华 `pypi.tuna.tsinghua.edu.cn/simple`

### 非 ASCII 数据库密码
- 问题：PyMySQL 在 MySQL 8.0 SHA2 认证中，对非 ASCII 密码做 latin-1 编码时报错
- 修复：`base.py` 中检测非 ASCII 密码，自动转为 bytes 再传递

### staticfiles 权限
- 问题：Docker volume 初始权限为 root，appuser 无法写入
- 修复：entrypoint 以 root 运行 `collectstatic`，完成后 `su appuser` 启动 gunicorn

---

## 故障排查

### nginx 返回 502
```bash
docker compose logs backend --tail 30
```
常见原因：数据库连接失败、migrate 失败、collectstatic 权限不足。

> 若 502 只出现在 `mk-coffee.cn`（官网），先查 Node 服务：
> ```bash
> systemctl status mkweb --no-pager
> journalctl -u mkweb -n 50 --no-pager
> ss -tlnp | grep 3100        # 应监听 172.17.0.1:3100
> curl -s http://172.17.0.1:3100/api/trpc/ping
> ```
> 服务正常但 nginx 连不上，核对 `mk-coffee.cn.conf` 里的 `proxy_pass http://172.17.0.1:3100`
> 与 `docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'` 是否一致。

### 证书过期
```bash
# 检查证书到期时间
echo | openssl s_client -servername api.mk-coffee.com -connect 124.220.108.118:443 2>/dev/null | openssl x509 -noout -dates
```

### 容器全部重启
```bash
docker compose down && docker compose up -d
```

### MySQL 数据备份
```bash
docker compose exec db mysqldump -u root -p"$DB_PASSWORD" mkcoffee > backup.sql
```

---

## 安全加固

服务器安全由 `deploy/harden-server.sh` 一键完成。首次部署后执行：

```bash
sudo bash deploy/harden-server.sh
```

加固内容包括：

| 层面 | 措施 |
|------|------|
| SSH | 禁用 root 登录、密码认证（仅密钥）、MaxAuthTries=3 |
| fail2ban | SSH 3 次失败封禁 2 小时 |
| UFW 防火墙 | 仅开放 22/80/443，其余全部拒绝 |
| 自动更新 | unattended-upgrades 每日自动安装安全补丁 |
| 内核参数 | TCP syncookies、禁用 ICMP 重定向、RP 过滤 |

### Docker 容器安全（docker-compose.yml 内置）

| 措施 | 说明 |
|------|------|
| `no-new-privileges` | 禁止容器内提权 |
| `read_only: true` | backend + nginx 只读根文件系统 |
| 资源限制 | 每容器 CPU/内存上限 |
| 日志轮转 | json-file 驱动，10MB × 3 文件 |
| MySQL 端口 | 仅绑定 127.0.0.1，不对外暴露 |
| 应用用户 | Gunicorn 以 appuser 运行，非 root |

### Django 安全（production.py）

| 措施 | 说明 |
|------|------|
| DEBUG=False | 禁止错误页面泄露 |
| HSTS | max-age=2 年，含子域 |
| Secure Cookie | 仅 HTTPS 传输 |
| XSS/Content-Type 防护 | 浏览器安全头 |
| 日志 | 生产环境 WARNING 级别 |
