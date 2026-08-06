"""优惠券模块 · 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CouponViewSet, UserCouponViewSet

router = DefaultRouter()
router.register("coupons", CouponViewSet, basename="coupon")
router.register("my-coupons", UserCouponViewSet, basename="my-coupon")

urlpatterns = [
    path("", include(router.urls)),
]
