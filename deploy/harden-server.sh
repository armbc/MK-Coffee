#!/bin/bash
# ============================================================
# 迈科咖啡 · 腾服安全加固脚本
# 执行方式：ssh ubuntu@124.220.108.118 'bash -s' < harden-server.sh
#          或在腾服上直接 bash harden-server.sh
# ============================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; }

echo "============================================"
echo " 迈科咖啡 · 腾服安全加固"
echo " $(date '+%Y-%m-%d %H:%M')"
echo "============================================"
echo ""

# ---- 1. 检查当前状态 ----
log "1/6 检查当前安全状态..."

echo ""
echo "--- 监听端口 ---"
ss -tlnp 2>/dev/null | grep LISTEN || true

echo ""
echo "--- 防火墙状态 ---"
if command -v ufw &>/dev/null; then
    sudo ufw status verbose 2>/dev/null || true
else
    warn "ufw 未安装"
fi

echo ""
echo "--- SSH 配置摘要 ---"
grep -E '^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|Port)' /etc/ssh/sshd_config 2>/dev/null | grep -v '^#' || true

echo ""
echo "--- fail2ban 状态 ---"
if systemctl is-active --quiet fail2ban 2>/dev/null; then
    sudo fail2ban-client status 2>/dev/null || true
else
    warn "fail2ban 未运行"
fi

echo ""
echo "--- 自动更新状态 ---"
if systemctl is-active --quiet unattended-upgrades 2>/dev/null; then
    log "unattended-upgrades 已运行"
else
    warn "unattended-upgrades 未运行"
fi

echo ""

# ---- 2. SSH 加固 ----
log "2/6 SSH 加固..."

SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_CHANGED=false

# 检查是否已有密钥认证成功记录（安全前提）
KEY_AUTH_OK=false
if sudo grep -q 'Accepted publickey' /var/log/auth.log 2>/dev/null; then
    KEY_AUTH_OK=true
    log "检测到公钥认证成功记录，将禁用密码登录"
fi

backup_sshd() {
    if [ ! -f "${SSHD_CONFIG}.bak.$(date +%Y%m%d)" ]; then
        sudo cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak.$(date +%Y%m%d)"
        log "已备份 sshd_config → ${SSHD_CONFIG}.bak.$(date +%Y%m%d)"
    fi
}

set_sshd() {
    local key="$1" val="$2"
    if sudo grep -q "^${key} " "$SSHD_CONFIG"; then
        sudo sed -i "s/^${key} .*/${key} ${val}/" "$SSHD_CONFIG"
    else
        echo "${key} ${val}" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    fi
    SSHD_CHANGED=true
}

backup_sshd

set_sshd "PermitRootLogin" "no"
set_sshd "MaxAuthTries" "3"
set_sshd "ClientAliveInterval" "300"
set_sshd "ClientAliveCountMax" "2"
set_sshd "X11Forwarding" "no"

if $KEY_AUTH_OK; then
    set_sshd "PasswordAuthentication" "no"
    set_sshd "ChallengeResponseAuthentication" "no"
    set_sshd "UsePAM" "no"
    log "已禁用密码登录（仅密钥认证）"
else
    warn "未检测到公钥认证记录，保留密码登录。"
    warn "请确认密钥可用后手动执行: sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
fi

if $SSHD_CHANGED; then
    sudo sshd -t && sudo systemctl reload sshd
    log "SSH 配置已生效"
fi

# ---- 3. fail2ban ----
log "3/6 安装配置 fail2ban..."

if ! command -v fail2ban-client &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq fail2ban
    log "fail2ban 已安装"
fi

# 创建 jail.local（如果不存在）
if [ ! -f /etc/fail2ban/jail.local ]; then
    sudo tee /etc/fail2ban/jail.local > /dev/null <<'FAIL2BAN'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = ssh
maxretry = 3
bantime = 7200
FAIL2BAN
    sudo systemctl restart fail2ban
    log "fail2ban 已配置（SSH: 3 次失败封 2 小时）"
else
    sudo systemctl restart fail2ban
    log "fail2ban 已重启"
fi

# ---- 4. UFW 防火墙 ----
log "4/6 配置 UFW 防火墙..."

# Docker 会绕过 UFW，但 UFW 仍能保护 SSH 等宿主机端口
# Docker 端口安全由 docker-compose 的 127.0.0.1 绑定保证

if command -v ufw &>/dev/null; then
    sudo ufw --force disable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp comment 'SSH'
    sudo ufw allow 80/tcp comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'
    sudo ufw --force enable
    sudo ufw status verbose
    log "UFW 已启用：仅开放 22/80/443"
else
    warn "ufw 未安装，跳过"
fi

# ---- 5. 自动安全更新 ----
log "5/6 配置自动安全更新..."

if ! dpkg -l unattended-upgrades &>/dev/null; then
    sudo apt-get install -y -qq unattended-upgrades
fi

sudo tee /etc/apt/apt.conf.d/20auto-upgrades > /dev/null <<'AUTO'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
AUTO

sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null <<'UNATTEND'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
UNATTEND

sudo systemctl restart unattended-upgrades 2>/dev/null || sudo systemctl enable unattended-upgrades
log "unattended-upgrades 已配置（安全更新自动安装，不自动重启）"

# ---- 6. 内核参数加固 ----
log "6/6 内核参数加固..."

if ! grep -q "mk-coffee" /etc/sysctl.d/99-security.conf 2>/dev/null; then
    sudo tee -a /etc/sysctl.d/99-security.conf > /dev/null <<'SYSCTL'
# 迈科咖啡 · 安全内核参数
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
SYSCTL
    sudo sysctl -p /etc/sysctl.d/99-security.conf
    log "内核参数已加固"
else
    log "内核参数已存在，跳过"
fi

# ---- 完成 ----
echo ""
echo "============================================"
echo " 加固完成！"
echo "============================================"
echo ""
echo "变更摘要："
echo "  SSH: PermitRootLogin=no, MaxAuthTries=3"
if $KEY_AUTH_OK; then
    echo "  SSH: PasswordAuthentication=no（仅密钥）"
fi
echo "  fail2ban: SSH 3 次失败封 2 小时"
echo "  UFW: 仅开放 22/80/443"
echo "  unattended-upgrades: 安全更新自动安装"
echo "  sysctl: TCP syncookies, 禁用重定向"
echo ""
echo "⚠️  请保持当前 SSH 会话不断开，新开一个终端验证登录正常后再关闭。"
