"""订单模块 · 模型"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from products.models import Product, Spec


class CartItem(models.Model):
    """购物车条目"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="cart_items", verbose_name="用户",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name="cart_items", verbose_name="商品",
    )
    spec = models.ForeignKey(
        Spec, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cart_items", verbose_name="规格",
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="数量")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "carts"
        verbose_name = "购物车"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        constraints = [
            # 同一用户同一商品同一规格不可重复
            models.UniqueConstraint(
                fields=["user", "product", "spec"],
                name="unique_cart_item",
            ),
        ]

    def __str__(self):
        spec_name = f"({self.spec.name})" if self.spec else ""
        return f"{self.user} - {self.product.name}{spec_name} x{self.quantity}"

    @property
    def unit_price(self):
        """单价：有规格取规格价，否则取商品价"""
        if self.spec:
            return self.spec.price
        return self.product.price

    @property
    def subtotal(self):
        """小计"""
        return self.unit_price * self.quantity


class Order(models.Model):
    """订单"""
    STATUS_CHOICES = [
        ("pending", "待支付"),
        ("paid", "已支付"),
        ("shipped", "已发货"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="orders", verbose_name="用户",
    )
    order_no = models.CharField(
        max_length=36, unique=True, default="", verbose_name="订单编号",
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="订单金额")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "orders"
        verbose_name = "订单"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"订单 {self.order_no}"


class OrderItem(models.Model):
    """订单明细"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name="items", verbose_name="订单",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name="order_items", verbose_name="商品",
    )
    spec = models.ForeignKey(
        Spec, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="order_items", verbose_name="规格",
    )
    # 快照字段 —— 下单后商品名称/规格可能变更，保留历史记录
    product_name = models.CharField(max_length=64, verbose_name="商品名称")
    spec_name = models.CharField(max_length=32, blank=True, default="", verbose_name="规格名称")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    quantity = models.PositiveIntegerField(default=1, verbose_name="数量")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "order_items"
        verbose_name = "订单明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def subtotal(self):
        """小计"""
        return self.price * self.quantity
