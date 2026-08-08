"""支付模块 · 模型"""
from django.conf import settings
from django.db import models


class PaymentRecord(models.Model):
    """支付流水记录"""
    PAYMENT_METHOD_CHOICES = [
        ("wechat_jsapi", "微信小程序支付"),
        ("mock", "模拟支付"),
    ]

    STATUS_CHOICES = [
        ("initiated", "已发起"),
        ("paid", "已支付"),
        ("refunded", "已退款"),
        ("failed", "失败"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payment_records",
        verbose_name="订单",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_records",
        verbose_name="用户",
    )
    method = models.CharField(
        max_length=16,
        choices=PAYMENT_METHOD_CHOICES,
        default="mock",
        verbose_name="支付方式",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="initiated",
        verbose_name="状态",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="支付金额",
    )
    transaction_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="微信支付交易号",
    )
    prepay_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="预支付 ID",
    )
    raw_response = models.JSONField(
        blank=True,
        default=dict,
        verbose_name="原始响应/回调数据",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "payment_records"
        verbose_name = "支付流水"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"支付 #{self.id} - {self.get_method_display()} - {self.get_status_display()}"
