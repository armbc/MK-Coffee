"""订单模块 · 业务服务层

核心订单流程的状态流转逻辑在此层实现，供 DRF API 与 Django Admin 共用，
保证状态流转规则只有一份、不会绕过业务校验。
"""
from django.db import transaction
from django.db.models import F

from coupons.models import UserCoupon
from products.models import Product, Spec

from .models import CartItem, Order


def ship_order(order):
    """标记订单为已发货。

    仅「已支付(paid)」状态可发货，返回 (order, error_msg)：
    - 成功：error_msg 为 None，订单状态变为 shipped
    - 失败：error_msg 为原因，订单状态不变（幂等，不重复发货）

    供 OrderViewSet.ship（商家发货 API）与
    OrderAdmin.mark_shipped（后台批量发货按钮）共用。
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != "paid":
            return order, f"订单状态为「{order.get_status_display()}」，无法发货"
        order.status = "shipped"
        order.save(update_fields=["status", "updated_at"])
        return order, None


def cancel_order_to_cart(order):
    """取消待支付订单并把商品退回购物车（顾客支付弹窗「退回购物车」）。

    仅「待支付(pending)」可操作，返回 (order, cart_count, error_msg)：
    - 成功：error_msg 为 None，订单取消、库存/优惠券恢复、商品写回购物车（同品同规格合并数量）
    - 失败：error_msg 为原因，订单状态不变（幂等保护）

    与 cancel API 的取消语义一致（状态/库存/优惠券），额外把订单明细退回购物车。
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != "pending":
            return order, 0, f"订单状态为「{order.get_status_display()}」，无法退回购物车"

        order.status = "cancelled"
        order.save(update_fields=["status", "updated_at"])

        # 释放优惠券（本单核销的券退回，可再次使用）
        UserCoupon.objects.filter(order=order, status="used").update(
            status="unused", order=None, used_at=None,
        )

        # 原子恢复库存
        for item in order.items.select_related("spec", "product"):
            if item.spec:
                Spec.objects.filter(pk=item.spec.pk).update(stock=F("stock") + item.quantity)
            else:
                Product.objects.filter(pk=item.product.pk).update(stock=F("stock") + item.quantity)

        # 写回购物车：同用户同商品同规格合并数量（无规格用 spec__isnull 匹配，兼容 MySQL NULL 语义）
        cart_count = 0
        for item in order.items.select_related("spec", "product"):
            existing_qs = CartItem.objects.filter(user=order.user, product=item.product)
            if item.spec_id:
                existing = existing_qs.filter(spec=item.spec).first()
            else:
                existing = existing_qs.filter(spec__isnull=True).first()
            if existing:
                existing.quantity += item.quantity
                existing.save(update_fields=["quantity", "updated_at"])
            else:
                CartItem.objects.create(
                    user=order.user, product=item.product,
                    spec=item.spec, quantity=item.quantity,
                )
            cart_count += item.quantity

        return order, cart_count, None
