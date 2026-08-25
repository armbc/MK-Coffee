"""清除测试数据：订单/购物车/优惠券/地址/用户（保留商品与分类）"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from coupons.models import Coupon, UserCoupon
from orders.models import CartItem, Order
from payments.models import PaymentRecord
from users.models import Address


class Command(BaseCommand):
    help = "清除测试数据：订单/购物车/优惠券/地址/用户（保留商品与分类）"

    def handle(self, *args, **options):
        counters = {}
        # 先删支付记录（PaymentRecord.order 为 PROTECT），再删订单（OrderItem 随 Order 级联）
        for label, qs in [
            ("支付记录", PaymentRecord.objects.all()),
            ("订单", Order.objects.all()),
            ("购物车", CartItem.objects.all()),
            ("用户优惠券", UserCoupon.objects.all()),
            ("优惠券", Coupon.objects.all()),
            ("地址", Address.objects.all()),
        ]:
            counters[label] = qs.count()
            qs.delete()

        User = get_user_model()
        counters["用户"] = User.objects.count()
        User.objects.all().delete()

        for label, n in counters.items():
            if n:
                self.stdout.write(f"  ✗ 清除 {label}: {n} 条")
        self.stdout.write(self.style.SUCCESS("测试数据清除完成"))
