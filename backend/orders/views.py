"""订单模块 · 视图"""
import logging
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from payments.models import PaymentRecord
from payments.wxpay import get_wxpay_client, WXPayError
from mkcoffee.utils.notify import send_order_notify
from coupons.models import UserCoupon

logger = logging.getLogger(__name__)
from products.models import Product, Spec
from users.models import Address
from .models import CartItem, Order, OrderItem
from .serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
)
from .services import ship_order


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

        # 修复：MySQL 中 spec=NULL 时 spec=spec 无法匹配（NULL ≠ NULL）
        # 需用 spec__isnull=True 替代 spec=None 查询
        existing_qs = CartItem.objects.filter(
            user=request.user,
            product=product,
        )
        if spec is None:
            existing = existing_qs.filter(spec__isnull=True).first()
        else:
            existing = existing_qs.filter(spec=spec).first()

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
        """下单：从当前用户购物车创建订单（item_ids 可选，默认下单全部；address_id 必填）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item_ids = serializer.validated_data.get("item_ids")
        address_id = serializer.validated_data.get("address_id")

        # 收货地址：必须是当前用户的地址，快照到订单
        address = Address.objects.filter(
            id=address_id, user=request.user,
        ).first()
        if not address:
            return Response(
                {"code": 400, "data": None, "msg": "收货地址无效，请重新选择"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = CartItem.objects.filter(
            user=request.user,
        ).select_related("product", "spec").select_for_update()
        if item_ids:
            qs = qs.filter(pk__in=item_ids)
        cart_items = qs

        if not cart_items.exists():
            return Response(
                {"code": 400, "data": None, "msg": "购物车为空，无法下单"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 锁定涉及的 Product 和 Spec 行，防止并发超卖
        product_ids = list({item.product_id for item in cart_items})
        spec_ids = list({item.spec_id for item in cart_items if item.spec_id})

        locked_products = {p.pk: p for p in Product.objects.filter(pk__in=product_ids).select_for_update()}
        locked_specs = {s.pk: s for s in Spec.objects.filter(pk__in=spec_ids).select_for_update()}

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

            # 库存检查（基于锁定行）
            if spec:
                if locked_specs[spec.pk].stock < quantity:
                    return Response(
                        {"code": 400, "data": None,
                         "msg": f"「{product.name}-{spec.name}」库存不足（余 {locked_specs[spec.pk].stock}）"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if locked_products[product.pk].stock < quantity:
                    return Response(
                        {"code": 400, "data": None,
                         "msg": f"「{product.name}」库存不足（余 {locked_products[product.pk].stock}）"},
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

        # ---- 优惠券（可选，下单即核销，取消订单自动释放）----
        coupon_discount = Decimal("0.00")
        user_coupon = None
        coupon_id = serializer.validated_data.get("coupon_id")
        if coupon_id:
            user_coupon = (
                UserCoupon.objects.select_for_update()
                .select_related("coupon")
                .filter(id=coupon_id, user=request.user)
                .first()
            )
            if not user_coupon:
                return Response(
                    {"code": 400, "data": None, "msg": "优惠券不存在或不属于当前用户"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            coupon = user_coupon.coupon
            now = timezone.now()
            if user_coupon.status != "unused":
                return Response(
                    {"code": 400, "data": None, "msg": "该优惠券已使用，无法重复抵扣"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if coupon.status != "active":
                return Response(
                    {"code": 400, "data": None, "msg": "优惠券已停用"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if now < coupon.start_date or now > coupon.end_date:
                return Response(
                    {"code": 400, "data": None, "msg": "优惠券不在有效期内"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if total < coupon.min_amount:
                return Response(
                    {"code": 400, "data": None,
                     "msg": f"订单金额未达优惠门槛（满 ¥{coupon.min_amount} 可用）"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if coupon.type == "full_reduce":
                # 满减：抵扣 = min(券值, 订单总额)，防止超扣
                coupon_discount = min(coupon.value, total)
            elif coupon.type == "discount":
                # 折扣：value 为折数（如 8 = 8折）
                payable = (total * coupon.value / Decimal("10")).quantize(
                    Decimal("0.01"), ROUND_HALF_UP,
                )
                coupon_discount = total - payable

        # 创建订单
        order = Order.objects.create(
            user=request.user,
            total=total,
            coupon_discount=coupon_discount,
            receiver_name=address.name,
            receiver_phone=address.phone,
            receiver_address=(
                f"{address.province}{address.city}{address.district}{address.detail}"
            ),
        )

        # 创建订单明细
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # 核销优惠券（下单即核销；取消订单时自动释放）
        if user_coupon:
            user_coupon.status = "used"
            user_coupon.used_at = timezone.now()
            user_coupon.order = order
            user_coupon.save(update_fields=["status", "used_at", "order"])

        # 原子扣减库存（F表达式，避免竞态）
        for item_data in order_items_data:
            spec = item_data["spec"]
            if spec:
                Spec.objects.filter(pk=spec.pk).update(stock=F("stock") - item_data["quantity"])
            else:
                product = item_data["product"]
                Product.objects.filter(pk=product.pk).update(stock=F("stock") - item_data["quantity"])

        # 清空购物车 —— 仅删除本次下单已锁定的条目。
        # 直接 cart_items.delete() 会按 user 重新查询，可能误删
        # 下单事务期间用户新加入购物车的商品。
        CartItem.objects.filter(
            pk__in=[item.pk for item in cart_items],
        ).delete()

        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "下单成功",
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="ship", permission_classes=[IsAdminUser])
    def ship(self, request, pk=None):
        """商家发货：将「已支付」订单标记为「已发货」

        商家视角，不走 self.get_object()（它按当前用户过滤，订单属于买家）。
        与 Django Admin 的「标记为已发货」共用 ship_order 业务逻辑。
        """
        order = get_object_or_404(Order, pk=pk)
        order, err = ship_order(order)
        if err:
            return Response(
                {"code": 400, "data": None, "msg": err},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "已发货",
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """取消订单（仅待支付状态可取消）"""
        order = self.get_object()

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)

            if order.status != "pending":
                return Response(
                    {"code": 400, "data": None, "msg": f"订单状态为「{order.get_status_display()}」，无法取消"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order.status = "cancelled"
            order.save(update_fields=["status", "updated_at"])

            # 释放优惠券（本单核销的券退回，可再次使用）
            UserCoupon.objects.filter(order=order, status="used").update(
                status="unused", order=None, used_at=None,
            )

            # 原子恢复库存（F表达式，避免竞态）
            for item in order.items.select_related("spec", "product"):
                if item.spec:
                    Spec.objects.filter(pk=item.spec.pk).update(stock=F("stock") + item.quantity)
                else:
                    Product.objects.filter(pk=item.product.pk).update(stock=F("stock") + item.quantity)

        return Response({
            "code": 0,
            "data": OrderDetailSerializer(order).data,
            "msg": "订单已取消",
        })

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        """
        统一支付入口

        - 微信支付已配置 → 统一下单，返回小程序支付参数
        - 微信支付未配置 → 模拟支付
        """
        with transaction.atomic():
            order = Order.objects.select_for_update().get(
                pk=self.kwargs["pk"], user=request.user,
            )

            if order.status != "pending":
                return Response(
                    {"code": 400, "data": None, "msg": f"订单状态为「{order.get_status_display()}」，无法支付"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not settings.WXPAY_ENABLED:
                # ---- 模拟支付（仅在 WXPAY_ENABLED=false 时可用）----
                order.status = "paid"
                order.save(update_fields=["status", "updated_at"])

                PaymentRecord.objects.create(
                    order=order,
                    user=request.user,
                    method="mock",
                    status="paid",
                    amount=order.payable,
                )

                # 企业微信群通知（未配置 webhook 时静默跳过，不影响支付）
                send_order_notify(order, event="paid")

                return Response({
                    "code": 0,
                    "data": {
                        "method": "mock",
                        "order": OrderDetailSerializer(order).data,
                    },
                    "msg": "支付成功（模拟）",
                })

            # ---- 真实微信支付 ----
            # fail-closed：已启用微信支付但配置缺失/初始化失败时，
            # 必须拒绝支付，绝不静默降级为模拟支付（防止“免费下单”）。
            try:
                wxpay = get_wxpay_client()
            except WXPayError as e:
                logger.error("微信支付已启用但不可用: %s", e)
                return Response(
                    {"code": 500, "data": None, "msg": "微信支付配置错误，请联系客服"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            amount_fen = int(order.payable * 100)
            description = f"迈科咖啡-{order.order_no[:8]}"

            try:
                result = wxpay.jsapi_order(
                    out_trade_no=order.order_no,
                    amount=amount_fen,
                    payer_openid=request.user.openid,
                    description=description,
                )
            except Exception as e:
                return Response(
                    {"code": 500, "data": None, "msg": f"微信支付下单失败: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            prepay_id = result.get("prepay_id", "")

            # 记录支付流水
            PaymentRecord.objects.create(
                order=order,
                user=request.user,
                method="wechat_jsapi",
                amount=order.payable,
                prepay_id=prepay_id,
            )

            # 返回小程序调起支付所需参数
            pay_params = wxpay.sign_miniapp_params(prepay_id)

            return Response({
                "code": 0,
                "data": {
                    "method": "wechat_jsapi",
                    "pay_params": pay_params,
                },
                "msg": "ok",
            })
