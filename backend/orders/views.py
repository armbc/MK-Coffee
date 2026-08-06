"""订单模块 · 视图"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CartItem, Order, OrderItem
from .serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
)


class CartViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """购物车接口（需登录）"""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(
            user=self.request.user,
        ).select_related("product", "spec")

    def create(self, request, *args, **kwargs):
        """加入购物车：若已存在同商品同规格，则叠加数量"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        spec = serializer.validated_data.get("spec")
        quantity = serializer.validated_data.get("quantity", 1)

        existing = CartItem.objects.filter(
            user=request.user,
            product=product,
            spec=spec,
        ).first()

        if existing:
            existing.quantity += quantity
            existing.save(update_fields=["quantity", "updated_at"])
            return Response(
                CartItemSerializer(existing).data,
                status=status.HTTP_201_CREATED,
            )

        item = serializer.save(user=request.user)
        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """修改购物车数量"""
        instance = self.get_object()
        serializer = CartItemUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # 返回完整购物车条目
        return Response(CartItemSerializer(instance).data)

    def get_object(self):
        """确保用户只能操作自己的购物车条目"""
        return get_object_or_404(
            CartItem,
            id=self.kwargs["pk"],
            user=self.request.user,
        )

    @action(detail=True, methods=["post"], url_path="update-qty")
    def update_qty(self, request, pk=None):
        """修改购物车数量（POST 版本，兼容微信小程序）"""
        instance = self.get_object()
        serializer = CartItemUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "code": 0,
            "data": CartItemSerializer(instance).data,
            "msg": "ok",
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="remove")
    def remove(self, request, pk=None):
        """移除购物车条目（POST 版本，兼容微信小程序）"""
        instance = self.get_object()
        instance.delete()
        return Response({
            "code": 0, "data": None, "msg": "已移除",
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        """清空购物车"""
        count, _ = CartItem.objects.filter(user=request.user).delete()
        return Response({"code": 0, "data": {"deleted": count}, "msg": "ok"})


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """订单接口（需登录）"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
        ).prefetch_related("items")

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """下单：从当前用户购物车创建订单"""
        cart_items = CartItem.objects.filter(
            user=request.user,
        ).select_related("product", "spec").select_for_update()

        if not cart_items.exists():
            return Response(
                {"code": 400, "data": None, "msg": "购物车为空，无法下单"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 验证库存 & 计算总价
        order_items_data = []
        total = 0

        for item in cart_items:
            product = item.product
            spec = item.spec

            # 商品状态检查
            if product.status != "on":
                return Response(
                    {"code": 400, "data": None, "msg": f"商品「{product.name}」已下架"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 价格取规格价或商品价
            price = spec.price if spec else product.price
            quantity = item.quantity

            # 库存检查
            if spec:
                if spec.stock < quantity:
                    return Response(
                        {"code": 400, "data": None,
                         "msg": f"「{product.name}-{spec.name}」库存不足（余 {spec.stock}）"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if product.stock < quantity:
                    return Response(
                        {"code": 400, "data": None,
                         "msg": f"「{product.name}」库存不足（余 {product.stock}）"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            line_total = price * quantity
            total += line_total

            order_items_data.append({
                "product": product,
                "spec": spec,
                "product_name": product.name,
                "spec_name": spec.name if spec else "",
                "price": price,
                "quantity": quantity,
            })

        # 创建订单
        order = Order.objects.create(
            user=request.user,
            total=total,
        )

        # 创建订单明细
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # 扣减库存
        for item_data in order_items_data:
            spec = item_data["spec"]
            if spec:
                spec.stock -= item_data["quantity"]
                spec.save(update_fields=["stock"])
            else:
                product = item_data["product"]
                product.stock -= item_data["quantity"]
                product.save(update_fields=["stock"])

        # 清空购物车
        cart_items.delete()

        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "下单成功",
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """取消订单（仅待支付状态可取消）"""
        order = self.get_object()

        if order.status != "pending":
            return Response(
                {"code": 400, "data": None, "msg": f"订单状态为「{order.get_status_display()}」，无法取消"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            order.status = "cancelled"
            order.save(update_fields=["status", "updated_at"])

            # 恢复库存
            for item in order.items.select_related("spec", "product"):
                if item.spec:
                    item.spec.stock += item.quantity
                    item.spec.save(update_fields=["stock"])
                else:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=["stock"])

        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "订单已取消",
        })

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        """模拟支付（微信支付接入前的占位实现）"""
        order = self.get_object()

        if order.status != "pending":
            return Response(
                {"code": 400, "data": None, "msg": f"订单状态为「{order.get_status_display()}」，无法支付"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])

        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "支付成功",
        })
