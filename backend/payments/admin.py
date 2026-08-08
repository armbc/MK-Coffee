"""支付模块 · 管理后台"""
from django.contrib import admin

from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = [
        "id", "order", "user", "method", "status", "amount",
        "transaction_id", "created_at",
    ]
    list_filter = ["method", "status", "created_at"]
    search_fields = ["order__order_no", "transaction_id"]
    readonly_fields = ["created_at", "updated_at", "raw_response"]
    raw_id_fields = ["order", "user"]
