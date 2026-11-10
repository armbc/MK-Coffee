#!/bin/bash
# ============================================================
# 迈科咖啡 · MySQL 备份脚本
# ============================================================
# 用法：
#   bash deploy/backup-mysql.sh              # 备份到 ~/backup/mysql
#   BACKUP_DIR=/data/bk bash deploy/backup-mysql.sh
#   bash deploy/backup-mysql.sh --list       # 列出已有备份
#
# 为什么是这么写的（三个坑，缺一个都会「看起来成功」）：
#
#   1. 密码是 bytes 且含非 ASCII 字符
#      Django 的 base.py 检测到非 ASCII 密码会转 bytes 传给 PyMySQL。
#      直接 echo "$PASSWORD" 会得到 b'...' 字面量或丢字节。
#      → 用 base64 传，边界干净。
#
#   2. root@localhost 和 root@% 是两个不同的 MySQL 用户
#      docker exec 默认走 socket，MySQL 识别为 root@localhost（密码不同）；
#      Django 走 TCP，识别为 root@%。不加 -h 会报 Access denied。
#      → 强制 -h 127.0.0.1 --protocol=TCP。
#
#   3. 空 dump 也会产出合法的 20 字节 gzip，且 exit code 为 0
#      mysqldump 失败 → 空输入 → gzip 仍生成合法文件 → cron 无感知。
#      → 校验尾部 "-- Dump completed" 和 CREATE TABLE 数量，否则删文件并非零退出。
#
# 退出码：0 全部成功；1 任一库失败（cron 会据此发邮件/告警）
# ============================================================

set -uo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backup/mysql}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_CONTAINER="${DB_CONTAINER:-mk-coffee-db-1}"
APP_CONTAINER="${APP_CONTAINER:-mk-coffee-backend-1}"
DATABASES="${DATABASES:-mkcoffee mkweb}"
# 完整性校验期望的最少建表数（mkcoffee 22 张、mkweb 1 张）；低于该值视为异常
MIN_TABLES="${MIN_TABLES:-mkcoffee:20 mkweb:1}"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
fail() { log "ERROR: $*"; exit 1; }

# ---- --list：列出已有备份 ----
if [ "${1:-}" = "--list" ]; then
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "备份目录不存在：$BACKUP_DIR"
        exit 0
    fi
    # 用「时间  大小  文件名」的行格式，避开中文表头的宽度对齐问题
    echo "备份目录：$BACKUP_DIR"
    find "$BACKUP_DIR" -name '*.sql.gz' -type f -printf '%TY-%Tm-%Td %TH:%TM\t%s\t%f\n' 2>/dev/null \
        | sort \
        | awk -F'\t' '{printf "  %s  %8.1fK  %s\n", $1, $2/1024, $3}'
    n=$(find "$BACKUP_DIR" -name '*.sql.gz' -type f | wc -l)
    echo "共 $n 个备份"
    exit 0
fi

# ---- 前置检查 ----
command -v docker >/dev/null || fail "docker 未安装"
docker inspect "$DB_CONTAINER" >/dev/null 2>&1 || fail "容器不存在：$DB_CONTAINER"
docker inspect "$APP_CONTAINER" >/dev/null 2>&1 || fail "容器不存在：$APP_CONTAINER"

mkdir -p "$BACKUP_DIR" || fail "无法创建备份目录：$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# ---- 读取数据库密码 ----
# 从 Django 配置取（与后端实际使用的凭据完全一致），base64 传递。
# 密码全程不出现在命令行参数、日志或进程列表里。
DBP_B64=$(docker exec "$APP_CONTAINER" python -c '
import os, django, sys, base64
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mkcoffee.settings.production")
django.setup()
from django.conf import settings
p = settings.DATABASES["default"]["PASSWORD"]
raw = p.encode("latin-1") if isinstance(p, str) else p
sys.stdout.write(base64.b64encode(raw).decode("ascii"))
' 2>/dev/null) || fail "无法从 $APP_CONTAINER 读取数据库凭据"

[ -n "$DBP_B64" ] || fail "数据库凭据为空"
DBP=$(printf '%s' "$DBP_B64" | base64 -d) || fail "凭据 base64 解码失败"
[ -n "$DBP" ] || fail "数据库密码解码后为空"

# ---- 单库 dump ----
dump_db() {
    local db="$1"
    docker exec -e MYSQL_PWD="$DBP" "$DB_CONTAINER" \
        mysqldump -uroot -h 127.0.0.1 --protocol=TCP \
        --single-transaction --quick --routines \
        --default-character-set=utf8mb4 \
        "$db"
}

min_tables_for() {
    local db="$1" pair
    for pair in $MIN_TABLES; do
        [ "${pair%%:*}" = "$db" ] && { echo "${pair##*:}"; return; }
    done
    echo 1
}

# ---- 主流程 ----
STAMP=$(date '+%Y%m%d-%H%M%S')
RC=0
SUMMARY=""

for db in $DATABASES; do
    final="$BACKUP_DIR/${db}-${STAMP}.sql.gz"
    tmp="$BACKUP_DIR/.tmp-${db}-${STAMP}.sql.gz"
    errf="$BACKUP_DIR/.err-${db}-${STAMP}.log"

    # 临时文件用 600：dump 含手机号、地址等个人信息
    umask 077

    if ! dump_db "$db" 2>"$errf" | gzip -6 > "$tmp"; then
        log "FAIL  $db：mysqldump 失败"
        [ -s "$errf" ] && sed 's/^/        /' "$errf" | head -3
        rm -f "$tmp" "$errf"
        RC=1
        SUMMARY="${SUMMARY}${db}=FAIL "
        continue
    fi

    # 校验 1：文件非空（空 dump 经 gzip 会得到 20 字节的合法文件）
    size=$(stat -c%s "$tmp" 2>/dev/null || echo 0)
    if [ "$size" -le 100 ]; then
        log "FAIL  $db：产物仅 ${size} 字节，疑似空 dump（mysqldump 静默失败）"
        [ -s "$errf" ] && sed 's/^/        /' "$errf" | head -3
        rm -f "$tmp" "$errf"
        RC=1
        SUMMARY="${SUMMARY}${db}=EMPTY "
        continue
    fi

    # 校验 2：gzip 完整
    if ! gzip -t "$tmp" 2>/dev/null; then
        log "FAIL  $db：gzip 校验失败（文件损坏）"
        rm -f "$tmp" "$errf"
        RC=1
        SUMMARY="${SUMMARY}${db}=CORRUPT "
        continue
    fi

    # 校验 3：尾部有 Dump completed 标记
    tail_line=$(zcat "$tmp" 2>/dev/null | tail -1)
    case "$tail_line" in
        *"Dump completed"*) ;;
        *)
            log "FAIL  $db：缺少 '-- Dump completed' 结尾，dump 被截断"
            rm -f "$tmp" "$errf"
            RC=1
            SUMMARY="${SUMMARY}${db}=TRUNCATED "
            continue
            ;;
    esac

    # 校验 4：建表数量不低于预期
    n_tables=$(zcat "$tmp" 2>/dev/null | grep -c '^CREATE TABLE' || true)
    want=$(min_tables_for "$db")
    if [ "$n_tables" -lt "$want" ]; then
        log "FAIL  $db：仅 $n_tables 张表，低于预期 $want"
        rm -f "$tmp" "$errf"
        RC=1
        SUMMARY="${SUMMARY}${db}=FEWTABLES($n_tables) "
        continue
    fi

    # 全部通过，落正式文件名
    mv "$tmp" "$final"
    chmod 600 "$final"
    sha=$(sha256sum "$final" | cut -d' ' -f1)
    printf '%s  %s\n' "$sha" "$(basename "$final")" >> "$BACKUP_DIR/SHA256SUMS"

    # 人类可读大小；小于 1K 时补上 B，避免只显示一个裸数字
    if [ "$size" -ge 1048576 ]; then
        human=$(awk -v s="$size" 'BEGIN{printf "%.1fM", s/1048576}')
    elif [ "$size" -ge 1024 ]; then
        human=$(awk -v s="$size" 'BEGIN{printf "%.1fK", s/1024}')
    else
        human="${size}B"
    fi

    log "OK    $db：$(basename "$final")  $human  ${n_tables} 张表  sha256=${sha:0:12}…"
    SUMMARY="${SUMMARY}${db}=OK "
    rm -f "$errf"
done

# ---- 轮转 ----
if [ "$RETENTION_DAYS" -gt 0 ] 2>/dev/null; then
    deleted=$(find "$BACKUP_DIR" -maxdepth 1 -name '*.sql.gz' -type f -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
    [ "$deleted" -gt 0 ] && log "轮转：删除 $deleted 个超过 ${RETENTION_DAYS} 天的备份"
fi

# 清理残留临时文件（>1 天的，避免误删正在写的）
find "$BACKUP_DIR" -maxdepth 1 -name '.tmp-*' -type f -mtime +1 -delete 2>/dev/null || true
find "$BACKUP_DIR" -maxdepth 1 -name '.err-*' -type f -mtime +1 -delete 2>/dev/null || true

log "汇总：${SUMMARY}(备份目录 $BACKUP_DIR)"
exit "$RC"
