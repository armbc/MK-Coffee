"""订单模块 · 序列化器"""
from rest_framework import serializers
from products.models import Product, Spec
from .models import CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    """购物车条目"""
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_image = serializers.URLField(source="product.image", read_only=True)
    spec_name = serializers.CharField(source="spec.name", read_only=True, default="")
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "product_image",
            "spec", "spec_name", "quantity",
            "unit_price", "subtotal",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_quantity(self, value):
        """数量必须为正整数"""
        if value < 1:
            raise serializers.ValidationError("数量不能小于 1")
        return value

    def validate_product(self, value):
        """仅允许上架商品加入购物车"""
        if value.status != "on":
            raise serializers.ValidationError("该商品已下架，无法加入购物车")
        return value

    def validate(self, attrs):
        """校验规格是否属于该商品"""
        spec = attrs.get("spec")
        product = attrs.get("product")
        if spec and spec.product_id != product.id:
            raise serializers.ValidationError({"spec": "规格不属于该商品"})
        return attrs


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """购物车更新（仅数量）"""

    class Meta:
        model = CartItem
        fields = ["quantity"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("数量不能小于 1")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """订单明细"""
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "product", "product_name",
            "spec", "spec_name",
            "price", "quantity", "subtotal",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表（不含明细）"""
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_no", "total", "status", "status_display",
            "item_count", "created_at",
        ]

    def get_item_count(self, obj):
        # 使用 len() 利用 prefetch_related 缓存，避免 N+1 查询
        return len(obj.items.all())


class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情（含明细）"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_no", "total", "status", "status_display",
            "items", "created_at", "updated_at",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """下单请求 —— 从购物车生成订单（item_ids 可选，默认下单全部；address_id 必填）"""
    remark = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    address_id = serializers.IntegerField(required=True, help_text="收货地址 ID")
