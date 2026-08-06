"""商品模块 · 序列化器"""
from rest_framework import serializers
from .models import Category, Product, Spec


class SpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spec
        fields = ["id", "name", "price", "stock"]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "icon", "sort_order"]


class ProductListSerializer(serializers.ModelSerializer):
    """商品列表（不含规格详情）"""
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "category_name", "image", "price", "stock"]


class ProductDetailSerializer(serializers.ModelSerializer):
    """商品详情（含规格）"""
    category_name = serializers.CharField(source="category.name", read_only=True)
    specs = SpecSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "category_name",
            "description", "image", "price", "stock",
            "status", "specs", "created_at",
        ]
