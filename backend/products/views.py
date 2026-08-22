"""商品模块 · 视图"""
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """分类接口（只读）"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """商品接口（只读）"""
    queryset = Product.objects.filter(status="on").select_related("category").prefetch_related("specs")
    permission_classes = [AllowAny]
    filterset_fields = ["category"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer
