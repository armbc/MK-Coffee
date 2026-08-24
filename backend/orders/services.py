"""订单模块 · 业务服务层

核心订单流程的状态流转逻辑在此层实现，供 DRF API 与 Django Admin 共用，
保证状态流转规则只有一份、不会绕过业务校验。
"""
from django.db import transaction

from .models import Order


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
