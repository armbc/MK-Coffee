"""清除测试数据：订单/购物车/用户优惠券/地址/普通用户（保留商品、分类、优惠券模板与管理员账号）"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from coupons.models import UserCoupon
from orders.models import CartItem, Order
from payments.models import PaymentRecord
from users.models import Address


class Command(BaseCommand):
    help = "清除测试数据：订单/购物车/用户优惠券/地址/普通用户（保留商品、分类、优惠券模板与管理员账号）"

    def handle(self, *args, **options):
        counters = {}
        # 先删支付记录（PaymentRecord.order 为 PROTECT），再删订单（OrderItem 随 Order 级联）
        # 注意：只清 UserCoupon（用户领取记录），Coupon 模板是运营配置，必须保留
        for label, qs in [
            ("支付记录", PaymentRecord.objects.all()),
            ("订单", Order.objects.all()),
            ("购物车", CartItem.objects.all()),
            ("用户优惠券", UserCoupon.objects.all()),
            ("地址", Address.objects.all()),
        ]:
            counters[label] = qs.count()
            qs.delete()

        User = get_user_model()
        # 只删普通用户，保留管理员（is_staff=True），避免误删后台账号
        non_staff = User.objects.filter(is_staff=False)
        counters["用户"] = non_staff.count()
        non_staff.delete()
        self.stdout.write(
            f"  ✓ 保留管理员账号: {User.objects.filter(is_staff=True).count()} 个"
        )

        for label, n in counters.items():
            if n:
                self.stdout.write(f"  ✗ 清除 {label}: {n} 条")
        self.stdout.write(self.style.SUCCESS("测试数据清除完成（优惠券模板已保留）"))
