"""优惠券模块 · 序列化器"""
from rest_framework import serializers
from .models import Coupon, UserCoupon


class CouponSerializer(serializers.ModelSerializer):
    """优惠券列表/详情（面向用户）"""
    value_text = serializers.CharField(read_only=True)
    claimed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id", "name", "type", "value", "value_text",
            "min_amount", "stock", "claimed_count",
            "start_date", "end_date", "status",
        ]


class UserCouponSerializer(serializers.ModelSerializer):
    """用户持有的优惠券"""
    coupon_name = serializers.CharField(source="coupon.name", read_only=True)
    coupon_type = serializers.CharField(source="coupon.type", read_only=True)
    coupon_value = serializers.DecimalField(source="coupon.value", max_digits=10, decimal_places=2, read_only=True)
    coupon_min_amount = serializers.DecimalField(source="coupon.min_amount", max_digits=10, decimal_places=2, read_only=True)
    coupon_value_text = serializers.CharField(source="coupon.value_text", read_only=True)
    end_date = serializers.DateTimeField(source="coupon.end_date", read_only=True)

    class Meta:
        model = UserCoupon
        fields = [
            "id", "coupon", "coupon_name", "coupon_type",
            "coupon_value", "coupon_min_amount", "coupon_value_text",
            "end_date", "status", "used_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
