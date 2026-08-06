"""商品模块 · 模型"""
from django.db import models


class Category(models.Model):
    """商品分类"""
    name = models.CharField(max_length=32, unique=True, verbose_name="分类名称")
    icon = models.CharField(max_length=64, blank=True, default="", verbose_name="图标")
    sort_order = models.IntegerField(default=0, verbose_name="排序")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "categories"
        verbose_name = "分类"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品"""
    STATUS_CHOICES = [
        ("on", "上架"),
        ("off", "下架"),
    ]

    name = models.CharField(max_length=64, verbose_name="商品名称")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name="products", verbose_name="分类",
    )
    description = models.TextField(blank=True, default="", verbose_name="描述")
    image = models.URLField(max_length=512, blank=True, default="", verbose_name="主图")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="价格")
    stock = models.PositiveIntegerField(default=0, verbose_name="库存")
    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default="on", verbose_name="状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "products"
        verbose_name = "商品"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Spec(models.Model):
    """商品规格（如 200g / 500g）"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name="specs", verbose_name="商品",
    )
    name = models.CharField(max_length=32, verbose_name="规格名称")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="规格价格")
    stock = models.PositiveIntegerField(default=0, verbose_name="规格库存")

    class Meta:
        db_table = "specs"
        verbose_name = "规格"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.product.name} - {self.name}"
