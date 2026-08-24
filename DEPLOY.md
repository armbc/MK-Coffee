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
| 域名 | `api.mk-coffee.cn`（主域，A 记录解析到上述 IP），`api.mk-coffee.com`（别名，同一证书覆盖） |
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
| 3306 | MySQL | 仅监听 127.0.0.1（不对外） |
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
- 有效期至：**2026-11-05**
- 证书路径：`/etc/letsencrypt/live/api.mk-coffee.com/`
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
