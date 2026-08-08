"""支付模块 · 序列化器"""
from rest_framework import serializers

from .models import PaymentRecord


class PaymentRecordSerializer(serializers.ModelSerializer):
    """支付流水"""
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PaymentRecord
        fields = [
            "id", "order", "method", "method_display",
            "status", "status_display", "amount",
            "transaction_id", "created_at",
        ]
        read_only_fields = fields
