"""优惠券模块 · 视图"""
from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Coupon, UserCoupon
from .serializers import CouponSerializer, UserCouponSerializer


class CouponViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """优惠券列表（所有用户可查看） + 领取（需登录）"""
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action == "claim":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Coupon.objects.filter(status="active").order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="claim")
    def claim(self, request, pk=None):
        """领取优惠券"""
        coupon = self.get_object()

        # 状态校验（不依赖锁，外部检查即可）
        if coupon.status != "active":
            return Response({"code": 400, "data": None, "msg": "优惠券已停用"}, status=400)

        # 时间校验
        now = timezone.now()
        if now < coupon.start_date:
            return Response({"code": 400, "data": None, "msg": "优惠券尚未开始"}, status=400)
        if now > coupon.end_date:
            return Response({"code": 400, "data": None, "msg": "优惠券已过期"}, status=400)

        try:
            with transaction.atomic():
                # 锁定优惠券行，防止并发超领
                coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)

                # 库存校验（使用数据库查询替代 Python property）
                claimed = UserCoupon.objects.filter(coupon=coupon).count()
                if coupon.stock > 0 and claimed >= coupon.stock:
                    return Response({"code": 400, "data": None, "msg": "优惠券已领完"}, status=400)

                user_coupon = UserCoupon.objects.create(
                    user=request.user, coupon=coupon,
                )
        except IntegrityError:
            return Response({"code": 400, "data": None, "msg": "您已领取过此优惠券"}, status=400)

        return Response({
            "code": 0,
            "data": UserCouponSerializer(user_coupon).data,
            "msg": "领取成功",
        }, status=201)


class UserCouponViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """我的优惠券列表（需登录）"""
    serializer_class = UserCouponSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCoupon.objects.filter(
            user=self.request.user,
        ).select_related("coupon").order_by("-created_at")
