"""支付模块 · 视图"""
import json
import logging

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from orders.models import Order
from .models import PaymentRecord
from .wxpay import get_wxpay_client, WXPayError
from mkcoffee.utils.notify import send_order_notify

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def payment_callback(request):
    """
    微信支付回调通知

    POST /api/payments/callback/

    微信支付 V3 回调格式：
    {
        "id": "EV-20180225112233...",
        "create_time": "2018-02-25T11:22:33+08:00",
        "resource_type": "encrypt-resource",
        "event_type": "TRANSACTION.SUCCESS",
        "summary": "支付成功",
        "resource": {
            "algorithm": "AEAD_AES_256_GCM",
            "ciphertext": "...",
            "associated_data": "...",
            "nonce": "..."
        }
    }
    """
    try:
        wxpay = get_wxpay_client()
    except WXPayError as e:
        logger.error("微信支付已启用但配置异常: %s", e)
        return Response(
            {"code": "FAIL", "message": "支付配置错误"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if not wxpay:
        logger.warning("收到支付回调但微信支付未配置")
        return Response(
            {"code": "FAIL", "message": "微信支付未配置"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        body = request.body.decode("utf-8")
        data = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.error(f"回调数据解析失败: {e}")
        return Response(
            {"code": "FAIL", "message": "数据格式错误"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 验证签名
    if not wxpay.verify_callback_sign(request.headers, body):
        logger.error("回调签名验证失败")
        return Response(
            {"code": "FAIL", "message": "签名验证失败"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 解密通知数据
    try:
        resource = data.get("resource", {})
        decrypted = wxpay.decrypt_callback(resource)
    except Exception as e:
        logger.error(f"回调解密失败: {e}")
        return Response(
            {"code": "FAIL", "message": "解密失败"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 处理支付成功事件
    event_type = data.get("event_type", "")
    if event_type != "TRANSACTION.SUCCESS":
        logger.info(f"忽略非支付成功事件: {event_type}")
        return Response({"code": "SUCCESS"})

    # 校验商户与应用标识，防止伪造/串单
    if (
        decrypted.get("appid") != settings.WX_APP_ID
        or decrypted.get("mchid") != settings.WXPAY_MCH_ID
    ):
        logger.error("回调 appid/mchid 不匹配")
        return Response(
            {"code": "FAIL", "message": "商户信息不匹配"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if decrypted.get("trade_state") != "SUCCESS":
        logger.info("忽略非成功交易状态: %s", decrypted.get("trade_state"))
        return Response({"code": "SUCCESS"})

    out_trade_no = decrypted.get("out_trade_no", "")
    transaction_id = decrypted.get("transaction_id", "")

    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(order_no=out_trade_no)

            if order.status != "pending":
                logger.warning(f"订单 {out_trade_no} 状态异常: {order.status}")
                # 已支付、已发货等状态也返回成功，避免微信重复回调
                return Response({"code": "SUCCESS"})

            # 金额一致性校验（微信支付官方强制要求，防止伪造金额）
            try:
                paid_fen = int((decrypted.get("amount") or {}).get("total"))
            except (TypeError, ValueError):
                paid_fen = None
            expected_fen = int(order.total * 100)
            if paid_fen != expected_fen:
                logger.error(
                    "回调金额不一致: 订单 %s 应收 %s 分，实收 %s 分",
                    out_trade_no, expected_fen, paid_fen,
                )
                return Response(
                    {"code": "FAIL", "message": "金额不一致"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 更新订单状态
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])

            # 更新支付记录
            PaymentRecord.objects.filter(
                order=order,
                status="initiated",
                method="wechat_jsapi",
            ).update(
                status="paid",
                transaction_id=transaction_id,
                raw_response=decrypted,
            )

            logger.info(
                f"支付回调处理成功: 订单 {out_trade_no}, 微信交易号 {transaction_id}"
            )

            # 企业微信群通知（未配置 webhook 时静默跳过，不影响回调响应）
            send_order_notify(order, event="paid")

    except Order.DoesNotExist:
        logger.error(f"订单不存在: {out_trade_no}")
        return Response(
            {"code": "FAIL", "message": "订单不存在"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 必须返回成功，否则微信会持续重试
    return Response({"code": "SUCCESS"})
