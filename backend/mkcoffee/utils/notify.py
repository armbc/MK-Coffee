"""订单通知工具：企业微信群机器人

配置（backend/.env）：
    WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

未配置或推送失败时只记日志，绝不抛出异常、不影响支付/下单主流程。
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# 企业微信机器人频率限制：每分钟最多 20 条，通知量小无需排队


def send_order_notify(order, event="paid"):
    """订单事件 → 企业微信群机器人推送

    event:
        "paid"    顾客支付成功（模拟支付与真实微信支付回调统一入口）
        "created" 新订单（预留，暂未接入）
    """
    url = (getattr(settings, "WECOM_WEBHOOK_URL", "") or "").strip()
    if not url:
        logger.info("未配置 WECOM_WEBHOOK_URL，跳过企业微信订单通知")
        return False

    head = "💰 顾客已支付" if event == "paid" else "🟢 新订单待处理"

    lines = [
        f"**【{head}】**",
        f"订单号：`{order.order_no}`",
        f"金额：**¥{order.total}**",
    ]
    receiver = order.receiver_name or "-"
    phone = order.receiver_phone or "-"
    address = order.receiver_address or "（未填）"
    lines.append(f"收货：{receiver}  {phone}")
    lines.append(f"地址：{address}")
    lines.append("明细：")
    for oi in order.items.all():
        spec = f"（{oi.spec_name}）" if oi.spec_name else ""
        lines.append(f"> {oi.product_name}{spec} × {oi.quantity}  ¥{oi.price}")
    lines.append(f"时间：{order.created_at:%Y-%m-%d %H:%M}")

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": "\n".join(lines)},
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
        if data.get("errcode") == 0:
            logger.info("企业微信订单通知发送成功: %s", order.order_no)
            return True
        logger.error("企业微信通知发送失败: HTTP %s %s", resp.status_code, data)
    except Exception as exc:  # noqa: BLE001 通知失败绝不影响支付主流程
        logger.error("企业微信通知异常: %s", exc)
    return False
