"""重建/更新 5 张运营优惠券模板（与 COUPONS.md 台账一致，幂等可重复执行）"""
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from coupons.models import Coupon

# 统一有效期：08-23 ~ 09-30（测试期），正式运营前可在 COUPONS.md 调整后改这里
_START = timezone.make_aware(datetime(2026, 8, 23, 0, 0, 0))
_END = timezone.make_aware(datetime(2026, 9, 30, 23, 59, 59))

# 与 COUPONS.md「一、当前优惠券模板」保持一致
# 折扣 value = 折数（9 = 9折、88 = 8.8折）；满减 value = 减现金额（元）
TEMPLATES = [
    {"name": "新人券", "type": "discount", "value": 9, "min_amount": 0, "stock": 200},
    {"name": "新客满减券", "type": "full_reduce", "value": 10, "min_amount": 50, "stock": 200},
    {"name": "咖啡豆满减券", "type": "full_reduce", "value": 15, "min_amount": 100, "stock": 300},
    {"name": "大额满减券", "type": "full_reduce", "value": 40, "min_amount": 200, "stock": 100},
    {"name": "复购折扣券", "type": "discount", "value": 88, "min_amount": 80, "stock": 200},
]


class Command(BaseCommand):
    help = "重建/更新 5 张运营优惠券模板（按名称 upsert，幂等；有效期/库存/状态统一对齐台账）"

    def handle(self, *args, **options):
        for t in TEMPLATES:
            coupon, created = Coupon.objects.update_or_create(
                name=t["name"],
                defaults={
                    "type": t["type"],
                    "value": t["value"],
                    "min_amount": t["min_amount"],
                    "stock": t["stock"],
                    "start_date": _START,
                    "end_date": _END,
                    "status": "active",
                },
            )
            verb = "创建" if created else "更新"
            self.stdout.write(
                f"  ✓ {verb}《{coupon.name}》{coupon.value_text} "
                f"满{coupon.min_amount}元 库存{coupon.stock}"
            )
        self.stdout.write(self.style.SUCCESS(
            f"优惠券模板就绪：共 {Coupon.objects.count()} 张"
        ))
