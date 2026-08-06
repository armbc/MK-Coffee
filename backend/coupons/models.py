"""优惠券模块 · 模型"""
from django.conf import settings
from django.db import models


class Coupon(models.Model):
    """优惠券模板"""
    TYPE_CHOICES = [
        ("full_reduce", "满减"),
        ("discount", "折扣"),
    ]
    STATUS_CHOICES = [
        ("active", "生效中"),
        ("inactive", "已停用"),
    ]

    name = models.CharField(max_length=64, verbose_name="名称")
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, verbose_name="类型")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="优惠值")
    min_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="最低消费",
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="库存")
    start_date = models.DateTimeField(verbose_name="开始时间")
    end_date = models.DateTimeField(verbose_name="结束时间")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="active", verbose_name="状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "coupons"
        verbose_name = "优惠券"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def claimed_count(self):
        return self.user_coupons.count()

    @property
    def value_text(self):
        if self.type == "full_reduce":
            return f"¥{int(self.value)}"
        return f"{int(self.value)}折"


class UserCoupon(models.Model):
    """用户持有的优惠券"""
    STATUS_CHOICES = [
        ("unused", "未使用"),
        ("used", "已使用"),
        ("expired", "已过期"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="coupons", verbose_name="用户",
    )
    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE,
        related_name="user_coupons", verbose_name="优惠券",
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="unused", verbose_name="状态",
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="used_coupon", verbose_name="使用订单",
    )
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="使用时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="领取时间")

    class Meta:
        db_table = "user_coupons"
        verbose_name = "用户优惠券"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "coupon"], name="unique_user_coupon",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.coupon.name}"
